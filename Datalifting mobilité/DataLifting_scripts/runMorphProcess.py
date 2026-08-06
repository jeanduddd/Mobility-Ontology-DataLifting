import subprocess
import pandas as pd
from pymongo import MongoClient
import numpy as np

def runMorphPipeline(df: pd.DataFrame, type2convert: str, batchNumber: str = ""):
    """import the dataframe in a MongoDB data base then start the rdf conversion with Morph-xR2RML tool"""
    
    client = MongoClient("mongodb://localhost:27017/")

    db = "database"    
    xr2rml_container = "morph-xr2rml"
    collection = ""

    if type2convert == "space":
        collection = "space2convert" 
        mapping = "mapping_Space.ttl"
        output = "space.ttl"
    elif type2convert == "indicator":
        collection = "indicator2convert" 
        mapping = "mapping_Indicator.ttl"
        output = "indicator.ttl"
    elif type2convert == "record":
        collection = "record2convert" 
        mapping = "mapping_Record.ttl"
        output = f"record{batchNumber}.ttl"
    
    mongo_db = client[db]
    mongo_collection = mongo_db[collection]

    df = df.replace({np.nan: None})
    df = df.replace({"nan": None})
    records_json = df.to_dict(orient='records')

    print("importing the batch in MongoDB")

    if records_json:
        mongo_collection.drop()
        mongo_collection.insert_many(records_json)

    cmd_morph = f"docker exec -w /xr2rml_config {xr2rml_container} /bin/bash run_xr2rml_template.sh {mapping} {output} dataset1.0 {collection}"
    
    try:
        subprocess.run(cmd_morph, shell=True, check=True)

    except subprocess.CalledProcessError:
        print("Error: can't convert the data using Morph-xR2RML.")
