import pandas as pd
import ijson
import itertools

CHUNK_SIZE = 100000

def extractFlatFileInfos(filePath, fileType, mappingDict, keysToExclude, jsonPrefix=""):
    """Global function used to read, rename, filter and drop duplicates for a flat JSON or CSV file in batches."""
    
    renameMapping = {}
    columns = []

    for propertyName, CSVColumn in mappingDict.items():
        if propertyName not in keysToExclude:
            columns.append(propertyName)
            if CSVColumn is not None and CSVColumn != "":
                renameMapping[CSVColumn] = propertyName
    
    processedChunks = []

    if fileType == "CSV":
        try:
            #read the file by chunk of size CHUNK_SIZE
            chunkIterator = pd.read_csv(filePath, sep=';', dtype=str, chunksize=CHUNK_SIZE)
            #for each chunk, rename the columns, keep only useful columns then drop duplicated rows.
            for chunk in chunkIterator:
                chunk = chunk.rename(columns=renameMapping)
                chunk = chunk.reindex(columns=columns)
                chunk = chunk.drop_duplicates()
                processedChunks.append(chunk)
        except Exception as e:
            print(f"Error while reading the CSV file : {e}")

    elif fileType == "JSON":
        try:
            with open(filePath, 'rb') as f:
                objects = ijson.items(f, jsonPrefix, multiple_values=True)
                while True:
                    #read the first CHUNK_SIZE objects of the json file
                    batch = list(itertools.islice(objects, CHUNK_SIZE))
                    if not batch:
                        break
                    #for each batch, rename the columns, keep only useful columns then drop duplicated rows.
                    chunk = pd.DataFrame(batch)
                    chunk = chunk.rename(columns=renameMapping)
                    chunk = chunk.reindex(columns=columns)
                    chunk = chunk.drop_duplicates()
                    processedChunks.append(chunk)
                    
        except (StopIteration, ijson.JSONError, FileNotFoundError) as e:
            print(f"Error while reading the JSON file : {e}")
            
    else:
        print(f"Error : File type '{fileType}' not convertible")
        return pd.DataFrame(columns=columns)

    if not processedChunks:
        print("Empty file")
        return pd.DataFrame(columns=columns)

    df = pd.concat(processedChunks, ignore_index=True)
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    
    return df



def extractFlatFileInfosFromDF(chunk, fileType, mappingDict, keysToExclude, jsonPrefix=""):
    """Global function used to rename, filter and drop duplicates for a flat JSON or CSV file in batches.
    Already take in input a dataframe."""
    
    renameMapping = {}
    columns = []

    for propertyName, CSVColumn in mappingDict.items():
        if propertyName not in keysToExclude:
            columns.append(propertyName)
            if CSVColumn is not None and CSVColumn != "":
                renameMapping[CSVColumn] = propertyName
    
    processedChunks = []

    try:
        #rename the columns, keep only useful columns then drop duplicated rows of the chunk passed in argument.
        chunk = chunk.rename(columns=renameMapping)
        chunk = chunk.reindex(columns=columns)
        chunk = chunk.drop_duplicates()
            
    except Exception as e:
        print(f"Error while reading the file : {e}")
    
    chunk = chunk.drop_duplicates()
    
    return chunk

def renameColumns (df, mappingDict, keysToExclude):
    """function used to rename the row names of the DataFrame"""
    renameMapping = {}
    
    for propertyName, CSVColumn in mappingDict.items():
        if propertyName not in keysToExclude and CSVColumn != "":
            renameMapping[CSVColumn] = propertyName

    columns = list(renameMapping.values())
    df = df.rename(columns=renameMapping)
    
    return df
