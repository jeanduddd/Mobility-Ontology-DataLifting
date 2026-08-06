import sys
import argparse
from pathlib import Path
import yaml
import pandas as pd
import ijson
import os

import convertSpaces
import convertIndicators
import convertDataRecords

#delete all files located in the output folder
for item in os.listdir("DataLifting_output"):
    itemPath = os.path.join("DataLifting_output", item)
    try:
        os.remove(itemPath)
    except OSError as e:
        print(f"Error:{ e.strerror}")


def parseArguments():
    """function used to parse the launch command-line aguments
    This feature is currently not implemented"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--hasSpaceType", type=str, choices=["Territory", "Partition", "Zone"],
                        help="e.g: Territory, Partition, Zone")
    return parser.parse_args()

"""
An improvement can be added for two following functions by checking not only the first object
of the file, but by checking a certain amount of them.
This so the file is correctly sorted even if the first object is not correctly formed
"""
def getJsonKeys(filepath, nestedKey=None):
    """Extract json properties from the first JSON object of the file."""

    try:
        with open(filepath, 'rb') as f:

            jsonStructure = getJsonStructureType(filepath)
            
            # construct prefix
            if nestedKey:
                prefix = f"item.{nestedKey}.item" if jsonStructure == "array" else f"{nestedKey}.item"
            else:
                prefix = 'item' if jsonStructure == "array" else ''
            

            objects = ijson.items(f, prefix, multiple_values=True)
            
            firstObj = next(objects, None)

            #get and return the corresponding keys of the first object of the file
            if isinstance(firstObj, dict):
                return set(firstObj.keys())

    except (StopIteration, ijson.JSONError, FileNotFoundError) as e:
        print(f"Error while reading file {filepath} (prefix '{prefix}') : {e}")

    return set()


def getGeoJsonKeys(filepath):
    """Extract json properties from the first GeoJSON object of the file."""

    try:
        with open(filepath, 'rb') as f:
            #construct the profix to collect only property names
            objects = ijson.items(f, 'features.item.properties')
            
            firstObj = next(objects, None)

            if isinstance(firstObj, dict):
                return set(firstObj.keys())
            
    except (StopIteration, ijson.JSONError) as e:
        print(f"Error GeoJSON {filepath} : {e}")
    return set()

def getJsonStructureType(filepath):
    """Determine if the JSON file is an array or a list of objects."""
    try:
        with open(filepath, 'rb') as f:
            parser = ijson.parse(f)
            firstEvent = next(parser)
            return 'array' if firstEvent[0] == '' and firstEvent[1] == 'start_array' else 'line'
    except StopIteration:
        return "empty"

def classifyCSV(filepath, signatures):
    """Classify a CSV file based on columns."""
    try:
        columns = set(pd.read_csv(filepath, nrows=0, sep=';').columns)
    except Exception as e:
        print(f"Error while reading CSV {filepath}: {e}")
        return None

    hasIndicatorSpaceIDs = signatures["IndicatorSpaceIDs"].issubset(columns)
    hasLinkedIndicatorSpaceIDs = signatures["hasLinkedIndicator"].issubset(columns)

    if signatures["flatRecords"].issubset(columns) and hasLinkedIndicatorSpaceIDs:
        #CSV file for records
        return {"type": "CSV_records", "categories": ["space", "indicator", "record"]}
    elif signatures["indicators"].issubset(columns) and hasIndicatorSpaceIDs:
        #CSV file for indicators
        return {"type": "CSV_indicators", "categories": ["space", "indicator"]}
    elif signatures["potentialPartition"].issubset(columns):
        #CSV file for spaces
        return {"type": "CSV_spaces", "categories": ["space"]}
    
    return None

def classifyJSON(filepath, config, signatures):
    """Classify a JSON file based on its root and nested properties."""
    rootKeys = getJsonKeys(filepath)
    
    recordsPrefix = config["mapping_indicators"].get("hasRecords")
    spacesPrefix = config["mapping_indicators"].get("hasTerritories")
    containsPrefix = config["mapping_spaces"].get("contains")
    
    hasRootIndicators = signatures["indicators"].issubset(rootKeys)
    hasRootSpaces = signatures["spaces"].issubset(rootKeys)
    hasRootSpacesEmbedded = signatures["potentialPartition"].issubset(rootKeys)
    hasRootRecords = signatures["flatRecords"].issubset(rootKeys)
    hasRootIndicatorSpaceIDs = signatures["IndicatorSpaceIDs"].issubset(rootKeys)
    hasRootLinkedIndicatorSpaceIDs = signatures["hasLinkedIndicator"].issubset(rootKeys)

    hasNestedIndicatorRecords = signatures["nestedRecords"].issubset(getJsonKeys(filepath, recordsPrefix)) if recordsPrefix else False
    hasNestedIndicatorSpaces = signatures["IndicatorSpaceIDs"].issubset(getJsonKeys(filepath, spacesPrefix)) if spacesPrefix else False
    hasNestedSpacesSpaces = signatures["potentialPartition"].issubset(getJsonKeys(filepath, containsPrefix)) if containsPrefix else False
    hasNestedSpatialLocation = signatures["hasSpatialLocation"].issubset(getJsonKeys(filepath, recordsPrefix)) if recordsPrefix else False
    hasNestedOriginDestination = signatures["hasOriginDestination"].issubset(getJsonKeys(filepath, recordsPrefix)) if recordsPrefix else False

    jsonType = getJsonStructureType(filepath)
    result = {"format": jsonType, "categories": []}

    #Indicator json
    if hasRootIndicators and not hasRootRecords:
        if hasNestedIndicatorRecords and not hasNestedIndicatorSpaces and hasRootIndicatorSpaceIDs:
            if (hasNestedOriginDestination and not hasNestedSpatialLocation) or (not hasNestedOriginDestination and hasNestedSpatialLocation):
                #JSON file for records embedded into the indicator they are linked to
                result.update({"type": "hierarchical json indicator-records", "categories": ["space", "indicator", "record"]})
            else:
                return None
        elif not hasNestedIndicatorRecords and hasNestedIndicatorSpaces and not hasRootIndicatorSpaceIDs:
            #JSON file for spaces embedded into the indicator they are linked to
            result.update({"type": "hierarchical json indicator-spaces", "categories": ["space", "indicator"]})
        elif hasRootIndicators and hasRootIndicatorSpaceIDs and not hasNestedIndicatorRecords and not hasNestedIndicatorSpaces:
            #flat JSON file for indicators
            result.update({"type": "flatJSON_indicators", "categories": ["space", "indicator"]})
        else:
            return None
            
    # nested spaces
    elif hasRootSpacesEmbedded and hasNestedSpacesSpaces:
        #JSON file for spaces embedded into their parent space
        result.update({"type": "hierarchical json spaces", "categories": ["space"]})

    # flat json
    elif hasRootRecords and hasRootLinkedIndicatorSpaceIDs:
        #flat JSON file for records
        result.update({"type": "flatJSON_records", "categories": ["space", "indicator", "record"]})
    elif hasRootSpaces:
        #flat JSON file for spaces
        result.update({"type": "flatJSON_spaces", "categories": ["space"]})
    else:
        return None

    return result

def main():
    args = parseArguments()
    
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    #a set of signatures representing the mandatory properties for each element
    signatures = {
        "spaces": set([
            config["mapping_spaces"]["hasSpaceID"],
            config["mapping_spaces"]["hasName"],
            config["mapping_spaces"]["hasSpaceType"]
        ]),
        "potentialPartition": set([
            config["mapping_spaces"]["hasSpaceID"],            
            config["mapping_spaces"]["hasSpaceType"]
        ]),
        "IndicatorSpaceIDs": set([
            config["mapping_indicators"]["onTerritoryName"],
            config["mapping_indicators"]["onTerritorySpaceID"],
        ]),
        "indicators": set([
            config["mapping_indicators"]["hasIndicatorType"], 
            config["mapping_indicators"]["hasCalculationMethod"], 
            config["mapping_indicators"]["hasObject"],
        ]),
        "flatRecords": set([
            config["mapping_records"]["hasValue"],
            config["mapping_records"]["linkedIndicatorType"],
            config["mapping_records"]["linkedObject"],
            config["mapping_records"]["linkedCalculationMethod"]
        ]),
        "nestedRecords": set([
            config["mapping_records"]["hasValue"]
        ]),
        "hasSpatialLocation": set([
            config["mapping_records"]["onSpatialLocationID"],
            config["mapping_records"]["onSpatialLocationName"]
        ]),
        "hasOriginDestination": set([
            config["mapping_records"]["onOriginID"],
            config["mapping_records"]["onOriginName"],
            config["mapping_records"]["onDestinationID"],
            config["mapping_records"]["onDestinationName"]
        ]),
        "hasLinkedIndicator": set([
            config["mapping_records"]["linkedIndicatorTerritoryName"],
            config["mapping_records"]["linkedIndicatorTerritorySpaceID"]
        ]),
    }

    #data structure made to contain the classification of each file
    filesByCategory = {
        "space": set(),
        "indicator": set(),
        "record": set(),
        "geometry": set()
    }

    inputFolder = Path(config["sources"]["inputFolder"])
    
    if not inputFolder.exists():
        print(f"Error : Input folder {inputFolder} doesn't exist.")
        sys.exit(1)

    #for each file contained in the input folder
    for filepath in inputFolder.iterdir():
        if not filepath.is_file():
            continue

        print(f"Analyze {filepath.name}")
        classification = None
        fileTuple = None

        #we call classification function of their file type
        if filepath.suffix == '.csv':
            classification = classifyCSV(filepath, signatures)
            if classification:
                fileTuple = (filepath.name, classification["type"])
                
        elif filepath.suffix == '.json':
            classification = classifyJSON(filepath, config, signatures)
            if classification:
                fileTuple = (filepath.name, classification["type"], classification["format"])
                
        elif filepath.suffix == '.geojson':
            geojsonKeys = getGeoJsonKeys(filepath)
            if signatures["spaces"].issubset(geojsonKeys):
                #goejson containing spaces and their geometries
                filesByCategory["space"].add((filepath.name, "geojson"))
                print(f"-> classified as : space geojson file")
            else:
                #geojson containing only geometries and the spaceID and name they are linked to
                filesByCategory["geometry"].add((filepath.name, "geometries"))
                print(f"-> classified as : geometry geojson file")
            continue
            
        else:
            print(f"not recognized format ignored : {filepath.name}")
            continue

        #Add the files to the classification sets if the format of the file correspond
        #to any handled file structure
        if classification and fileTuple:
            for category in classification["categories"]:
                filesByCategory[category].add(fileTuple)
            print(f"-> classified as : {classification['type']}")

    #Execute space conversion with the space and geometry files
    if filesByCategory["space"] and config.get("importParameters", {}).get("createSpaces"):
        convertSpaces.spaceConversion(
            filesByCategory["space"], 
            filesByCategory["geometry"], 
            args.hasSpaceType
        )

    #Execute indicator conversion with the indicator files
    if filesByCategory["indicator"] and config.get("importParameters", {}).get("createIndicators"):
        convertIndicators.indicatorConversion(
            filesByCategory["indicator"], 
            #indicator args
            args.hasSpaceType
        )

    #Execute record conversion with the record files
    if filesByCategory["record"] and config.get("importParameters", {}).get("createRecords"):
        convertDataRecords.recordConversion(
            filesByCategory["record"], 
            #record args
            args.hasSpaceType
        )

if __name__ == "__main__":
    main()