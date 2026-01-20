import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from ..models import DataType
import logging
from ..utils import clean_records_for_json
logger = logging.getLogger(__name__)


class CSVProcessor:
    """Processor for CSV files"""
    
    @staticmethod
    def read(file_path: str, sample_size: int = None) -> pd.DataFrame:
        """Read CSV file and return DataFrame"""
        try:
            # Try to read with different encodings
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    if sample_size:
                        df = pd.read_csv(file_path, encoding=encoding, nrows=sample_size)
                    else:
                        df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Successfully read CSV with encoding: {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, try with error handling
            df = pd.read_csv(file_path, encoding='utf-8', errors='replace')
            return df
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    @staticmethod
    def get_preview(file_path: str, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int, List[str]]:
        """Get preview data from CSV"""
        df = CSVProcessor.read(file_path)
        total_rows = len(df)
        
        # Apply pagination
        preview_df = df.iloc[offset:offset + limit]
        
        # Convert to dict and clean for JSON
        records = preview_df.to_dict('records')
        cleaned_records = clean_records_for_json(records)
        columns = df.columns.tolist()
        
        return cleaned_records, total_rows, columns

    
    @staticmethod
    def infer_data_type(series: pd.Series) -> DataType:
        """Infer the data type of a pandas Series"""
        # Remove null values for type checking
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return DataType.TEXT
        
        # Check if boolean
        if series.dtype == 'bool' or set(non_null.unique()).issubset({0, 1, True, False, 'True', 'False', 'true', 'false'}):
            return DataType.BOOLEAN
        
        # Check if numeric
        if pd.api.types.is_numeric_dtype(series):
            return DataType.NUMERICAL
        
        # Try to convert to datetime
        try:
            pd.to_datetime(non_null.head(100))
            return DataType.DATETIME
        except:
            pass
        
        # Check if categorical (low cardinality relative to size)
        unique_ratio = len(non_null.unique()) / len(non_null)
        if unique_ratio < 0.5 and len(non_null.unique()) < 100:
            return DataType.CATEGORICAL
        
        return DataType.TEXT
    
    @staticmethod
    def analyze_column(series: pd.Series, column_name: str):
        """Analyze a single column and return ColumnInfo (méthode originale)"""
        total_count = len(series)
        missing_count = series.isna().sum()
        missing_percentage = (missing_count / total_count * 100) if total_count > 0 else 0
        
        # Get non-null values
        non_null = series.dropna()
        unique_count = len(non_null.unique())
        
        # Sample values (first 5 non-null unique values)
        sample_values = non_null.unique()[:5].tolist()
        
        # Infer data type
        data_type = CSVProcessor.infer_data_type(series)
        
        from ..models import ColumnInfo
        
        column_info = ColumnInfo(
            name=column_name,
            data_type=data_type,
            missing_count=int(missing_count),
            missing_percentage=round(float(missing_percentage), 2),
            unique_count=int(unique_count),
            sample_values=sample_values
        )
        
        # Add statistics based on data type
        if data_type == DataType.NUMERICAL and len(non_null) > 0:
            try:
                column_info.mean = round(float(non_null.mean()), 4)
                column_info.std = round(float(non_null.std()), 4)
                column_info.min = round(float(non_null.min()), 4)
                column_info.max = round(float(non_null.max()), 4)
                column_info.median = round(float(non_null.median()), 4)
                column_info.q25 = round(float(non_null.quantile(0.25)), 4)
                column_info.q75 = round(float(non_null.quantile(0.75)), 4)
            except Exception as e:
                logger.warning(f"Could not compute statistics for {column_name}: {e}")
        
        elif data_type == DataType.CATEGORICAL and len(non_null) > 0:
            # Get top 10 most frequent values
            value_counts = non_null.value_counts().head(10)
            column_info.top_values = {str(k): int(v) for k, v in value_counts.items()}
        
        return column_info
    
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame) -> List:
        """Analyze entire DataFrame and return column information (méthode originale)"""
        columns_info = []
        
        for column in df.columns:
            try:
                col_info = CSVProcessor.analyze_column(df[column], column)
                columns_info.append(col_info)
            except Exception as e:
                logger.error(f"Error analyzing column {column}: {e}")
                from ..models import ColumnInfo
                # Add basic info even if analysis fails
                columns_info.append(ColumnInfo(
                    name=column,
                    data_type=DataType.TEXT,
                    missing_count=0,
                    missing_percentage=0.0,
                    unique_count=0,
                    sample_values=[]
                ))
        
        return columns_info
    
    # ========== NOUVELLES MÉTHODES POUR PREPROCESSING AVANCÉ ==========
    
    @staticmethod
    def detect_custom_missing_values(series: pd.Series, custom_values: List[str]) -> pd.Series:
        """
        Detect custom missing values (?, ??, -, etc.)
        Returns a boolean Series indicating which values are considered missing
        """
        # Convert to string for comparison
        series_str = series.astype(str)
        
        # Default suspicious values
        default_suspicious = ['?', '??', '-', '--', 'N/A', 'n/a', 'NA', 'null', 'NULL', 
                             'None', 'NONE', '', ' ', 'unknown', 'Unknown', 'UNKNOWN',
                             '.', '..', '...', '#N/A', '#NA', 'NaN', 'nan']
        
        # Combine with custom values
        all_suspicious = list(set(default_suspicious + (custom_values or [])))
        
        # Check if value is in suspicious list
        is_missing = series_str.isin(all_suspicious)
        
        return is_missing
    
    @staticmethod
    def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> Dict[str, Any]:
        """
        Detect outliers using IQR method
        """
        # Only for numerical columns
        if not pd.api.types.is_numeric_dtype(series):
            return {'method': 'iqr', 'outliers_count': 0, 'outliers_indices': []}
        
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'method': 'iqr', 'outliers_count': 0, 'outliers_indices': []}
        
        Q1 = non_null.quantile(0.25)
        Q3 = non_null.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        outliers = (series < lower_bound) | (series > upper_bound)
        outliers_indices = series[outliers].index.tolist()
        
        return {
            'method': 'iqr',
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'q1': float(Q1),
            'q3': float(Q3),
            'iqr': float(IQR),
            'multiplier': multiplier,
            'outliers_count': int(outliers.sum()),
            'outliers_indices': outliers_indices[:100]  # Limit to first 100
        }
    
    @staticmethod
    def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> Dict[str, Any]:
        """
        Detect outliers using Z-score method
        """
        if not pd.api.types.is_numeric_dtype(series):
            return {'method': 'zscore', 'outliers_count': 0, 'outliers_indices': []}
        
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'method': 'zscore', 'outliers_count': 0, 'outliers_indices': []}
        
        mean = non_null.mean()
        std = non_null.std()
        
        if std == 0:
            return {'method': 'zscore', 'outliers_count': 0, 'outliers_indices': []}
        
        z_scores = np.abs((series - mean) / std)
        outliers = z_scores > threshold
        outliers_indices = series[outliers].index.tolist()
        
        return {
            'method': 'zscore',
            'mean': float(mean),
            'std': float(std),
            'threshold': threshold,
            'outliers_count': int(outliers.sum()),
            'outliers_indices': outliers_indices[:100]
        }
    
    @staticmethod
    def detect_outliers_range(series: pd.Series, min_val: float = None, max_val: float = None) -> Dict[str, Any]:
        """
        Detect values outside a specified range
        """
        if not pd.api.types.is_numeric_dtype(series):
            return {'method': 'range', 'outliers_count': 0, 'outliers_indices': []}
        
        outliers = pd.Series([False] * len(series), index=series.index)
        
        if min_val is not None:
            outliers |= series < min_val
        if max_val is not None:
            outliers |= series > max_val
        
        outliers_indices = series[outliers].index.tolist()
        
        return {
            'method': 'range',
            'min_value': min_val,
            'max_value': max_val,
            'outliers_count': int(outliers.sum()),
            'outliers_indices': outliers_indices[:100]
        }
    
    @staticmethod
    def get_value_frequencies(series: pd.Series, top_n: int = 20) -> Dict[str, int]:
        """
        Get frequency distribution of all values
        """
        value_counts = series.value_counts().head(top_n)
        return {str(k): int(v) for k, v in value_counts.items()}
    
    @staticmethod
    def analyze_column_advanced(series: pd.Series, column_name: str, 
                               custom_missing: List[str] = None,
                               detect_outliers: bool = True) -> Dict[str, Any]:
        """
        Advanced column analysis with custom missing values and outlier detection
        """
        total_count = len(series)
        
        # Standard missing values
        standard_missing = series.isna().sum()
        
        # Custom missing values
        custom_missing_mask = CSVProcessor.detect_custom_missing_values(
            series, custom_missing or []
        )
        custom_missing_count = custom_missing_mask.sum()
        
        # Total missing (standard + custom)
        total_missing = standard_missing + custom_missing_count
        missing_percentage = (total_missing / total_count * 100) if total_count > 0 else 0
        
        # Get sample of suspicious values
        suspicious_values = series[custom_missing_mask].unique()[:10].tolist()
        
        # Non-null values (excluding both standard and custom missing)
        valid_mask = ~(series.isna() | custom_missing_mask)
        non_null = series[valid_mask]
        unique_count = len(non_null.unique())
        
        # Infer data type
        data_type = CSVProcessor.infer_data_type(non_null)
        
        result = {
            'name': column_name,
            'data_type': data_type.value,
            'total_count': int(total_count),
            'standard_missing_count': int(standard_missing),
            'custom_missing_count': int(custom_missing_count),
            'total_missing_count': int(total_missing),
            'missing_percentage': round(float(missing_percentage), 2),
            'unique_count': int(unique_count),
            'suspicious_values': [str(v) for v in suspicious_values],
            'value_frequencies': CSVProcessor.get_value_frequencies(series)
        }
        
        # Outlier detection for numerical columns
        if detect_outliers and data_type == DataType.NUMERICAL and len(non_null) > 0:
            result['outliers'] = {
                'iqr': CSVProcessor.detect_outliers_iqr(non_null),
                'zscore': CSVProcessor.detect_outliers_zscore(non_null)
            }
        
        # Statistics for numerical columns
        if data_type == DataType.NUMERICAL and len(non_null) > 0:
            try:
                result['statistics'] = {
                    'mean': round(float(non_null.mean()), 4),
                    'std': round(float(non_null.std()), 4),
                    'min': round(float(non_null.min()), 4),
                    'max': round(float(non_null.max()), 4),
                    'median': round(float(non_null.median()), 4),
                    'q25': round(float(non_null.quantile(0.25)), 4),
                    'q75': round(float(non_null.quantile(0.75)), 4)
                }
            except:
                pass
        
        # Top values for categorical
        if data_type == DataType.CATEGORICAL and len(non_null) > 0:
            value_counts = non_null.value_counts().head(10)
            result['top_values'] = {str(k): int(v) for k, v in value_counts.items()}
        
        return result