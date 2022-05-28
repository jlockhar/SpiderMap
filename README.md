# Spider Map
Look for downstream points of cross-talk between two proteins

# Overview
Spider Map is a Python script designed to utilize the relations in the Kyoto Encyclopedia of Genes and Genomes (KEGG) database to determine the crosstalk between two target proteins. Potential applications for this script include validating proposed instances of crosstalk with available data and identifying potential crosstalk changes in disordered pathways. The algorithm utilized in this script relies on the data contained in the KEGG Markup Language (KGML) entries for the pathways in the KEGG database. The KEGG database is queried to collect all KGML files for pathways which include proteins downstream from the target proteins. These files are then parsed and converted into a directional graph with the genes/complexes forming the nodes, much like the graphs present in the KEGG database. The nodes which can trace back to both target proteins, which represent instances of crosstalk, are then recorded for manual exploration. Limitations of this script are based on the information present in KGML files, most important of which is the tendency for genes to appear individually and as complexes (e.g. RAC1). These nodes are considered to be unrelated during the creation of the relation graph in Spider Map, and such nodes may appear in the results a number of times. In such a case it falls to the researcher to determine which complex is of interest.


# Instructions

See "Spider_map instructions.pdf" for more detailed instructions (with pictures).

## Instructions for getting data from KEGG:
1. Using the KEGG website (kegg.jp), identify your genes of interest and their KEGG IDs. (for example: I'm looking for links between BRAF and STAT3. I search for those on KEGG and find their IDs(hsa:673 and hsa:6774) )
2. Choose a pathway which your genes of interest are involved in and the pathway's KEGG ID. (Which one you choose does not matter, as they will all be analyzed. This will be changed in the optimized version) (example: BRAF is in hsa04015, STAT3 is in hsa04630)
3. Start the version of the mapping tool you want to use (with or without output file).
4. Navigate to target directory. (input HELP for a list of commands)
5. Start data collection algorithm using MAP command in target directory. (This will create 2 sub-directories for the genes of interest)
6. When prompted input the KEGG ID for the pathways of your genes of interest (Pathways in the KEGG database do NOT have a ':' after their organism code). You will be prompted once for each gene of interest.
7. After data collection is finished, you may continue to parse data immediately using the PARSE command. You may also quit the script using the QUIT command.

## Instructions for parsing data collected from KEGG:
(Assuming you did not continue after collecting data)
1. Start the version of the mapping tool you want to use (with or without output file)
2. Navigate to the directory where you ran the mapping tool (If in doubt, such a directory will contain 2 files named '1' and '2')
3. Run the PARSE command.
(If you continued after collecting data, start here)
4. When prompted enter the KEGG ID for your genes of interest (This step will work with multi-gene proteins, such as RAP1 [hsa:5906 hsa:5908]. However these must be entered exactly as they appear in the KEGG database)
6a. If using the version without an output file: you may enter the KEGG ID of any genes you wish to test as links between your genes of interest. If you do not have any to test, you may press the enter key. If your test gene is not in the list of linking genes you will be able to display the list of links by responding 'y' to the next prompt.)
6b. If using the version with an output file: the output file will be located in the directory where you ran the MAP and PARSE commands. The file will be named "protein_links.txt". If you wish to re-run the analysis and keep this file, you must move it to another location or rename it, else it will be overwritten.



