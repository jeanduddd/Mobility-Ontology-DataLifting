import yaml
import pandas as pd
import ijson
from URIHasher import createURI
from fileTools import extractFlatFileInfosFromDF
from runMorphProcess import runMorphPipeline


with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

calculationMethodMapping = {
    "Count" : "Count",
    "Ratio" : "DimensionlessRatio",
    "Density" : "AreaDensity"
}

def checkRecordProperties(df):
    """function made to check if every values of the dataframe have mandatory values to create a record triple
    If a row is uncomplete, it is dropped."""
    idxToDeleteIndicator = df.index[(df["linkedIndicatorType"].isna()) | (df["linkedObject"].isna()) | (df["linkedCalculationMethod"].isna()) | (df["linkedIndicatorTerritorySpaceID"].isna()) | (df["linkedIndicatorTerritoryName"].isna())].tolist()
    idxToDeleteValue = df.index[(df["hasValue"].isna())].tolist()

    emptyColumn = pd.Series(pd.NA, index=df.index)

    hasStartTime = df.get("hasStartTime", emptyColumn).notna()
    hasEndTime = df.get("hasEndTime", emptyColumn).notna()

    keepMask = (hasStartTime & hasEndTime) | (~hasStartTime & ~hasEndTime)
    idxToDeleteTime = df.index[~keepMask].tolist()

    hasSpatialLocation = df.get("onSpatialLocationID", emptyColumn).notna() & df.get("onSpatialLocationName", emptyColumn).notna()
    hasOrigin = df.get("onOriginID", emptyColumn).notna() & df.get("onOriginName", emptyColumn).notna()
    hasDestination = df.get("onDestinationID", emptyColumn).notna() & df.get("onDestinationName", emptyColumn).notna()

    keepMask = (hasSpatialLocation & ~hasOrigin & ~hasDestination) | (~hasSpatialLocation & hasOrigin & hasDestination) | (~hasSpatialLocation & ~hasOrigin & ~hasDestination)
    idxToDeleteSpaces = df.index[~keepMask].tolist()

    idxToDelete = list(set(idxToDeleteIndicator + idxToDeleteSpaces + idxToDeleteValue + idxToDeleteTime))
    df.drop(idxToDelete, inplace=True)
    
    return df

def CsvConversion(chunk: pd.DataFrame, fileAnnotation: str, hasSpaceType: str | None):
    """function to convert chunk dataframes extracted from a CSV file into a proper renamed and complete record dataframe"""

    df = pd.DataFrame()
    
    if fileAnnotation == "CSV_records":
        df = extractFlatFileInfosFromDF(chunk, "CSV", config["mapping_records"], [config["mapping_indicators"]["hasRecords"], config["mapping_indicators"]["hasTerritories"]])

    if hasSpaceType:
        df["hasSpaceType"] = hasSpaceType

    if "hasTransportationMode" in df.columns:
        df.loc[df["hasTransportationMode"].notna(), "hasTransportationModeTheme"] = "TransportationMode"
    else:
        df["hasTransportationModeTheme"] = None

    if "hasTripPurpose" in df.columns:
        df.loc[df["hasTripPurpose"].notna(), "hasTripPurposeTheme"] = "TripPurpose"
    else:
        df["hasTripPurposeTheme"] = None
    #TODO uncomment when population profile is set up
    # if "hasPopulationProfile" in df.columns:
    #     df.loc[df["hasPopulationProfile"].notna(), "hasPopulationProfileTheme"] = "PopulationProfile"
    # else:
    #     df["hasTripPurposeTheme"] = None


    recordKeys = ["hasOriginID","hasDestinationID","hasSpatialLocationID","hasLinkedIndicatorID","hasTripPurpose","hasTransportationMode","hasStartTime","hasEndTime","hasPopulationProfile"]

    linkedTerritoryKeys = ["linkedIndicatorTerritorySpaceID", "linkedIndicatorTerritoryName"]
    #TODO add indicator key "hasPopulationProfile" when population profile is set up
    indicatorKeys = ["linkedIndicatorType", "linkedObject", "linkedCalculationMethod", "hasLinkedTerritoryID", "hasTransportationModeTheme", "hasTripPurposeTheme"]

    spatialLocationKeys = ["onSpatialLocationID", "onSpatialLocationName"]
    originKeys = ["onOriginID", "onOriginName"]
    destinationKeys = ["onDestinationID", "onDestinationName"]

    df["hasOriginID"] = df.apply(lambda row: createURI(row,originKeys,"space"),axis=1)
    df["hasDestinationID"] = df.apply(lambda row: createURI(row,destinationKeys,"space"),axis=1)
    df["hasSpatialLocationID"] = df.apply(lambda row: createURI(row,spatialLocationKeys,"space"),axis=1)

    df["hasLinkedTerritoryID"] = df.apply(lambda row: createURI(row,linkedTerritoryKeys,"space"),axis=1)
    df["linkedCalculationMethod"] = df["linkedCalculationMethod"].map(calculationMethodMapping)

    df["hasLinkedIndicatorID"] = df.apply(lambda row: createURI(row,indicatorKeys,"indicator"),axis=1)


    df["hasID"] = df.apply(lambda row: createURI(row,recordKeys,"record"),axis=1)

    emptyCol = pd.Series(pd.NA, index=df.index)
    df["isTimeAggregated"] = (
        df.get("hasStartTime", emptyCol).isna() &
        df.get("hasEndTime", emptyCol).isna()
    )
    df["isSpaceAggregated"] = (
        df.get("hasSpatialLocationID", emptyCol).isna() & 
        df.get("hasOriginID", emptyCol).isna() & 
        df.get("hasDestinationID", emptyCol).isna()      
    )

    return df.dropna(axis=1, how='all')


def JsonConversion(chunk: pd.DataFrame, fileAnnotation, fileArchitecture, hasSpaceType):
    """function to convert chunk dataframes extracted from a JSON file into a proper renamed and complete record dataframe"""
    prefix = "" if fileArchitecture == "line" else "item"

    if fileAnnotation.startswith("flatJSON"):
        if fileAnnotation == "flatJSON_records":
            df = extractFlatFileInfosFromDF(chunk, "JSON", config["mapping_records"],[])            

    if fileAnnotation == "hierarchical json indicator-records":

        hybridMapping = config["mapping_records"].copy()

        hybridMapping["linkedIndicatorType"] = config["mapping_indicators"]["hasIndicatorType"]
        hybridMapping["linkedObject"] = config["mapping_indicators"]["hasObject"]
        hybridMapping["linkedCalculationMethod"] = config["mapping_indicators"]["hasCalculationMethod"]
        hybridMapping["linkedIndicatorTerritoryName"] = config["mapping_indicators"]["onTerritoryName"]
        hybridMapping["linkedIndicatorTerritorySpaceID"] = config["mapping_indicators"]["onTerritorySpaceID"]

        df = extractFlatFileInfosFromDF(chunk, "JSON", hybridMapping, [])

    if hasSpaceType:
        df["hasSpaceType"] = hasSpaceType

    if "hasTransportationMode" in df.columns:
        df.loc[df["hasTransportationMode"].notna(), "hasTransportationModeTheme"] = "TransportationMode"
    else:
        df["hasTransportationModeTheme"] = None

    if "hasTripPurpose" in df.columns:
        df.loc[df["hasTripPurpose"].notna(), "hasTripPurposeTheme"] = "TripPurpose"
    else:
        df["hasTripPurposeTheme"] = None
    #TODO uncomment when population profile is set up
    # if "hasPopulationProfile" in df.columns:
    #     df.loc[df["hasPopulationProfile"].notna(), "hasPopulationProfileTheme"] = "PopulationProfile"
    # else:
    #     df["hasTripPurposeTheme"] = None

    recordKeys = ["hasOriginID","hasDestinationID","hasSpatialLocationID","hasLinkedIndicatorID","hasTripPurpose","hasTransportationMode","hasStartTime","hasEndTime","hasPopulationProfile"]

    linkedTerritoryKeys = ["linkedIndicatorTerritorySpaceID", "linkedIndicatorTerritoryName"]
    #TODO add indicator key "hasPopulationProfile" when population profile is set up
    indicatorKeys = ["linkedIndicatorType", "linkedObject", "linkedCalculationMethod", "hasLinkedTerritoryID", "hasTransportationModeTheme", "hasTripPurposeTheme"]

    spatialLocationKeys = ["onSpatialLocationID", "onSpatialLocationName"]
    originKeys = ["onOriginID", "onOriginName"]
    destinationKeys = ["onDestinationID", "onDestinationName"]

    df["hasOriginID"] = df.apply(lambda row: createURI(row,originKeys,"space"),axis=1)
    df["hasDestinationID"] = df.apply(lambda row: createURI(row,destinationKeys,"space"),axis=1)
    df["hasSpatialLocationID"] = df.apply(lambda row: createURI(row,spatialLocationKeys,"space"),axis=1)

    df["hasLinkedTerritoryID"] = df.apply(lambda row: createURI(row,linkedTerritoryKeys,"space"),axis=1)
    df["linkedCalculationMethod"] = df["linkedCalculationMethod"].map(calculationMethodMapping)

    df["hasLinkedIndicatorID"] = df.apply(lambda row: createURI(row,indicatorKeys,"indicator"),axis=1)


    df["hasID"] = df.apply(lambda row: createURI(row,recordKeys,"record"),axis=1)

    emptyCol = pd.Series(pd.NA, index=df.index)
    df["isTimeAggregated"] = (
        df.get("hasStartTime", emptyCol).isna() &
        df.get("hasEndTime", emptyCol).isna()
    )
    df["isSpaceAggregated"] = (
        df.get("hasSpatialLocationID", emptyCol).isna() & 
        df.get("hasOriginID", emptyCol).isna() & 
        df.get("hasDestinationID", emptyCol).isna()      
    )

    return df.dropna(axis=1, how='all')


def getDataChunks(filePath: str, fileType: str, chunkSize: int = 100000):
    """Read a file and yield fixed sized dataframes."""
    if fileType == "CSV":
        chunkIterator = pd.read_csv(filePath, sep=';', dtype=str, chunksize=chunkSize)
        for chunk in chunkIterator:
            yield chunk

    elif fileType == "flatJSON_records":

        chunkRecords = []

        with open(filePath, 'rb') as f:
            parser = ijson.parse(f)

            try:
                firstEvent = next(parser)
            except StopIteration:
                return set()
            
            isArray = (firstEvent[1] == 'start_array')
            prefix = 'item' if isArray else ''

            f.seek(0)

            objects = ijson.items(f, prefix, multiple_values=True)
            for obj in objects:
                if isinstance(obj, dict):
                    chunkRecords.append(obj)
                    if len(chunkRecords) >= chunkSize:
                        yield pd.DataFrame(chunkRecords).astype(str)
                        chunkRecords = []
            if chunkRecords:
                yield pd.DataFrame(chunkRecords).astype(str)

                    
    elif fileType == "hierarchical json indicator-records":

        with open(filePath, 'rb') as f:
            parser = ijson.parse(f, multiple_values=True)
            chunkRecords = []
            indicatorData = {}

            currentRecord = {}
            inRecord = False
            recordPrefix = ""

            for prefix, event, value in parser:
                recordPropertyName = config["mapping_indicators"]["hasRecords"]
                if f'.{recordPropertyName}.item' in prefix or prefix.startswith(f'{recordPropertyName}.item'):
                    if event == 'start_map' and not inRecord:
                        inRecord = True
                        recordPrefix = prefix
                        currentRecord = {}
                        
                    elif event == 'end_map' and prefix == recordPrefix:
                        merged = {**currentRecord, **{k: v for k, v in indicatorData.items()}}
                        chunkRecords.append(merged)
                        inRecord = False
                        
                        if len(chunkRecords) >= chunkSize:
                            yield pd.DataFrame(chunkRecords).astype(str)
                            chunkRecords = []
                            
                    elif inRecord and event not in ('start_map', 'end_map', 'start_array', 'end_array', 'map_key'):
                        key = prefix[len(recordPrefix)+1:]
                        currentRecord[key] = value

                elif event not in ('start_map', 'end_map', 'start_array', 'end_array', 'map_key'):
                    key = prefix.split('.')[-1] if '.' in prefix else prefix
                    if key and key != recordPropertyName:
                        indicatorData[key] = value

            if chunkRecords:
                yield pd.DataFrame(chunkRecords).astype(str)

#todo changer les params 
def recordConversion(recordFiles: set, hasSpaceType: str | None):
    """function used to lauch the correct pipeline based on the file structure"""

    print("records conversion beginning")

    df = pd.DataFrame()

    batchNumber = -1
    for recordFileInfos in recordFiles:
        fileName = recordFileInfos[0]
        fileAnnotation = recordFileInfos[1]

        filePath = f"{config["sources"]["inputFolder"]}/{fileName}"
        
        if fileAnnotation.startswith("CSV"):
            print("csv file detected, conversion starting...")
            for chunk in getDataChunks(filePath, "CSV"):
                batchNumber+=1
                print(f"processing batch {batchNumber} of records")
                df = CsvConversion(chunk, fileAnnotation, hasSpaceType)
                df = df.replace({"nan": None})
                checkRecordProperties(df)
                runMorphPipeline(df,"record", batchNumber if batchNumber != 0 else "")
                
        else:   
            print("json file detected, conversion starting...")
            fileArchitecture = recordFileInfos[2]
            for chunk in getDataChunks(filePath, fileAnnotation):
                batchNumber+=1
                print(f"processing batch {batchNumber} of records")
                df = JsonConversion(chunk, fileAnnotation, fileArchitecture, hasSpaceType)
                df = df.replace({"nan": None})
                checkRecordProperties(df)
                runMorphPipeline(df,"record", batchNumber if batchNumber != 0 else "")

    print("Record conversion ended successfully")