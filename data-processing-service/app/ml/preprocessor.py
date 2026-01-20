import joblib
import json
import pandas as pd
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Apply saved transformations to new data"""
    
    def __init__(self, transformations_path: str):
        """Load transformations config"""
        if not os.path.exists(transformations_path):
            raise FileNotFoundError(f"Transformations file not found: {transformations_path}")
        
        with open(transformations_path, 'r') as f:
            self.config = json.load(f)
        
        self.categorical_columns = self.config.get('categorical_columns', [])
        self.numerical_columns = self.config.get('numerical_columns', [])
        self.feature_columns = self.config.get('feature_columns', [])
        
        # Charger le scaler
        self.scaler = None
        if 'scaler_path' in self.config and os.path.exists(self.config['scaler_path']):
            self.scaler = joblib.load(self.config['scaler_path'])
            logger.info(f"✅ Loaded scaler from {self.config['scaler_path']}")
        
        # Charger les encoders
        self.encoders = {}
        if 'encoders_path' in self.config and os.path.exists(self.config['encoders_path']):
            self.encoders = joblib.load(self.config['encoders_path'])
            logger.info(f"✅ Loaded {len(self.encoders)} encoders")
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply transformations to new data"""
        df = df.copy()
        
        # Vérifier les colonnes requises
        missing_cols = set(self.feature_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Sélectionner uniquement les features nécessaires dans le bon ordre
        df = df[self.feature_columns].copy()
        
        logger.info(f"📊 Processing {len(df)} samples with {len(df.columns)} features")
        
        # Appliquer les encoders aux colonnes catégorielles
        if self.categorical_columns and self.encoders:
            logger.info(f"🔄 Encoding {len(self.categorical_columns)} categorical columns...")
            for col in self.categorical_columns:
                if col in df.columns and col in self.encoders:
                    encoder = self.encoders[col]
                    
                    # Convertir en string et gérer les valeurs inconnues
                    df[col] = df[col].fillna('_MISSING_')
                    df[col] = df[col].astype(str)
                    
                    unknown_mask = ~df[col].isin(encoder.classes_)
                    
                    if unknown_mask.any():
                        logger.warning(f"⚠️  Column '{col}' has {unknown_mask.sum()} unknown values")
                        # Utiliser la classe la plus fréquente (index 0)
                        most_frequent = encoder.classes_[0]
                        df.loc[unknown_mask, col] = most_frequent
                    
                    df[col] = encoder.transform(df[col])
                    logger.info(f"  ✅ Encoded '{col}'")
        
        # Appliquer le scaler aux colonnes numériques
        if self.numerical_columns and self.scaler:
            logger.info(f"🔄 Normalizing {len(self.numerical_columns)} numerical columns...")
            df[self.numerical_columns] = self.scaler.transform(df[self.numerical_columns])
            logger.info(f"  ✅ Normalized")
        
        logger.info(f"✅ Transformation completed")
        return df