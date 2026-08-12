import pandas as pd
import geopandas as gpd
import shapely
import ijson
import json
from runMorphProcess import runMorphPipeline
import yaml
from URIHasher import createURI
from fileTools import extractFlatFileInfos

CHUNK_SIZE = 100000

spaceKeys = ["hasSpaceID", "hasName"]

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


def checkSpaceProperties(df):
    """function made to check if every values of the dataframe have mandatory values to create a space triple
    If a row is uncomplete, it is dropped."""
    idxToDelete = df.index[(df["hasSpaceType"].isna())].tolist()
    idxToDeletePartitions = df.index[(df["hasSpaceType"] == "Partition") & (df["hasSpaceID"].isna())].tolist()
    idxToDeleteSpaces = df.index[(df["hasSpaceType"] != "Partition") & ((df["hasSpaceID"].isna()) | df["hasName"].isna())].tolist()
    idxToDelete = list(set(idxToDelete + idxToDeletePartitions + idxToDeleteSpaces))
    df.drop(labels = idxToDelete, axis=0, inplace = True)
    return df
    
def computeCentroids(df):
    """function used to compute the centroid of a space in different format based on existing information in the dataframe"""
    wktCentroidList = []

    for idx, row in df.iterrows():

        if pd.notna(row.get("hasCentroidLatitude")) and pd.notna(row.get("hasCentroidLongitude")):
            centroidLatitude = row["hasCentroidLatitude"]
            centroidLongitude = row["hasCentroidLongitude"]

            if pd.notna(centroidLongitude) and pd.notna(centroidLatitude):
                pointGeom = shapely.Point(centroidLongitude, centroidLatitude)
                wktCentroidList.append(pointGeom.wkt)
        else:
            wktCentroidList.append(None)


    df["hasCentroidWKT"] = wktCentroidList

    return df

def computeGeometries(df):
    """function used to compute the geometry of a space in different formats based on existing information in the dataframe"""

    wktGeometryList = []

    for idx, row in df.iterrows():

        if pd.notna(row.get("geometry")):
            geo = shapely.geometry.shape(row["geometry"])
            wkt = (geo.wkt)

            wktGeometryList.append(wkt)

        else:
            wktGeometryList.append(None)

    df["hasGeometryWKT"] = wktGeometryList

    return df 


def flattenSpaceJSON(data, lineOrArray):
    """function used to flatten space embedded files"""

    columns = ["hasSpaceType", "hasSpaceID", "hasName", "hasParentSpaceID", "hasPopulation", "hasCentroidLatitude", "hasCentroidLongitude", "hasSqmArea"]
    df = pd.DataFrame(columns=columns)
    
    mapping = config["mapping_spaces"]

    def flatten (space, parentID):
        hasSpaceType = space.get(mapping.get("hasSpaceType")) 
        hasSpaceId = space.get(mapping.get("hasSpaceID"))
        hasName = space.get(mapping.get("hasName"))
        hasPopulation = space.get(mapping.get("hasPopulation"))
        hasCentroidLatitude = space.get(mapping.get("hasCentroidLatitude"))
        hasCentroidLongitude = space.get(mapping.get("hasCentroidLongitude"))
        hasSqmArea = space.get(mapping.get("hasSqmArea"))

        hasParentSpaceID = parentID
        df.loc[len(df.index)] = [hasSpaceType, hasSpaceId, hasName, hasParentSpaceID, hasPopulation, hasCentroidLatitude, hasCentroidLongitude, hasSqmArea]
        if space.get(mapping.get("contains")):
            for containedSpaces in space.get(mapping.get("contains")):
                flatten(containedSpaces, hasSpaceId)
    
    for item in data:
        flatten(item, None)

    df.reindex(columns=columns)
    return df



def JsonConversion(filePath: str, fileAnnotation: str, fileArchitecture: str, hasSpaceType: str | None):
    """function to convert a JSON file into a proper renamed and complete space dataframe"""
    prefix = "" if fileArchitecture == "line" else "item"

    if fileAnnotation.startswith("flatJSON"):
        if fileAnnotation == "flatJSON_spaces":
            df = extractFlatFileInfos(filePath, "JSON", config["mapping_spaces"], [config["mapping_spaces"]["contains"]],prefix)
        if fileAnnotation == "flatJSON_indicators":
            hybridMapping = config["mapping_spaces"].copy()
        
            hybridMapping["hasSpaceID"] = config["mapping_indicators"]["onTerritorySpaceID"]
            hybridMapping["hasName"] = config["mapping_indicators"]["onTerritoryName"]

            df = extractFlatFileInfos(filePath, "JSON", hybridMapping, [config["mapping_spaces"]["contains"]],prefix)
            df["hasSpaceType"] = "Territory"

        if fileAnnotation == "flatJSON_records":
            mappingSpatialLocation = config["mapping_spaces"].copy()

            mappingSpatialLocation["hasSpaceID"] = config["mapping_records"]["onSpatialLocationID"]
            mappingSpatialLocation["hasName"] = config["mapping_records"]["onSpatialLocationName"]

            dfSpatialLocation = extractFlatFileInfos(filePath, "JSON", mappingSpatialLocation, [config["mapping_spaces"]["contains"]],prefix)
            if not dfSpatialLocation.empty:
                dfSpatialLocation["hasSpaceType"] = "Zone"
                df = pd.concat([df, dfSpatialLocation], ignore_index=True)

            mappingOrigin = config["mapping_spaces"].copy()

            mappingOrigin["hasSpaceID"] = config["mapping_records"]["onOriginID"]
            mappingOrigin["hasName"] = config["mapping_records"]["onOriginName"]

            dfOrigin = extractFlatFileInfos(filePath, "JSON", mappingOrigin, [config["mapping_spaces"]["contains"]],prefix)

            if not dfOrigin.empty:
                dfOrigin["hasSpaceType"] = "Zone"
                df = pd.concat([df, dfOrigin], ignore_index=True)

            mappingDestination = config["mapping_spaces"].copy()

            mappingDestination["hasSpaceID"] = config["mapping_records"]["onDestinationID"]
            mappingDestination["hasName"] = config["mapping_records"]["onDestinationName"]

            dfDestination = extractFlatFileInfos(filePath, "JSON", mappingDestination, [config["mapping_spaces"]["contains"]],prefix)

            if not dfDestination.empty:
                dfDestination["hasSpaceType"] = "Zone"
                df = pd.concat([df, dfDestination], ignore_index=True)

            mappingIndicatorLinkedSpace = config["mapping_spaces"].copy()

            mappingIndicatorLinkedSpace["hasSpaceID"] = config["mapping_records"]["linkedIndicatorTerritorySpaceID"]
            mappingIndicatorLinkedSpace["hasName"] = config["mapping_records"]["linkedIndicatorTerritoryName"]

            dfIndicatorLinkedSpace = extractFlatFileInfos(filePath, "JSON", mappingIndicatorLinkedSpace, [config["mapping_spaces"]["contains"]],prefix)

            if not dfIndicatorLinkedSpace.empty:
                dfIndicatorLinkedSpace["hasSpaceType"] = "Territory"
                df = pd.concat([df, dfIndicatorLinkedSpace], ignore_index=True)

            df = df.drop_duplicates()

    if fileAnnotation == "hierarchical json spaces":
        with open(filePath,"r",encoding="UTF-8") as f:
            if fileArchitecture == "line":
                generator = ijson.items(f, '', multiple_values=True)
                data = list(generator)
            else:
                data = json.load(f)
        df=flattenSpaceJSON(data, fileArchitecture)


    if fileAnnotation == "hierarchical json indicator-records":
        spaces = []  

        with open(filePath, 'rb') as f:
            parser = ijson.parse(f, multiple_values=True)
            space = {}

            for prefix, event, value in parser:
                if event == 'start_map' and prefix in ('', 'item'):
                    space = {}
                    
                elif prefix.endswith(config["mapping_indicators"]["onTerritoryName"]):
                    space["hasName"] = value
                    
                elif prefix.endswith(config["mapping_indicators"]["onTerritorySpaceID"]):
                    space['hasSpaceID'] = value
                    
                elif event == 'end_map' and prefix in ('', 'item'):
                    if space.get("hasName") != None or space.get("hasSpaceID") != None:
                        space['hasSpaceType'] = "Territory"
                        spaces.append(space)

        with open(filePath, 'rb') as f:
            parser = ijson.parse(f, multiple_values=True)
            space = {}
            recordPropertyName = config["mapping_indicators"]["hasRecords"]

            for prefix, event, value in parser:
                if event == 'start_map' and prefix in (f'{recordPropertyName}.item', f'item.{recordPropertyName}.item'):
                    space = {}

                elif prefix.endswith(config["mapping_records"]["onSpatialLocationName"]) and config["mapping_records"]["onSpatialLocationName"] != "":
                    space["onSpatialLocationName"] = value
                elif prefix.endswith(config["mapping_records"]["onSpatialLocationID"]) and config["mapping_records"]["onSpatialLocationID"] != "":
                    space['onSpatialLocationID'] = value

                elif prefix.endswith(config["mapping_records"]["onOriginName"]) and config["mapping_records"]["onOriginName"] != "":
                    space["onOriginName"] = value
                elif prefix.endswith(config["mapping_records"]["onOriginID"]) and config["mapping_records"]["onOriginID"] != "":
                    space['onOriginID'] = value

                elif prefix.endswith(config["mapping_records"]["onDestinationName"]) and config["mapping_records"]["onDestinationName"] != "":
                    space["onDestinationName"] = value
                elif prefix.endswith(config["mapping_records"]["onDestinationID"]) and config["mapping_records"]["onDestinationID"] != "":
                    space['onDestinationID'] = value

                elif event == 'end_map' and prefix in (f'{recordPropertyName}.item', f'item.{recordPropertyName}.item'):
                    if space.get("onSpatialLocationName") != None or space.get("onSpatialLocationID") != None:
                        spaces.append({
                            "hasName": space.get("onSpatialLocationName"),
                            "hasSpaceID": space.get("onSpatialLocationID"),
                            "hasSpaceType": "Zone"
                        })
                    if space.get("onOriginName") != None or space.get("onOriginID") != None:
                        spaces.append({
                            "hasName": space.get("onOriginName"),
                            "hasSpaceID": space.get("onOriginID"),
                            "hasSpaceType": "Zone"
                        })
                    if space.get("onDestinationName") != None or space.get("onDestinationID") != None:
                        spaces.append({
                            "hasName": space.get("onDestinationName"),
                            "hasSpaceID": space.get("onDestinationID"),
                            "hasSpaceType": "Zone"
                        })

            
        df = pd.DataFrame(spaces).astype(str)
        df = df.replace({"nan": None})
        

    if fileAnnotation == "hierarchical json indicator-spaces":

        territories = []  
        territoriesPropertyName = config["mapping_indicators"]["hasTerritories"]
        prefix = prefix + f".{territoriesPropertyName}.item"  
        
        with open(filePath, 'rb') as f:
            parser = ijson.parse(f)
            objects = ijson.items(f, prefix, multiple_values=True)
            for obj in objects:
                if isinstance(obj, dict):
                    territories.append(obj)

        df = pd.DataFrame(territories).astype(str)
        df = df.replace({"nan": None})
        df["hasSpaceType"] = "Territory"
        df.rename(columns={config["mapping_indicators"]["onTerritoryName"]: "hasName"}, inplace=True)
        df.rename(columns={config["mapping_indicators"]["onTerritorySpaceID"]: "hasSpaceID"}, inplace=True)

    standardDFSchema = ["hasSpaceID", "hasName", "hasSpaceType", "hasPopulation", "hasParentSpaceID", "hasCentroidLatitude", "hasCentroidLongitude", "hasSqmArea"]
    df = df.reindex(columns=standardDFSchema)

    df = df.replace({"nan": None})

    if hasSpaceType:
        df["hasSpaceType"] = hasSpaceType
  
    df["hasID"] = df.apply(lambda row: createURI(row,spaceKeys,"space"), axis=1)


    df["hasCentroidLatitude"] = pd.to_numeric(df.get("hasCentroidLatitude"), errors="coerce")
    df["hasCentroidLongitude"] = pd.to_numeric(df.get("hasCentroidLongitude"), errors="coerce")

    df = computeCentroids(df)
    return df.dropna(axis=1, how='all')


def GeojsonConversion(filePath: str, hasSpaceType: str | None):
    """function to convert a GeoJSON file into a proper renamed and complete space dataframe"""

    gdf = gpd.read_file(filePath)
    df = pd.DataFrame(gdf)

    keyToExclude = [config["mapping_spaces"]["contains"]]
    renameMapping = {}
    
    for propertyName, CSVColumn in config["mapping_spaces"].items():
        if propertyName not in keyToExclude and CSVColumn is not None:
            renameMapping[CSVColumn] = propertyName

    columns = list(renameMapping.values())
    columns.append("geometry")

    df = df.rename(columns=renameMapping)
    df = df.reindex(columns=columns)

    df = df.replace({"nan": None})

    if hasSpaceType:
        df["hasSpaceType"]=hasSpaceType

    df["hasID"] = df.apply(lambda row: createURI(row,spaceKeys,"space"), axis=1)

    df = computeCentroids(df)
    df = computeGeometries(df)

    df = df.drop(columns=["geometry"])
    df = df.dropna(axis=1, how='all')

    return df


def CsvConversion(filePath: str, fileAnnotation: str, hasSpaceType: str | None):
    """function to convert a CSV file into a proper renamed and complete space dataframe"""

    df = pd.DataFrame()

    if fileAnnotation == "CSV_spaces":
        df = extractFlatFileInfos(filePath, "CSV", config["mapping_spaces"], [config["mapping_spaces"]["contains"]])
        
    if fileAnnotation == "CSV_indicators":
        hybridMapping = config["mapping_spaces"].copy()
    
        hybridMapping["hasSpaceID"] = config["mapping_indicators"]["onTerritorySpaceID"]
        hybridMapping["hasName"] = config["mapping_indicators"]["onTerritoryName"]

        df = extractFlatFileInfos(filePath, "CSV", hybridMapping, [config["mapping_spaces"]["contains"]])
        df["hasSpaceType"] = "Territory"

    if fileAnnotation == "CSV_records":

        mappingSpatialLocation = config["mapping_spaces"].copy()

        mappingSpatialLocation["hasSpaceID"] = config["mapping_records"]["onSpatialLocationID"]
        mappingSpatialLocation["hasName"] = config["mapping_records"]["onSpatialLocationName"]

        dfSpatialLocation = extractFlatFileInfos(filePath, "CSV", mappingSpatialLocation, [config["mapping_spaces"]["contains"]])

        if not dfSpatialLocation.empty:
            dfSpatialLocation["hasSpaceType"] = "Zone"
            df = pd.concat([df, dfSpatialLocation], ignore_index=True)          

        mappingOrigin = config["mapping_spaces"].copy()

        mappingOrigin["hasSpaceID"] = config["mapping_records"]["onOriginID"]
        mappingOrigin["hasName"] = config["mapping_records"]["onOriginName"]

        dfOrigin = extractFlatFileInfos(filePath, "CSV", mappingOrigin, [config["mapping_spaces"]["contains"]])

        if not dfOrigin.empty:
            dfOrigin["hasSpaceType"] = "Zone"
            df = pd.concat([df, dfOrigin], ignore_index=True)

        mappingDestination = config["mapping_spaces"].copy()

        mappingDestination["hasSpaceID"] = config["mapping_records"]["onDestinationID"]
        mappingDestination["hasName"] = config["mapping_records"]["onDestinationName"]

        dfDestination = extractFlatFileInfos(filePath, "CSV", mappingDestination, [config["mapping_spaces"]["contains"]])
        if not dfDestination.empty:
            dfDestination["hasSpaceType"] = "Zone"
            df = pd.concat([df, dfDestination], ignore_index=True)

        mappingIndicatorLinkedSpace = config["mapping_spaces"].copy()

        mappingIndicatorLinkedSpace["hasSpaceID"] = config["mapping_records"]["linkedIndicatorTerritorySpaceID"]
        mappingIndicatorLinkedSpace["hasName"] = config["mapping_records"]["linkedIndicatorTerritoryName"]
        mappingIndicatorLinkedSpace["hasParentSpaceID"] = ""

        dfIndicatorLinkedSpace = extractFlatFileInfos(filePath, "CSV", mappingIndicatorLinkedSpace, [config["mapping_spaces"]["contains"]])
        if not dfIndicatorLinkedSpace.empty:
            dfIndicatorLinkedSpace["hasSpaceType"] = "Territory"    
            df = pd.concat([df, dfIndicatorLinkedSpace], ignore_index=True)
        
        df = df.drop_duplicates()

    df = df.replace({"nan": None})
    
    if hasSpaceType:
        df["hasSpaceType"] = hasSpaceType
  
    df["hasID"] = df.apply(lambda row: createURI(row,spaceKeys,"space"), axis=1)


    df["hasCentroidLatitude"] = pd.to_numeric(df.get("hasCentroidLatitude"), errors="coerce")
    df["hasCentroidLongitude"] = pd.to_numeric(df.get("hasCentroidLongitude"), errors="coerce")

    df = computeCentroids(df)
    return df.dropna(axis=1, how='all')


def associateGeometries(dfData: pd.DataFrame, dfGeoms: pd.DataFrame):
    "function used to merge spaces dataframe with their geometries extracted from GeoJSON files"

    columnsGeoms = [
        "hasGeometryWKT", 
        "hasCentroidWKT", 
        "hasCentroidLatitude",
        "hasCentroidLongitude",
        "hasSqmArea"
    ]
    
    presentColumns = [col for col in columnsGeoms + ["hasAssociatedSpaceID"] + ["hasAssociatedName"] if col in dfGeoms.columns]
    dfGeoms = dfGeoms[presentColumns].copy()
    
    dfGeoms = dfGeoms.groupby(["hasAssociatedSpaceID","hasAssociatedName"], as_index=False).first()

    dfData["hasSpaceID"] = dfData["hasSpaceID"].astype(str)

    finalDF = pd.merge(
        dfData,
        dfGeoms,
        left_on=["hasSpaceID","hasName"],
        right_on=["hasAssociatedSpaceID","hasAssociatedName"],
        how="left",
        suffixes=("", "_geom") 
    )
    
    for col in columnsGeoms:
        colGeom = col + "_geom"
        
        if col in finalDF.columns and colGeom in finalDF.columns:
            finalDF[col] = finalDF[col].combine_first(finalDF[colGeom])
            finalDF = finalDF.drop(columns=[colGeom])
            
        elif colGeom in finalDF.columns:
            finalDF = finalDF.rename(columns={colGeom: col})
            
    if "hasAssociatedSpaceID" in finalDF.columns:
        finalDF = finalDF.drop(columns=["hasAssociatedSpaceID"])
    if "hasAssociatedName" in finalDF.columns:
            finalDF = finalDF.drop(columns=["hasAssociatedName"])

    return finalDF

def extractGeometryInfos(geometryFiles):
    "function used to extract geometries from geoJSON files made to complete another file without geometries"

    df = pd.DataFrame(columns=["hasAssociatedSpaceID", "hasAssociatedName", "hasCentroidLatitude", "hasCentroidLongitude","hasSqmArea"])
    
    for geometryFileName, geometryAnnotation in geometryFiles:
        geometryFilePath = f"{config["sources"]["inputFolder"]}/{geometryFileName}"
        gdfGeoms = gpd.read_file(geometryFilePath)
        dfGeoms = pd.DataFrame(gdfGeoms)

        dfGeoms.rename(columns={config["mapping_geometries"]["hasAssociatedSpaceID"]: "hasAssociatedSpaceID"}, inplace=True)
        dfGeoms.rename(columns={config["mapping_geometries"]["hasAssociatedName"]: "hasAssociatedName"}, inplace=True)
        dfGeoms.rename(columns={config["mapping_geometries"]["hasCentroidLatitude"]: "hasCentroidLatitude"}, inplace=True)
        dfGeoms.rename(columns={config["mapping_geometries"]["hasCentroidLongitude"]: "hasCentroidLongitude"}, inplace=True)
        dfGeoms.rename(columns={config["mapping_geometries"]["hasSqmArea"]: "hasSqmArea"}, inplace=True)
        
        standardGeometrySchema = ["geometry", "hasAssociatedSpaceID", "hasAssociatedName", "hasCentroidLatitude", "hasCentroidLongitude", "hasSqmArea"]
        dfGeoms = dfGeoms.reindex(columns=standardGeometrySchema)

        dfGeoms = computeCentroids(dfGeoms)
        dfGeoms = computeGeometries(dfGeoms)

        df = df.dropna(axis=1, how='all')
        dfGeoms = dfGeoms.dropna(axis=1, how='all')
        dfGeoms = dfGeoms.drop(columns=["geometry"])
        df = pd.concat([df, dfGeoms], ignore_index=True)

        groupbyColumns = ["hasAssociatedSpaceID"]
        if "hasAssociatedName" in df.columns:
            groupbyColumns.append("hasAssociatedName")

        df = df.groupby(groupbyColumns, as_index=False).first()
        dfGeoms = dfGeoms.reindex(columns=standardGeometrySchema)

    if "hasAssociatedSpaceID" in df.columns:
        df["hasAssociatedSpaceID"] = df["hasAssociatedSpaceID"].astype(int).astype(str)    
    else:
        df["hasAssociatedSpaceID"] = None
    if "hasSqmArea" in df.columns:
        df["hasSqmArea"] = df["hasSqmArea"].astype(str)
    df = df.dropna(axis=1, how='all')
    
    return df    

def spaceConversion(spaceFiles: set, geometryFiles: set, hasSpaceType: str | None):
    """function used to lauch the correct pipeline based on the file structure"""

    print("Space conversion beginning")

    dfGeoms = extractGeometryInfos(geometryFiles) if geometryFiles != set() else None

    df = pd.DataFrame()

    for spaceFileInfos in spaceFiles:
        fileName = spaceFileInfos[0]
        fileAnnotation = spaceFileInfos[1]

        filePath = f"{config["sources"]["inputFolder"]}/{fileName}"

        if fileAnnotation.startswith("CSV"): 
            print("csv file detected, conversion starting...")
            df = pd.concat([df, CsvConversion(filePath, fileAnnotation, hasSpaceType)],ignore_index=True)
        elif fileAnnotation == "geojson":
            print("geojson file detected, conversion starting...")
            df = pd.concat([df, GeojsonConversion(filePath, hasSpaceType)],ignore_index=True)
        else:
            print("json file detected, conversion starting...")
            fileArchitecture = spaceFileInfos[2]
            df = pd.concat([df, JsonConversion(filePath, fileAnnotation, fileArchitecture, hasSpaceType)],ignore_index=True)

    if "hasParentSpaceID" in df.columns and "hasSpaceID" in df.columns:
        dictTypes = df.dropna(subset=["hasSpaceID"]).set_index("hasSpaceID")["hasSpaceType"].to_dict()
        dictIds = df.dropna(subset=["hasSpaceID"]).set_index("hasSpaceID")["hasID"].to_dict()

        df["hasParentSpaceType"] = df["hasParentSpaceID"].map(dictTypes)
        df["hasParentID"] = df["hasParentSpaceID"].map(dictIds)

    df = associateGeometries(df, dfGeoms) if geometryFiles != set() else df
    
    df = checkSpaceProperties(df)
    runMorphPipeline(df,"space")
    
    print("Space conversion ended successfully")