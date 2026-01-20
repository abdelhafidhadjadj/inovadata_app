import pandas as pd
import numpy as np
from sklearn.preprocessing import (
    StandardScaler, 
    MinMaxScaler, 
    RobustScaler, 
    LabelEncoder
)
from typing import List, Dict, Any, Tuple

class DataTransformer:
    """Handle data transformations using scikit-learn"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.transformations_history = []
    
    def normalize_columns(
        self, 
        columns: List[str], 
        method: str = 'zscore',
        feature_range: Tuple[float, float] = (0, 1)
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Normalize numerical columns using scikit-learn scalers
        
        Args:
            columns: List of column names to normalize
            method: 'zscore' (StandardScaler), 'minmax' (MinMaxScaler), or 'robust' (RobustScaler)
            feature_range: For minmax, the target range (default: 0-1)
        
        Returns:
            Tuple of (transformed dataframe, transformation info)
        """
        if not columns:
            raise ValueError("No columns specified for normalization")
        
        # Validate columns
        for col in columns:
            if col not in self.df.columns:
                raise ValueError(f"Column '{col}' not found in dataset")
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                raise ValueError(f"Column '{col}' is not numerical")
        
        # Choose scaler
        if method == 'zscore':
            scaler = StandardScaler()
            method_name = "Z-Score Standardization"
        elif method == 'minmax':
            scaler = MinMaxScaler(feature_range=feature_range)
            method_name = f"Min-Max Scaling {feature_range}"
        elif method == 'robust':
            scaler = RobustScaler()
            method_name = "Robust Scaling"
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        # Store original stats
        original_stats = {}
        for col in columns:
            original_stats[col] = {
                'mean': float(self.df[col].mean()),
                'std': float(self.df[col].std()),
                'min': float(self.df[col].min()),
                'max': float(self.df[col].max()),
                'median': float(self.df[col].median())
            }
        
        # Apply transformation
        self.df[columns] = scaler.fit_transform(self.df[columns])
        
        # Store new stats
        new_stats = {}
        for col in columns:
            new_stats[col] = {
                'mean': float(self.df[col].mean()),
                'std': float(self.df[col].std()),
                'min': float(self.df[col].min()),
                'max': float(self.df[col].max()),
                'median': float(self.df[col].median())
            }
        
        # Create transformation info
        transform_info = {
            'type': 'normalization',
            'method': method,
            'method_name': method_name,
            'columns': columns,
            'original_stats': original_stats,
            'new_stats': new_stats
        }
        
        if method == 'minmax':
            transform_info['feature_range'] = feature_range
        
        self.transformations_history.append(transform_info)
        
        return self.df, transform_info
    
    def encode_columns(self, columns: List[str], method: str = 'label_encoding', drop_first: bool = False):
        """
        Apply encoding to specified categorical columns
        
        Args:
            columns: List of column names to encode
            method: 'label_encoding' or 'onehot_encoding'
            drop_first: For one-hot encoding, drop first category to avoid multicollinearity
        """
        # ✅ Normaliser le nom de la méthode
        method = method.lower().replace('-', '_').replace(' ', '_')
        
        # ✅ Accepter plusieurs variantes
        if method in ['label', 'label_encoding', 'labelencoding']:
            method = 'label_encoding'
        elif method in ['onehot', 'one_hot', 'onehot_encoding', 'one_hot_encoding']:
            method = 'onehot_encoding'
        
        if method not in ['label_encoding', 'onehot_encoding']:
            raise ValueError(f"Unknown encoding method: {method}. Use 'label_encoding' or 'onehot_encoding'")
        
        df_encoded = self.df.copy()
        encodings_info = {}
        
        for col in columns:
            if col not in self.df.columns:
                raise ValueError(f"Column '{col}' not found in dataset")
            
            if method == 'label_encoding':
                # Label Encoding
                le = LabelEncoder()
                df_encoded[col] = le.fit_transform(self.df[col].astype(str))
                
                # Sauvegarder le mapping
                encodings_info[col] = {
                    'method': 'label_encoding',
                    'mapping': dict(zip(le.classes_, range(len(le.classes_))))
                }
                
            elif method == 'onehot_encoding':
                # One-Hot Encoding
                dummies = pd.get_dummies(
                    self.df[col], 
                    prefix=col, 
                    drop_first=drop_first
                )
                
                # Supprimer la colonne originale
                df_encoded = df_encoded.drop(columns=[col])
                
                # Ajouter les colonnes dummy
                df_encoded = pd.concat([df_encoded, dummies], axis=1)
                
                # Sauvegarder les informations
                encodings_info[col] = {
                    'method': 'onehot_encoding',
                    'new_columns': list(dummies.columns),
                    'drop_first': drop_first,
                    'original_categories': list(self.df[col].unique())
                }
        
        # Créer le résumé
        total_new_cols = sum(
            len(info.get('new_columns', [])) 
            for info in encodings_info.values() 
            if info['method'] == 'onehot_encoding'
        )
        
        total_encoded_cols = len([
            info for info in encodings_info.values() 
            if info['method'] == 'label_encoding'
        ])
        
        transformation_info = {
            'type': 'encoding',
            'method': method,
            'columns': columns,
            'encodings': encodings_info,
            'original_shape': self.df.shape,
            'new_shape': df_encoded.shape,
            'drop_first': drop_first if method == 'onehot_encoding' else None,
            'summary': {
                'total_columns_encoded': len(columns),
                'label_encoded': total_encoded_cols,
                'onehot_encoded': len(columns) - total_encoded_cols,
                'new_columns_added': total_new_cols,
                'columns_removed': len([
                    col for col in columns 
                    if encodings_info[col]['method'] == 'onehot_encoding'
                ])
            }
        }
        
        self.df = df_encoded
        
        return df_encoded, transformation_info    
    def preview_normalization(
        self,
        columns: List[str],
        method: str = 'zscore',
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """Preview normalization without applying it"""
        preview_df = self.df[columns].copy()
        
        # Get sample for preview
        if len(preview_df) > sample_size:
            sample_indices = np.random.choice(len(preview_df), sample_size, replace=False)
            preview_df = preview_df.iloc[sample_indices]
        
        # Create temporary transformer
        temp_transformer = DataTransformer(preview_df)
        transformed_df, info = temp_transformer.normalize_columns(columns, method)
        
        return {
            'original_stats': info['original_stats'],
            'preview_stats': info['new_stats'],
            'method': method,
            'method_name': info['method_name']
        }
    
    def preview_encoding(
        self,
        columns: List[str],
        method: str = 'label'
    ) -> Dict[str, Any]:
        """Preview encoding without applying it"""
        preview_info = {
            'method': method,
            'columns': columns,
            'mappings': {},
            'estimated_new_columns': 0
        }
        
        for col in columns:
            unique_values = self.df[col].dropna().unique().tolist()
            
            if method == 'label':
                preview_info['mappings'][col] = {
                    str(val): idx for idx, val in enumerate(sorted(unique_values))
                }
                preview_info['estimated_new_columns'] += 1
            
            elif method == 'onehot':
                n_dummies = len(unique_values)
                dummy_names = [f"{col}_{val}" for val in unique_values]
                preview_info['mappings'][col] = {
                    'original_values': unique_values,
                    'new_columns': dummy_names,
                    'count': n_dummies
                }
                preview_info['estimated_new_columns'] += n_dummies
        
        return preview_info
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get the transformed dataframe"""
        return self.df
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get transformation history"""
        return self.transformations_history