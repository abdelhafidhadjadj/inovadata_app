import numpy as np
import pandas as pd
from typing import List, Dict, Any


def clean_value_for_json(value):
    """
    Convert a single value to JSON-safe format
    - Convert numpy types to Python types
    - Replace NaN/Infinity with None
    - Keep all other values as-is (including "?", "-", etc.)
    """
    # None stays None
    if value is None:
        return None
    
    # Pandas NA
    if pd.isna(value):
        return None
    
    # Numpy integer -> Python int
    if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(value)
    
    # Numpy float -> Python float (check NaN/Inf)
    if isinstance(value, (np.floating, np.float64, np.float32, np.float16, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    
    # Numpy bool -> Python bool
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    
    # Everything else (strings, etc.) stays as-is
    return value


def clean_records_for_json(records: List[Dict]) -> List[Dict]:
    """
    Clean a list of records for JSON serialization
    """
    cleaned_records = []
    for row in records:
        cleaned_row = {}
        for key, value in row.items():
            cleaned_row[key] = clean_value_for_json(value)
        cleaned_records.append(cleaned_row)
    return cleaned_records