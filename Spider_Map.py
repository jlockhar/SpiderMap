import urllib.request
import os
from random import randint
from math import ceil
from xml.dom import minidom
import sys
import networkx as nx
'''
#####TODO######
add docstrings
see if fetching of kgmls can be accelerated, look into "grequests"
###############
'''
class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class entry_object:
    '''entry_object representing individual proteins in pathways
    information: kid, affector list, affects list, pathways list, activation state, hold state

    '''
    def __init__(self, protein_kid):
        self.id = protein_kid #kegg id
        self.affectors = set() #list of (proteins that act on this protein, the relation, and the pathway)
        self.affects = set()   #list of (proteins that this protein acts on, the relation, and the pathway)
        self.pathways = set()  #set of pathways this protein is present in
    def __str__(self):
        '''print information for entry_object
        format: kid, # of affectors, # of affects, # of pathways, self.state, self.hold'''
        return self.id + " " + str(len(self.affectors)) + " " + str(len(self.affects)) + " " + str(len(self.pathways))
    def addaffector(self, affector, relation, pathway):
        '''add affector to self.affectors[]'''
        self.affectors.add((affector, relation, self.id, pathway))
    def addaffect(self, affect, relation, pathway):
        '''add affect to self.affects[]'''
        self.affects.add((self.id, relation, affect, pathway ))
    def addpathway(self, pathway_input):
        '''add pathway to self.pathways[]'''
        self.pathways.add(pathway_input)


##################################get_target_id#####################################################
def get_target_id():
    valid_id = False
    valid_type = False
    valid_types = ["NCBI-GI", "NCBI-GENEID", "UNIPROT"]
    need_input = True
    while not valid_id:
        if need_input == True:
            input_id = input("Please enter gene ID [KEGG-ID, NCBI-GENEID, or UNIPROT] : ")
            need_input = False
        if input_id[0].isupper():
            input_id, success = convert_id(input_id, "UNIPROT")
            if succes == False:
                need_input = True
        elif input_id.isdigit():
            input_id, success = convert_id(input_id, "NCBI-GENEID")
            if success == False:
                need_input = True
        elif len(input_id) >= 5:
            if (input_id[0:2].isalpha() and input_id[3] == ':') or (input_id[0:3].isalpha() and input_id[4] == ':'):
                try:
                    get_call = "http://rest.kegg.jp/get/"+input_id
                    test = urllib.request.urlopen(get_call).read().decode(encoding = 'utf-8')
                    urllib.request.urlcleanup()
                    if test == '\n':
                        raise MyError('No entry found for ' + input_id + ', please enter ID again.')
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        print("No entry found for that ID, please enter ID again. (404)")
                        valid_id = False
                        need_input = True
                    elif e.code >= 500:
                        print("An error (" + str(e.code) + ") occured when contacting the KEGG database. Please wait and try again.")
                        valid_id = False
                        need_input = True
                except MyError as e:
                    print(e.value)
                    valid_id = False
                    need_input = True
                except:
                    print("An unexpected error occured during ID verificiation. Please re-run your query.\nIf this error persists contact the developer.\nError:" + str(sys.exc_info()[0]))
                    valid_id = False
                    need_input = True
                else:
                    valid_id = True
        else:
            print("Not a valid form of ID")
            need_input = True
    return input_id

def convert_id(input_id, id_type):
    if id_type == "NCBI-GENEID":
        input_id = 'hsa:' + input_id
        success = True
    elif id_type == "NCBI-GI" or id_type == "UNIPROT":
        try:
            got_id = urllib.request.urlopen("http://rest.kegg.jp/conv/genes/" + id_type.lower() + ':' + input_id).read().decode(encoding= 'utf-8')
            urllib.request.urlcleanup()
            if got_id == '\n':
                raise MyError('No entry found for ' + input_id+ ', please enter ID again.')
        except urllib.error.HTTPError as e:
                if e.code == 404:
                    print("No entry found for that ID, please enter ID again. (404)")
                    success = False
                elif e.code >= 500:
                    print("An error (" + str(e.code) + ") occured when contacting the KEGG database. Please wait and try again.")
                    success = False
        except MyError as e:
            print(e.value)
            success = False
        except:
            print("An unexpected error occured during ID conversion. Please re-run your query.\nIf this error persists contact the developer.\nError:" + str(sys.exc_info()[0]))
            success = False
        else:
            input_id = got_id[got_id.find('\t')+1:got_id.find('\n')]
    return input_id, success
##################################end get_target_id#################################################

##################################spider_map########################################################
def spider_map(target_id):
    pathways_set = set()
    pathways_batch = set()
    called_pathways_set = set()
    proteins_set = set()
    proteins_batch = set()
    called_proteins_set = set()
    max_call_size = 100
    proteins_set.add(target_id)
    pathways_set.update(get_pathways_from_proteins(proteins_set, max_call_size))#get pathways target_protein is involved in
    called_proteins_set.update(target_id)
    for pathway in pathways_set: #get proteins from pathways target_protein is involved in
        if pathway not in called_pathways_set:#call only unexplored pathways
            pathways_batch.add(pathway)
            called_pathways_set.add(pathway)
    proteins_set.update(get_proteins_from_pathways(pathways_batch, max_call_size))
    pathways_batch.clear()
    for protein in proteins_set: #get pathways for all proteins in pathways target_protein is involved in
        if protein not in called_proteins_set: #call only unexplored proteins
            proteins_batch.add(protein)
            called_proteins_set.add(protein)
    pathways_set.update(get_pathways_from_proteins(proteins_batch, max_call_size))
    proteins_batch.clear()
    for pathway in pathways_set: #get proteins from all pathways for all proteins in pathways target_protein is involved in
        if pathway not in called_pathways_set:#call only unexplored pathways
            pathways_batch.add(pathway)
            called_pathways_set.add(pathway)
    proteins_set.update(get_proteins_from_pathways(pathways_batch, max_call_size))
    pathways_batch.clear()
    return pathways_set

def get_pathways_from_proteins(protein_ids, max_call_size):
    pathways_set = set()
    proteins_count = len(protein_ids)
    index = 0
    call_count = ceil(proteins_count/max_call_size)
    #print("Length of call_count in get_pathways_from_proteins: " + str(call_count))
    for call_number in range(0, call_count):
        get_call = "http://rest.kegg.jp/link/pathway/"
        for i in range(0,max_call_size):
            if index < proteins_count:
                protein = protein_ids.pop()
                get_call = get_call + protein + '+'
                index +=1
            else:
                pass
        try:
            got_pathways = urllib.request.urlopen(get_call).read().decode(encoding = 'utf-8')
            urllib.request.urlcleanup()
            if got_pathways == '\n':
                raise MyError('No data found for pathways from proteins')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("No entry found for that ID, please enter ID again. (404)")
            elif e.code >= 500:
                print("An error (" + str(e.code) + ") occured when contacting the KEGG database. Please wait and try again.")
        except MyError as e:
            print(e.value)
        except:
            print("An unexpected error occured getting pathways from proteins. Please re-run your query.\nIf this error persists contact the developer.\nError:" + str(sys.exc_info()[0]))
        else:
            pathways_set.update(get_pathways_set(got_pathways))
    return pathways_set

def get_pathways_set(got_pathways):
    pathways_lines = got_pathways.splitlines()
    pathways_set = set()
    for line in pathways_lines:
        pathway = line[line.find('path:')+5:]
        pathways_set.add(pathway)
    return pathways_set

def get_proteins_from_pathways(pathway_ids, max_call_size):
    proteins_set = set()
    index = 0
    pathways_count = len(pathway_ids)
    calls =0
    call_count = ceil(pathways_count/max_call_size)
    for call_number in range(0, call_count):
        calls += 1
        get_call = "http://rest.kegg.jp/link/genes/"
        for i in range(0,max_call_size):
            if index < pathways_count:
                pathway = pathway_ids.pop()
                get_call = get_call + pathway + '+'
                index +=1
            else:
                pass
        try:
            got_proteins = urllib.request.urlopen(get_call).read().decode(encoding = 'utf-8')
            urllib.request.urlcleanup()
            if got_proteins == '\n':
                    raise MyError('No entry found for proteins from pathways.')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("No entry found for that ID, please enter ID again. (404)")
            elif e.code >= 500:
                print("An error (" + str(e.code) + ") occured when contacting the KEGG database. Please wait and try again.")
        except MyError as e:
            print(e.value)
        except:
            print("An unexpected error occured getting proteins from pathways. Please re-run your query.\nIf this error persists contact the developer.\nError:" + str(sys.exc_info()[0]))
        else:
            proteins_set.update(get_proteins_set(got_proteins))
    return proteins_set

def get_proteins_set(got_proteins):
    protein_lines = got_proteins.splitlines()
    proteins_set = set()
    for line in protein_lines:
        protein = line[line.rfind(':')-3:]
        proteins_set.add(protein)
    return proteins_set

##################################end spider_map####################################################

##################################analyze_kgmls#####################################################
def analyze_kgmls(pathways_set, target_id):
    kgml_relations_list_list = list()
    print("Fetching data for " +target_id)
    kgml_list = fetch_kgmls_for_pathways(pathways_set)
    print("Analyzing data for " +target_id)
    for kgml in kgml_list:
        kgml_relations_list_list.append(parse_kgml(kgml))
    entry_object_dict = create_entry_object_dict(kgml_relations_list_list)
    downstream_entry_object_dict = create_downstream_entry_object_dict(entry_object_dict, target_id)
    return downstream_entry_object_dict

def fetch_kgmls_for_pathways(pathways_set):
    kgml_list = list()
    for pathway in pathways_set:
        got_kgml = urllib.request.urlopen("http://rest.kegg.jp/get/" + pathway + '/kgml').read().decode(encoding = 'utf-8')
        kgml_list.append(got_kgml)
    return kgml_list

def parse_kgml(kgml):
    pathway_name = minidom.parseString(kgml).documentElement.getAttribute('name')[5:]
    id_entry_dict = create_id_entry_dict_from_kgml(create_entry_list_from_kgml(kgml))
    id_id_name_tuples_list = create_id_id_name_path_tuples(create_relations_list_from_kgml(kgml), pathway_name)
    entry_entry_name_tuples_list = create_entry_entry_name_path_tuples(id_entry_dict, id_id_name_tuples_list)
    return entry_entry_name_tuples_list

def create_entry_list_from_kgml(kgml):
    kgml_doc = minidom.parseString(kgml)
    entry_list = kgml_doc.getElementsByTagName('entry')
    return entry_list

def create_id_entry_dict_from_kgml(entry_list):
    id_entry_dict = {}
    entry_types = ('ortholog', 'enzyme', 'gene', 'compound')
    for i in range(len(entry_list)):
        if entry_list[i].attributes['type'].value in entry_types:
            id_entry_dict[entry_list[i].attributes['id'].value] = entry_list[i].attributes['name'].value
        elif entry_list[i].attributes['type'].value == 'group':
            complex_entries = []
            for j in range(len(entry_list[i].childNodes)):
                if entry_list[i].childNodes[j].nodeName == 'component':
                    complex_id = entry_list[i].childNodes[j].attributes['id'].value
                    complex_entries.append(id_entry_dict[complex_id])
            id_entry_dict[entry_list[i].attributes['id'].value] = ','.join(complex_entries)
        else:
            pass
    return id_entry_dict

def create_relations_list_from_kgml(kgml):
    kgml_doc = minidom.parseString(kgml)
    relations_list = kgml_doc.getElementsByTagName('relation')
    return relations_list

def create_id_id_name_path_tuples(relations_list, pathway_name):
    id_id_name_path_tuple_list = list()
    for i in range(len(relations_list)):
        try:
            if len(relations_list[i].childNodes) >= 2:
                id_id_name_path_tuple = relations_list[i].attributes['entry1'].value, relations_list[i].attributes['entry2'].value, relations_list[i].childNodes[1].attributes['name'].value, pathway_name
                id_id_name_path_tuple_list.append(id_id_name_path_tuple)
        except KeyError:
            print(relations_list[i].attributes['entry1'].value+ " or " +relations_list[i].attributes['entry2'] +" is an ignored entry type: " + relations_list[i].childNodes[1].attributes['name'].value)
            continue
    return id_id_name_path_tuple_list

def create_entry_entry_name_path_tuples(id_entry_dict, id_id_name_path_tuples_list):
    entry_entry_name_path_tuples_list = list()
    for i in range(len(id_id_name_path_tuples_list)):
        try:
            entry_entry_name_path_tuple = id_entry_dict[id_id_name_path_tuples_list[i][0]], id_entry_dict[id_id_name_path_tuples_list[i][1]], id_id_name_path_tuples_list[i][2], id_id_name_path_tuples_list[i][3]
            entry1_complex_split = entry_entry_name_path_tuple[0].split(',')
            entry2_complex_split = entry_entry_name_path_tuple[1].split(',')
            for split1 in entry1_complex_split:
                for split2 in entry2_complex_split:
                    split_entry_entry_name_path_tuple = split1, split2, id_id_name_path_tuples_list[i][2], id_id_name_path_tuples_list[i][3]
                    entry_entry_name_path_tuples_list.append(split_entry_entry_name_path_tuple)
        except:
            pass
    return entry_entry_name_path_tuples_list

def create_entry_object_dict(kgml_relations_list_list):
    entry_object_dict = dict()
    for relations_list in kgml_relations_list_list:
        for relation in relations_list:
            if relation[0] not in entry_object_dict:
                entry_object_dict[relation[0]] = entry_object(relation[0])
            entry_object_dict[relation[0]].addaffect(relation[1], relation[2], relation[3])
            entry_object_dict[relation[0]].addpathway(relation[3])
            if relation[1] not in entry_object_dict:
                entry_object_dict[relation[1]] = entry_object(relation[1])
            entry_object_dict[relation[1]].addaffector(relation[0], relation[2], relation[3])
            entry_object_dict[relation[1]].addpathway(relation[3])
    return entry_object_dict

def create_downstream_entry_object_dict(entry_object_dict, target_id):
    downstream_entry_object_dict = dict()
    downstream = set()
    downstream_entry_object_dict[target_id] = entry_object_dict[target_id]
    for affect in entry_object_dict[target_id].affects:
        downstream.add(entry_object_dict[affect[2]])
    while len(downstream) > 0:
         next_entry_object = downstream.pop()
         if next_entry_object.id not in downstream_entry_object_dict:
                downstream_entry_object_dict[next_entry_object.id] = next_entry_object
                for affect in next_entry_object.affects:
                    downstream.add(entry_object_dict[affect[2]])
    return downstream_entry_object_dict

##################################end analyze_kgmls#################################################

##################################analyze_digraph###################################################
def analyze_digraph(downstream_entry_object_dict1, downstream_entry_object_dict2, target1_id, target2_id):
    digraph = create_digraph(downstream_entry_object_dict1, downstream_entry_object_dict2)
    links = list()
    for node in digraph.nodes():
        if nx.has_path(digraph, target1_id, node) and nx.has_path(digraph, target2_id, node):
            links.append(node)
    save_links_as_file(links, digraph, target1_id, target2_id)


def create_digraph(downstream_entry_object_dict1, downstream_entry_object_dict2):
    digraph = nx.DiGraph()
    for key in downstream_entry_object_dict1:
        digraph.add_node(key)
    for key in downstream_entry_object_dict2:
        digraph.add_node(key)
    for key in downstream_entry_object_dict1:
        for affector in downstream_entry_object_dict1[key].affectors:
            digraph.add_edge(affector[0],affector[2],relation=affector[1], pathway=affector[3])
    for key in downstream_entry_object_dict2:
        for affector in downstream_entry_object_dict2[key].affectors:
            digraph.add_edge(affector[0],affector[2],relation=affector[1], pathway=affector[3])
    return digraph

def save_links_as_file(links, digraph, target1_id, target2_id):
    with open("crosstalk.csv", 'w') as outfile:
        lines = list()
        for link in links:
            target1_to_link = ('-->'.join(nx.shortest_path(digraph, target1_id, link)))
            target2_to_link = ('-->'.join(nx.shortest_path(digraph, target2_id, link)))
            line = ','.join([link, target1_to_link, target2_to_link])
            lines.append(line)
        outfile.write('\n'.join(lines))
            
##################################end analyze_digraph###############################################

def main():

    target1_id = get_target_id()
    target2_id = get_target_id()
    print("Building data requests for " + target1_id)
    pathways_set1 = spider_map(target1_id)
    print("Building data requests for " + target2_id)
    pathways_set2 = spider_map(target2_id)
    downstream_entry_object_dict1 = analyze_kgmls(pathways_set1, target1_id)
    downstream_entry_object_dict2 = analyze_kgmls(pathways_set2, target2_id)
    print("Finding points of crosstalk")
    analyze_digraph(downstream_entry_object_dict1, downstream_entry_object_dict2, target1_id, target2_id)

if __name__ == '__main__':
    print("    __    ")
    print(" | /  \ | ")
    print("\_\\\  //_/")
    print(" .'/()\'. ")
    print(" \ \  / / ")
    print("Spider mapping")
    print('')
    print('')
    main()
    print('done')
