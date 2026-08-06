import yaml
import pandas as pd
import ijson
from URIHasher import createURI
from fileTools import extractFlatFileInfos, renameColumns
from runMorphProcess import runMorphPipeline


with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

indicatorClassMapping = {
    "Presence": "Territory",
    "Fluctuation": "Territory",
    "Attractiveness": "Territory",
    "TravelFlow": "Movement",
    "MobilityRate": "Movement",
    "AttributeShare": "Movement"
}

calculationMethodMapping = {
    "Count" : "Count",
    "Ratio" : "DimensionlessRatio",
    "Density" : "AreaDensity"
}

def checkIndicatorProperties(df):
    """function made to check if every values of the dataframe have mandatory values to create an indicator triple
    If a row is uncomplete, it is dropped."""
    idxToDelete = df.index[(df["hasIndicatorType"].isna()) | (df["hasObject"].isna()) | (df["onTerritorySpaceID"].isna()) | (df["onTerritoryName"].isna())].tolist()
    df.drop(labels = idxToDelete, axis=0, inplace = True)
    return df

#TODO add indicator key "hasPopulationProfile" when population profile is set up
indicatorKeys = ["hasIndicatorType", "hasObject", "hasCalculationMethod", "hasLinkedTerritoryID","hasTransportationModeTheme", "hasTripPurposeTheme"]
territoryKeys = ["onTerritorySpaceID", "onTerritoryName"]

def CsvConversion(filePath: str, fileAnnotation: str, hasSpaceType: str | None):
    """function to convert a CSV file into a proper renamed and complete indicator dataframe"""
    df = pd.DataFrame()
    
    if fileAnnotation == "CSV_indicators":
        df = extractFlatFileInfos(filePath, "CSV", config["mapping_indicators"], ["hasRecords", "hasTerritories"])

    if fileAnnotation == "CSV_records":
        hybridMapping = config["mapping_indicators"].copy()

        hybridMapping["hasIndicatorType"] = config["mapping_records"]["linkedIndicatorType"]
        hybridMapping["hasObject"] = config["mapping_records"]["linkedObject"]
        hybridMapping["hasCalculationMethod"] = config["mapping_records"]["linkedCalculationMethod"]
        hybridMapping["onTerritoryName"] = config["mapping_records"]["linkedIndicatorTerritoryName"]
        hybridMapping["onTerritorySpaceID"] = config["mapping_records"]["linkedIndicatorTerritorySpaceID"]

        hybridMapping["hasTripPurposeTheme"] = config["mapping_records"]["hasTripPurpose"]
        hybridMapping["hasTransportationModeTheme"] = config["mapping_records"]["hasTransportationMode"]
        #TODO uncomment when population profile is set up
        #hybridMapping["hasPopulationProfileTheme"] = config["mapping_records"]["hasPopulationProfile"]

        df = extractFlatFileInfos(filePath, "CSV", hybridMapping, ["contains"])

        df["hasTransportationModeTheme"] = df["hasTransportationModeTheme"].apply(
            lambda x: "TransportationMode" if pd.notna(x) else x)
        df["hasTripPurposeTheme"] = df["hasTripPurposeTheme"].apply(
            lambda x: "TripPurpose" if pd.notna(x) else x)
        #TODO uncomment when population profile is set up
        # df["hasPopulationProfileTheme"] = df["hasPopulationProfileTheme"].apply(
        #     lambda x: "PopulationProfile" if pd.notna(x) else x)

    #todo mettre les vrais params
    # if hasSpaceType:
    #     df["hasSpaceType"] = hasSpaceType

    df["hasIndicatorClass"] = df["hasIndicatorType"].map(indicatorClassMapping)
    df["hasCalculationMethod"] = df["hasCalculationMethod"].map(calculationMethodMapping)

    df["hasLinkedTerritoryID"] = df.apply(lambda row: createURI(row,territoryKeys,"space"), axis=1)
    df["hasID"] = df.apply(lambda row: createURI(row,indicatorKeys,"indicator"),axis=1)

    return df.dropna(axis=1, how='all')


def JsonConversion(filePath, fileAnnotation, fileArchitecture, hasSpaceType):
    """function to convert a JSON file into a proper renamed and complete indicator dataframe"""

    prefix = "" if fileArchitecture == "line" else "item"

    if fileAnnotation.startswith("flatJSON"):
        if fileAnnotation == "flatJSON_indicators":
            df = extractFlatFileInfos(filePath, "JSON", config["mapping_indicators"], ["hasRecords", "hasTerritories"])
        if fileAnnotation == "flatJSON_records":
            hybridMapping = config["mapping_indicators"].copy()
    
            hybridMapping["hasIndicatorType"] = config["mapping_records"]["linkedIndicatorType"]
            hybridMapping["hasObject"] = config["mapping_records"]["linkedObject"]
            hybridMapping["hasCalculationMethod"] = config["mapping_records"]["linkedCalculationMethod"]
            hybridMapping["onTerritoryName"] = config["mapping_records"]["linkedIndicatorTerritoryName"]
            hybridMapping["onTerritorySpaceID"] = config["mapping_records"]["linkedIndicatorTerritorySpaceID"]
    
            hybridMapping["hasTripPurposeTheme"] = config["mapping_records"]["hasTripPurpose"]
            hybridMapping["hasTransportationModeTheme"] = config["mapping_records"]["hasTransportationMode"]
            #TODO uncomment when population profile is set up
            #hybridMapping["hasPopulationProfileTheme"] = config["mapping_records"]["hasPopulationProfile"]
    
            df = extractFlatFileInfos(filePath, "JSON", hybridMapping, ["hasRecords","hasTerritories"])

            df["hasTransportationModeTheme"] = df["hasTransportationModeTheme"].apply(
                lambda x: "TransportationMode" if pd.notna(x) else x)
            df["hasTripPurposeTheme"] = df["hasTripPurposeTheme"].apply(
                lambda x: "TripPurpose" if pd.notna(x) else x)
            #TODO uncomment when population profile is set up
            # df["hasPopulationProfileTheme"] = df["hasPopulationProfileTheme"].apply(
            #     lambda x: "PopulationProfile" if pd.notna(x) else x)

    if fileAnnotation == "hierarchical json indicator-spaces":

        with open(filePath, 'rb') as f:
            parser = ijson.parse(f, multiple_values=True)
            indicators = []
            indicatorData = {}

            currentSpace = {}
            inSpace = False
            spacePrefix = ""

            for prefix, event, value in parser:
                #TODO ici pas forcément hasTerritories, faut mettre le nom de la config
                if '.hasTerritories.item' in prefix or prefix.startswith('hasTerritories.item'):
                    if event == 'start_map' and not inSpace:
                        inSpace = True
                        spacePrefix = prefix
                        
                    elif event == 'end_map' and prefix == spacePrefix:
                        merged = {**currentSpace, **{k: v for k, v in indicatorData.items()}}
                        indicators.append(merged)
                        inSpace = False
                        
                            
                    elif inSpace and event not in ('start_map', 'end_map', 'start_array', 'end_array', 'map_key'):
                        key = prefix[len(spacePrefix)+1:]
                        currentSpace[key] = value

                elif event not in ('start_map', 'end_map', 'start_array', 'end_array', 'map_key'):
                    key = prefix.split('.')[-1] if '.' in prefix else prefix
                    #TODO ici pas forcément hasTerritories, faut mettre le nom de la config
                    if key and key != 'hasTerritories':
                        indicatorData[key] = value
    
        df = pd.DataFrame(indicators).astype(str)
        df = df.replace({"nan": None})
        df = renameColumns(df, config["mapping_indicators"],[config["mapping_indicators"]["hasRecords"], config["mapping_indicators"]["hasTerritories"]] )

    if fileAnnotation == "hierarchical json indicator-records":
        indicators = []      

        with open(filePath, 'rb') as f:
            parser = ijson.parse(f)
            objects = ijson.items(f, prefix, multiple_values=True)
            for obj in objects:
                if isinstance(obj, dict):
                    #TODO ici pas forcément hasRecords mais faut suppr le nom de la config
                    obj.__delitem__("hasRecords")
                    indicators.append(obj)

        df = pd.DataFrame(indicators).astype(str)
        df = df.replace({"nan": None})
        df = renameColumns(df, config["mapping_indicators"],[config["mapping_indicators"]["hasRecords"], config["mapping_indicators"]["hasTerritories"]] )

    #todo mettre les vrais params
    # if hasSpaceType:
    #     df["hasSpaceType"] = hasSpaceType

    df["hasIndicatorClass"] = df["hasIndicatorType"].map(indicatorClassMapping)
    df["hasCalculationMethod"] = df["hasCalculationMethod"].map(calculationMethodMapping)

    df["hasLinkedTerritoryID"] = df.apply(lambda row: createURI(row,territoryKeys,"space"), axis=1)
    df["hasID"] = df.apply(lambda row: createURI(row,indicatorKeys,"indicator"),axis=1)

    return df.dropna(axis=1, how='all')
    

#todo changer les params 
def indicatorConversion(indicatorFiles: set, hasSpaceType: str | None):
    """function used to lauch the correct pipeline based on the file structure"""

    print("Indicator conversion beginning")

    df = pd.DataFrame()

    for indicatorFileInfos in indicatorFiles:
        fileName = indicatorFileInfos[0]
        fileAnnotation = indicatorFileInfos[1]

        filePath = f"{config["sources"]["inputFolder"]}/{fileName}"

        if fileAnnotation.startswith("CSV"):
            print("csv file detected, conversion starting...")
            df = pd.concat([df, CsvConversion(filePath, fileAnnotation, hasSpaceType)],ignore_index=True)            
        else:
            print("json file detected, conversion starting...")
            fileArchitecture = indicatorFileInfos[2]
            df = pd.concat([df, JsonConversion(filePath, fileAnnotation, fileArchitecture, hasSpaceType)],ignore_index=True)

    df = checkIndicatorProperties(df)
    runMorphPipeline(df,"indicator")

    print("Indicator conversion ended successfully")