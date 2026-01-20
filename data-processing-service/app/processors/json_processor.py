import pandas as pd
import json
from typing import Dict, List, Any, Tuple
from ..models import ColumnInfo
import logging

logger = logging.getLogger(__name__)


class JSONProcessor:
    """Processor for JSON files"""
    
    @staticmethod
    def read(file_path: str, sample_size: int = None) -> pd.DataFrame:
        """Read JSON file and return DataFrame"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try to find the data array
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'records' in data:
                    df = pd.DataFrame(data['records'])
                else:
                    # Assume it's a single record
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Unsupported JSON structure")
            
            if sample_size:
                df = df.head(sample_size)
            
            logger.info(f"Successfully read JSON file with {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            raise
    
    @staticmethod
    def get_preview(file_path: str, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int, List[str]]:
        """Get preview data from JSON"""
        df = JSONProcessor.read(file_path)
        total_rows = len(df)
        
        # Apply pagination
        preview_df = df.iloc[offset:offset + limit]
        
        # CORRECTION: Garder les valeurs originales
        records = preview_df.to_dict('records')
        
        # Nettoyer seulement NaN/Infinity, garder les strings originales
        cleaned_data = []
        for row in records:
            cleaned_row = {}
            for key, value in row.items():
                # Garder les strings comme "?", "-", "N/A"
                if isinstance(value, str):
                    cleaned_row[key] = value
                # Nettoyer seulement les NaN/Infinity
                elif isinstance(value, (float, np.floating)):
                    if pd.isna(value) or np.isnan(value) or np.isinf(value):
                        cleaned_row[key] = None
                    else:
                        cleaned_row[key] = float(value)
                elif isinstance(value, (np.integer, np.int64, np.int32)):
                    cleaned_row[key] = int(value)
                elif isinstance(value, (np.bool_, bool)):
                    cleaned_row[key] = bool(value)
                elif value is None:
                    cleaned_row[key] = None
                else:
                    cleaned_row[key] = value
            cleaned_data.append(cleaned_row)
        
        columns = df.columns.tolist()
        
        return cleaned_data, total_rows, columns
        
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame) -> List[ColumnInfo]:
        """Analyze JSON DataFrame - reuse CSV processor logic"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.analyze_dataframe(df)
    
    # ========== DÉLÉGUER LES MÉTHODES DE PREPROCESSING À CSVProcessor ==========
    
    @staticmethod
    def detect_custom_missing_values(series: pd.Series, custom_values: List[str]) -> pd.Series:
        """Delegate to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.detect_custom_missing_values(series, custom_values)
    
    @staticmethod
    def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> Dict[str, Any]:
        """Delegate to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.detect_outliers_iqr(series, multiplier)
    
    @staticmethod
    def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> Dict[str, Any]:
        """Delegate to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.detect_outliers_zscore(series, threshold)
    
    @staticmethod
    def detect_outliers_range(series: pd.Series, min_val: float = None, max_val: float = None) -> Dict[str, Any]:
        """Delegate to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.detect_outliers_range(series, min_val, max_val)
    
    @staticmethod
    def get_value_frequencies(series: pd.Series, top_n: int = 20) -> Dict[str, int]:
        """Delegate to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.get_value_frequencies(series, top_n)
    
    @staticmethod
    def analyze_column_advanced(series: pd.Series, column_name: str, 
                               custom_missing: List[str] = None,
                               detect_outliers: bool = True) -> Dict[str, Any]:
        """Delegate to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.analyze_column_advanced(series, column_name, custom_missing, detect_outliers)