import hashlib
import pandas as pd

def createURI(row, keys, prefix="space"):

    rawValues = [row.get(key) for key in keys]
    if all(pd.isna(value) or value is None or value == "" for value in rawValues):
        return None
    
    cleanValues = []
    for val in rawValues:
        if not pd.isna(val) and val is not None and val != "":
            valStr = str(val)
            if valStr.endswith(".0"):
                valStr = valStr[:-2]
            cleanValues.append(valStr)
            
    concatString = "-".join(cleanValues)
    hashedValue = hashlib.sha256(concatString.encode('utf-8')).hexdigest()
    
    return f"{prefix}-{hashedValue}"