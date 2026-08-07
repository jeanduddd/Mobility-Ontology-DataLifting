# Mobility-Ontology-Converter

## 1. Mobility Ontology

This folder contains the ontology files.<br>
Its is composed of the main ontology file and its associated vocabulary.

## 2. Mobility Converter

This folder contains the datalifting tool made to convert mobility indicators data into RDF turtle triples.<br>
Relying on the Morph-xR2RML engine, it generates a knowledge graph based on the defined ontology.
### Requirements
To run the converter tool, you need to be in the converter root folder, not in the global root foler.<br>
This tool require Python as well as some librairies.<br>
You can automatically install all of them by running the following command-line in the root of the converter
<br><br>
```pip install -r requirements.txt```
<br><br>
To run this tool, you also need to install Docker on your device.

### How to structure input data ?
This project allows to convert mutiple file format for spaces, indicators and records.<br>
Exact specifications are avaliale in another detailed document :<br>
**[See documentation on input file formats](./Mobility%20Converter/README.md)**

### Output / Knowledge graphe
Once the script ended, you should find your file converted into RDF triples in turtle format in the folder ```DataLifting_output```<br>
The converted spaces are located in the file space.ttl<br>
The converted indicators are located in the file indicator.ttl<br>
The records are converted in batched so you might find multiple converted record files with the name recordX.ttl, X corresponding to the number of the record batch converted

### How to run the tool ? 
This is the process to run the tool:
1. Place all your input files in the folder ```DataLifting_input```,
2. Modify the configuration file ```config.yaml``` so the columns/property names of your input files are recognized,
3. Start Docker with the command ```docker-compose un -d```,
4. Start the tool by running the command ```python .\DataLifting_scripts\convert2RDF.py```,
5. At the end of the conversion, terminate Docker with the command ```docker-compose down```

Note : An example is provided so you can test the tool before adding your own file

### Morph-xR2RML conversion engine
Tool made by Frank Michel<br>
Franck Michel. Morph-xR2RML: MongoDB-to-RDF translation. 2015, ⟨swh:1:dir:8ea716c0d9e69527a5f50378bf135c5952b1a229⟩. ⟨hal-04128090⟩<br>
<br>
You can find it on the following github page:<br>
https://github.com/frmichel/morph-xr2rml/tree/master
