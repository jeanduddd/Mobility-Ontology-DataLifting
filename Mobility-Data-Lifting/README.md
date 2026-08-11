# Mobility-Data-Lifting

This folder contains the datalifting tool made to convert mobility indicators data into RDF turtle triples.<br>
Relying on the Morph-xR2RML engine, it generates a knowledge graph based on the defined ontology.

## Project Structure

This is an overview of the internal architecture of the Data Lifting tool:
### Folders
*   **[DataLifting_input](./DataLifting_input)** : Contains the formatted input datasets (CSV, JSON, GeoJSON) ready to be converted. This is where you put your data.
*   **[Datalifting_output](./DataLifting_output)** : The destination directory where the final generated RDF knowledge graph is saved.
*   **[DataLifting_mappings](./DataLifting_mappings)** : Contains the xR2RML mapping files. These are the rules used by the engine to translate the data into RDF triples based on the ontology. *(The base structure comes from the Morph-xR2RML repository, while the custom `mapping_*.ttl` files are specific to this tool).*
*   **[DataLifting_scripts](./DataLifting_scripts)** : Contains the core Python scripts used to run the data lifting pipeline.
*   **[mongo_tools](./mongo_tools)** : Contains scripts and utilities related to MongoDB management, which is by the lifting engine. *(Duplicated from the original Morph-xR2RML repository).*
*   **[DataPreparation/](./DataPreparation)** : Contains specific documentation and scripts used for a pre-processing task. It explains how a specific raw output from an external tool was cleaned and formatted into the standard input expected by this pipeline.

### Core Configuration Files
*   **[config.yaml](./config.yaml)** : The main configuration file where the tool's parameters and properties are defined.
*   **[docker-compose.yml](./docker-compose.yml)** : The Docker configuration file that sets up, links, and runs the isolated environment (including the Morph-xR2RML engine). *(Adapted from the original Morph-xR2RML repository).*
*   **[requirements.txt](./requirements.txt)** : Lists all the specific Python dependencies required to run the scripts locally.

## Requirements

To run the data lifting tool, you need to be in this exact folder (Mobility-Data-Lifting).<br>

1. Python & Libraries
This tool require Python as well as some librairies.<br>
Open your terminal in the mobility-data-lifting folder and run the following command to download all of them:
<br><br>
```pip install -r requirements.txt```
<br><br>
2. Docker & Docker-Compose
Any recent version of Docker is good to use. If you haven't already, the easiest way is to install [Docker Desktop](https://www.docker.com/products/docker-desktop/), which includes both tools.<br>

Docker is used to containerize our semantic lifting engine, **Morph-xR2RML**. This allows us to run the data conversion in an isolated environment, meaning you don't need to install Java or configure any dependencies on your device.

**About the Lifting Engine:**
Tool made by Franck Michel. Morph-xR2RML: MongoDB-to-RDF translation. 2015, ⟨swh:1:dir:8ea716c0d9e69527a5f50378bf135c5952b1a229⟩. ⟨hal-04128090⟩<br>
[Morph xR2RML GitHub Repository](https://github.com/frmichel/morph-xr2rml/tree/master)

To integrate the tool, the following steps were performed during development:
- The source files were downloaded directly from the official repository.
- Only the [mongo_tools](./mongo_tools/), the xr2rml_config renamed as [DataLifting_mappings](./DataLifting_mappings/) directories and the [docker file](./docker-compose.yml) necessary for our pipeline were kept.
- These files were bundled directly into our project folder with minor configuration adjustments in the docker file to adapt the names of the used folders.

It means that there is no extra manual installation step. Morph-xR2RML is already bundled and containerized within this repository. Docker will automatically build and run the engine when you launch the tool.

## Input data

### How to structure input data ?
This project allows to convert mutiple file format for spaces, indicators and records.<br>
Exact specifications are available in another detailed document :<br>
**[See documentation on input file formats](./input-file-documentation.md)** 

## Data lifting process

### How to run the tool ? 
This is the process to run the tool:
1. Place all your input files in the folder ```DataLifting_input```. You can add multiple files using different format at the same time and the tool will convert all of them at the same time,
2. Modify the configuration file ```config.yaml``` so the columns/property names of your input files are recognized,
3. Start Docker with the command ```docker-compose un -d```,
4. Start the tool by running the command ```python .\DataLifting_scripts\convert2RDF.py```,
5. At the end of the conversion, terminate Docker with the command ```docker-compose down```

## Output / Knowledge graph
Once the script ended, you should find your file converted into RDF triples in turtle format in the folder ```DataLifting_output```<br>
The converted spaces are located in the file space.ttl<br>
The converted indicators are located in the file indicator.ttl<br>
The records are converted in batched so you might find multiple converted record files with the name recordX.ttl, X corresponding to the number of the record batch converted

## Demo (Testing the tool)

To help you understand how the tool works, a set of demo files is provided by default in the [DataLifting_input](./DataLifting_input) folder (e.g., `indicators.csv`, `spaces.geojson`).<br><br>

These files contain fake mobility data created for specially for the example and formatted to work with the tool.<br>
You can run the pipeline directly after installation without providing any of your own data. The script will automatically detect and process these demo files so you can observe the generated RDF graph.<br>
Once you are familiar with the process, simply delete the demo files from the `DataLifting_input` directory and place your own formatted datasets inside, and run the tool again.