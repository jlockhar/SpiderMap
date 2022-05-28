# Spider Map
Look for downstream points of cross-talk between two proteins

Spider Map is a Python script designed to utilize the relations in the Kyoto Encyclopedia of Genes and Genomes (KEGG) database to determine the crosstalk between two target proteins. Potential applications for this script include validating proposed instances of crosstalk with available data and identifying potential crosstalk changes in disordered pathways. The algorithm utilized in this script relies on the data contained in the KEGG Markup Language (KGML) entries for the pathways in the KEGG database. The KEGG database is queried to collect all KGML files for pathways which include proteins downstream from the target proteins. These files are then parsed and converted into a directional graph with the genes/complexes forming the nodes, much like the graphs present in the KEGG database. The nodes which can trace back to both target proteins, which represent instances of crosstalk, are then recorded for manual exploration. Limitations of this script are based on the information present in KGML files, most important of which is the tendency for genes to appear individually and as complexes (e.g. RAC1). These nodes are considered to be unrelated during the creation of the relation graph in Spider Map, and such nodes may appear in the results a number of times. In such a case it falls to the researcher to determine which complex is of interest.
