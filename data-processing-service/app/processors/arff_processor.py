import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class ARFFProcessor:
    """Process ARFF files"""
    
    @staticmethod
    def read(file_path: str) -> pd.DataFrame:
        """
        Read ARFF file in permissive mode - keeps ALL values as-is
        """
        try:
            logger.info(f"Reading ARFF file: {file_path}")
            return ARFFProcessor._read_permissive(file_path)
            
        except Exception as e:
            logger.error(f"Error reading ARFF file: {e}")
            raise
    
    @staticmethod
    def _read_permissive(file_path: str) -> pd.DataFrame:
        """
        Read ARFF file line by line - keeps ALL values exactly as they are
        No automatic conversion to NaN
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Trouver @DATA et extraire les attributs
            data_start = None
            attributes = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Ignorer commentaires et lignes vides
                if line.startswith('%') or not line:
                    continue
                
                # Extraire les attributs
                if line.upper().startswith('@ATTRIBUTE'):
                    parts = line.split(None, 2)
                    if len(parts) >= 3:
                        attr_name = parts[1].strip("'\"")
                        attr_type = parts[2].strip()
                        attributes.append({
                            'name': attr_name,
                            'type': attr_type
                        })
                
                # Marquer le début des données
                elif line.upper() == '@DATA':
                    data_start = i + 1
                    break
            
            if data_start is None:
                raise ValueError("No @DATA section found")
            
            if not attributes:
                raise ValueError("No @ATTRIBUTE declarations found")
            
            column_names = [attr['name'] for attr in attributes]
            logger.info(f"Found {len(attributes)} attributes: {column_names}")
            
            # Lire les données
            data_lines = []
            for line in lines[data_start:]:
                line = line.strip()
                if line and not line.startswith('%'):
                    data_lines.append(line)
            
            logger.info(f"Found {len(data_lines)} data lines")
            
            # Parser les données
            rows = []
            for line_num, line in enumerate(data_lines, start=data_start + 1):
                try:
                    # Parser en gérant les guillemets
                    values = []
                    current_value = ""
                    in_quotes = False
                    
                    for char in line:
                        if char == "'" or char == '"':
                            in_quotes = not in_quotes
                        elif char == ',' and not in_quotes:
                            values.append(current_value.strip().strip("'\""))
                            current_value = ""
                        else:
                            current_value += char
                    
                    # Dernière valeur
                    if current_value:
                        values.append(current_value.strip().strip("'\""))
                    
                    # ✅ IMPORTANT : Garder TOUTES les valeurs telles quelles
                    # Ne PAS convertir ?, ??, !!, etc. en NaN
                    # L'utilisateur les marquera comme missing manuellement
                    
                    rows.append(values)
                    
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
                    continue
            
            # Créer le DataFrame
            df = pd.DataFrame(rows, columns=column_names)
            
            # Inférer les types SANS remplacer les valeurs
            for i, attr in enumerate(attributes):
                col_name = attr['name']
                attr_type = attr['type'].lower()
                
                try:
                    if 'numeric' in attr_type or 'real' in attr_type or 'integer' in attr_type:
                        # ✅ Convertir en numérique MAIS garder les non-numériques comme NaN
                        # errors='coerce' : les valeurs non numériques deviennent NaN
                        # MAIS on veut garder les strings !
                        
                        # Solution : créer une copie pour tester
                        test_col = pd.to_numeric(df[col_name], errors='coerce')
                        
                        # Si TOUTES les valeurs sont convertibles, c'est numérique pur
                        # Sinon, garder comme string pour que l'utilisateur voie les "!!"
                        if test_col.notna().sum() > len(df) * 0.9:  # 90% sont numériques
                            df[col_name] = test_col
                        # Sinon on garde comme string
                        
                    elif 'date' in attr_type:
                        df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
                    
                    # Nominal values = garder comme string
                    
                except Exception as e:
                    logger.warning(f"Could not convert {col_name}: {e}")
            
            logger.info(f"✅ Read ARFF: {len(df)} rows, {len(df.columns)} columns")
            
            # Log des premières valeurs pour debug
            for col in df.columns[:3]:
                sample_values = df[col].value_counts().head(5)
                logger.info(f"Column '{col}' sample values: {sample_values.to_dict()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error reading ARFF: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def write(df: pd.DataFrame, file_path: str) -> None:
        """Write DataFrame to file"""
        try:
            csv_path = file_path.replace('.arff', '.csv')
            df.to_csv(csv_path, index=False)
            logger.info(f"Written to CSV: {csv_path}")
        except Exception as e:
            logger.error(f"Error writing: {e}")
            raise
    
    @staticmethod
    def get_preview(file_path: str, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int, List[str]]:
        """Get preview of data"""
        try:
            df = ARFFProcessor.read(file_path)
            total_rows = len(df)
            
            preview_df = df.iloc[offset:offset + limit]
            records = preview_df.to_dict('records')
            
            from app.utils import clean_records_for_json
            clean_data = clean_records_for_json(records)
            
            return clean_data, total_rows, df.columns.tolist()
            
        except Exception as e:
            logger.error(f"Error getting preview: {e}")
            raise
    
    # ✅ AJOUTER CES 3 MÉTHODES À LA FIN
    
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame):
        """Analyze DataFrame - delegates to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.analyze_dataframe(df)
    
    @staticmethod
    def analyze_column_advanced(
        series: pd.Series,
        column_name: str,
        custom_missing_values: list = None,
        detect_outliers: bool = True
    ):
        """Advanced column analysis - delegates to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.analyze_column_advanced(
            series, 
            column_name, 
            custom_missing_values, 
            detect_outliers
        )
    
    @staticmethod
    def detect_outliers_range(
        series: pd.Series,
        min_val: float = None,
        max_val: float = None
    ):
        """Detect outliers by range - delegates to CSVProcessor"""
        from .csv_processor import CSVProcessor
        return CSVProcessor.detect_outliers_range(series, min_val, max_val)