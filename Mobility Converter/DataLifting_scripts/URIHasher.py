import hashlib
import pandas as pd

def createURI(row, keys, prefix="space"):

    values = [row.get(key) for key in keys]
    if all(pd.isna(value) or value == "" for value in values):
        return None
    values = [str(value) for value in values]
    concatString = "-".join(values)
    hashedValue = hashlib.sha256(concatString.encode('utf-8')).hexdigest()
    
    return f"{prefix}-{hashedValue}"
