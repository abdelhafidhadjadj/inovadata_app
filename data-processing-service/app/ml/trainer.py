import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score, roc_curve, auc
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import os
import json
from datetime import datetime
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class MLTrainer:
    """Classe principale pour l'entraînement des modèles ML"""
    
    def __init__(self, dataset_path: str, experiment_config: Dict):
        self.dataset_path = dataset_path
        self.config = experiment_config
        self.model = None
        self.metrics = {}
        
        # ✅ NOUVEAU : Transformations
        self.scaler = None
        self.label_encoders = {}
        self.target_encoder = None
        self.categorical_columns = []
        self.numerical_columns = []
        self.original_target_classes = None
        
    def load_data(self) -> pd.DataFrame:
        """Charge le dataset"""
        try:
            # Détecter le format
            if self.dataset_path.endswith('.csv'):
                df = pd.read_csv(self.dataset_path)
            elif self.dataset_path.endswith('.json'):
                df = pd.read_json(self.dataset_path)
            else:
                raise ValueError(f"Format non supporté: {self.dataset_path}")
            
            logger.info(f"Dataset chargé: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur chargement dataset: {str(e)}")
            raise
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prépare les données avec encodage et normalisation automatiques"""

        # Extraire features et target
        feature_columns = self.config['feature_columns']
        target_column = self.config['target_column']

        # Nettoyer les noms de colonnes du DataFrame
        df.columns = df.columns.str.strip()

        # Log pour debug
        logger.info(f"Colonnes disponibles dans le dataset: {list(df.columns)}")
        logger.info(f"Colonnes demandées - Target: {target_column}, Features: {feature_columns}")

        # Vérifier que les colonnes existent
        available_columns = list(df.columns)
        missing_cols = set(feature_columns + [target_column]) - set(available_columns)
        if missing_cols:
            raise ValueError(f"Colonnes manquantes: {missing_cols}")

        # Extraire les données
        X_df = df[feature_columns].copy()
        y_series = df[target_column].copy()

        # Log des types de données
        logger.info(f"Types des features AVANT transformation: {X_df.dtypes.to_dict()}")
        logger.info(f"Type de la target AVANT transformation: {y_series.dtype}")

        # ✅ NOUVEAU : Identifier les colonnes catégorielles et numériques
        self.categorical_columns = []
        self.numerical_columns = []
        
        for col in feature_columns:
            if X_df[col].dtype == 'object' or X_df[col].dtype.name == 'category':
                self.categorical_columns.append(col)
            else:
                self.numerical_columns.append(col)
        
        logger.info(f"Colonnes catégorielles détectées: {self.categorical_columns}")
        logger.info(f"Colonnes numériques détectées: {self.numerical_columns}")

        # ✅ NOUVEAU : Encoder les colonnes catégorielles des features
        if self.categorical_columns:
            logger.info("🔄 Encodage des colonnes catégorielles...")
            for col in self.categorical_columns:
                encoder = LabelEncoder()
                # Gérer les valeurs manquantes
                X_df[col] = X_df[col].fillna('_MISSING_')
                X_df[col] = encoder.fit_transform(X_df[col].astype(str))
                self.label_encoders[col] = encoder
                logger.info(f"  ✅ Encodé '{col}': {list(encoder.classes_)[:5]}...")

        # ✅ NOUVEAU : Encoder la target si c'est de la classification
        algorithm = self.config['algorithm']
        is_regression = algorithm in ['linear_regression']
        
        if not is_regression:
            if y_series.dtype == 'object' or y_series.dtype.name == 'category':
                logger.info("🔄 Encodage de la target (classification)...")
                self.target_encoder = LabelEncoder()
                y_series = pd.Series(self.target_encoder.fit_transform(y_series.astype(str)))
                self.original_target_classes = self.target_encoder.classes_
                logger.info(f"  ✅ Classes encodées: {dict(zip(self.target_encoder.classes_, range(len(self.target_encoder.classes_))))}")
        else:
            # Régression : s'assurer que c'est numérique
            try:
                y_series = pd.to_numeric(y_series, errors='coerce')
            except:
                raise ValueError(f"Target column '{target_column}' must be numeric for regression")

        # ✅ NOUVEAU : Normaliser les colonnes numériques
        if self.numerical_columns:
            logger.info("🔄 Normalisation des colonnes numériques...")
            self.scaler = StandardScaler()
            X_df[self.numerical_columns] = self.scaler.fit_transform(X_df[self.numerical_columns])
            logger.info(f"  ✅ Normalisé {len(self.numerical_columns)} colonnes")
            logger.info(f"  📊 Mean: {self.scaler.mean_[:3]}...")
            logger.info(f"  📊 Std: {self.scaler.scale_[:3]}...")

        # Convertir en numpy arrays
        X = X_df.values.astype(np.float64)
        y = y_series.values

        # Vérifier les valeurs manquantes
        if np.isnan(X).any():
            nan_count = np.isnan(X).sum()
            logger.warning(f"⚠️  {nan_count} valeurs NaN détectées après transformation, remplissage avec 0")
            X = np.nan_to_num(X, nan=0.0)

        if np.isnan(y).any():
            raise ValueError("Des valeurs manquantes ont été détectées dans la colonne target après transformation")

        # Train/test split
        train_ratio = self.config.get('train_ratio', 0.8)
        random_seed = self.config.get('random_seed', 42)

        # Split avec ou sans stratify selon le type de problème
        if is_regression or not self._can_stratify(y):
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                train_size=train_ratio,
                random_state=random_seed
            )
            logger.info("Split non stratifié (régression ou classes insuffisantes)")
        else:
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y,
                    train_size=train_ratio,
                    random_state=random_seed,
                    stratify=y
                )
                logger.info("Split stratifié (classification)")
            except Exception as e:
                logger.warning(f"Stratify échoué: {str(e)}. Split non stratifié utilisé.")
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y,
                    train_size=train_ratio,
                    random_state=random_seed
                )

        logger.info(f"✅ Split: {len(X_train)} train, {len(X_test)} test")
        logger.info(f"✅ Shape X_train: {X_train.shape}, Shape y_train: {y_train.shape}")

        return X_train, X_test, y_train, y_test
    
    def _can_stratify(self, y):
        """Vérifie si on peut faire un split stratifié"""
        try:
            unique_values = np.unique(y)
            # Au moins 2 échantillons par classe
            return len(unique_values) < len(y) / 2
        except:
            return False
    
    def save_transformations(self, experiment_id: int, project_id: int) -> str:
        """Sauvegarde les transformations (scaler + encoders) pour la prédiction"""
        
        models_dir = f"/app/models/project_{project_id}"
        os.makedirs(models_dir, exist_ok=True)
        
        transformations = {
            'feature_columns': self.config['feature_columns'],
            'target_column': self.config['target_column'],
            'categorical_columns': self.categorical_columns,
            'numerical_columns': self.numerical_columns,
            'algorithm': self.config['algorithm']
        }
        
        # Sauvegarder le scaler
        if self.scaler:
            scaler_path = f"{models_dir}/scaler_{experiment_id}.pkl"
            joblib.dump(self.scaler, scaler_path)
            transformations['scaler_path'] = scaler_path
            logger.info(f"💾 Scaler sauvegardé: {scaler_path}")
        
        # Sauvegarder les encoders des features
        if self.label_encoders:
            encoders_path = f"{models_dir}/encoders_{experiment_id}.pkl"
            joblib.dump(self.label_encoders, encoders_path)
            transformations['encoders_path'] = encoders_path
            logger.info(f"💾 Encoders sauvegardés: {encoders_path}")
        
        # Sauvegarder l'encoder de la target
        if self.target_encoder:
            target_encoder_path = f"{models_dir}/target_encoder_{experiment_id}.pkl"
            joblib.dump(self.target_encoder, target_encoder_path)
            transformations['target_encoder_path'] = target_encoder_path
            transformations['target_classes'] = self.original_target_classes.tolist()
            logger.info(f"💾 Target encoder sauvegardé: {target_encoder_path}")
        
        # Sauvegarder la config JSON
        transformations_path = f"{models_dir}/transformations_{experiment_id}.json"
        with open(transformations_path, 'w') as f:
            json.dump(transformations, f, indent=2)
        
        logger.info(f"💾 Configuration des transformations: {transformations_path}")
        return transformations_path
    
    def create_model(self):
        """Crée le modèle selon l'algorithme choisi"""
        
        algorithm = self.config['algorithm']
        hyperparameters = self.config.get('hyperparameters', {})
        
        if algorithm == 'knn':
            from .algorithms.knn import KNNAlgorithm
            self.model = KNNAlgorithm.create_model(hyperparameters)
        elif algorithm == 'decision_tree':
            from .algorithms.decision_tree import DecisionTreeAlgorithm
            self.model = DecisionTreeAlgorithm.create_model(hyperparameters)
        elif algorithm == 'c45':
            from .algorithms.c45_tree import C45Algorithm
            self.model = C45Algorithm.create_model(hyperparameters)
        elif algorithm == 'chaid':
            from .algorithms.chaid_tree import CHAIDAlgorithm
            self.model = CHAIDAlgorithm.create_model(hyperparameters)
        elif algorithm == 'naive_bayes':
            from .algorithms.naive_bayes import NaiveBayesAlgorithm
            self.model = NaiveBayesAlgorithm.create_model(hyperparameters)
        elif algorithm == 'neural_network':
            from .algorithms.neural_network import NeuralNetworkAlgorithm
            self.model = NeuralNetworkAlgorithm.create_model(hyperparameters)
        elif algorithm == 'linear_regression':
            from .algorithms.linear_regression import LinearRegressionAlgorithm
            self.model = LinearRegressionAlgorithm.create_model(hyperparameters)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        logger.info(f"✅ Model created: {algorithm}")

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> float:
        """Entraîne le modèle et retourne le temps d'entraînement"""
        import time
        start_time = time.perf_counter()
        
        self.model.fit(X_train, y_train)
        
        end_time = time.perf_counter()
        training_time = end_time - start_time
        
        logger.info(f"✅ Training completed in {training_time:.4f}s")
        return training_time
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Évalue le modèle de classification et calcule les métriques"""
        
        # Prédictions
        y_pred = self.model.predict(X_test)
        
        # Accuracy
        accuracy = accuracy_score(y_test, y_pred)
        
        # Precision, Recall, F1-Score
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1)
        }
        
        # ROC/AUC (si classification binaire et modèle supporte predict_proba)
        roc_data = None
        if hasattr(self.model, 'predict_proba'):
            try:
                y_proba = self.model.predict_proba(X_test)
                unique_classes = np.unique(y_test)
                
                if len(unique_classes) == 2:
                    # Classification binaire
                    fpr, tpr, thresholds = roc_curve(y_test, y_proba[:, 1])
                    roc_auc = auc(fpr, tpr)
                    
                    # ✅ FIX : Convertir Infinity en None
                    thresholds_clean = []
                    for t in thresholds:
                        if np.isinf(t) or np.isnan(t):
                            thresholds_clean.append(None)
                        else:
                            thresholds_clean.append(float(t))
                    
                    roc_data = {
                        'fpr': fpr.tolist(),
                        'tpr': tpr.tolist(),
                        'thresholds': thresholds_clean,  # ✅ Version nettoyée
                        'auc': float(roc_auc)
                    }
                    
                    metrics['auc'] = float(roc_auc)
                    logger.info(f"📊 AUC: {roc_auc:.4f}")
            except Exception as e:
                logger.warning(f"Could not compute ROC/AUC: {str(e)}")
        self.metrics = metrics
        
        logger.info(f"📊 Classification Metrics: Accuracy={accuracy:.4f}, F1={f1:.4f}")
        
        return {
            'metrics': metrics,
            'confusion_matrix': cm.tolist(),
            'roc_data': roc_data
        }
    
    def evaluate_regression(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Évalue le modèle de régression et calcule les métriques"""
        
        # Prédictions
        y_pred = self.model.predict(X_test)
        
        # Métriques
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Résidus
        residuals = y_test - y_pred
        
        metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2_score': float(r2)
        }
        
        self.metrics = metrics
        
        logger.info(f"📊 Regression Metrics: MSE={mse:.4f}, RMSE={rmse:.4f}, R²={r2:.4f}")
        
        return {
            'metrics': metrics,
            'residuals': residuals.tolist(),
            'predictions': y_pred.tolist()
        }
    
    def save_model(self, experiment_id: int, project_id: int) -> str:
        """Sauvegarde le modèle entraîné"""
        
        # Créer le répertoire si nécessaire
        models_dir = f"/app/models/project_{project_id}"
        os.makedirs(models_dir, exist_ok=True)
        
        # Nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_{experiment_id}_{timestamp}.pkl"
        filepath = os.path.join(models_dir, filename)
        
        # Sauvegarder
        joblib.dump(self.model, filepath)
        
        logger.info(f"💾 Modèle sauvegardé: {filepath}")
        return filepath
    
    def run(self, experiment_id: int, project_id: int) -> Dict:
        """Pipeline complet d'entraînement avec sauvegarde des transformations"""
        
        try:
            # 1. Charger les données
            df = self.load_data()
            
            # 2. Préparer les données (avec encodage et normalisation)
            X_train, X_test, y_train, y_test = self.prepare_data(df)
            
            # 3. Créer le modèle
            self.create_model()
            
            # 4. Entraîner
            training_time = self.train(X_train, y_train)
            
            # 5. Évaluer (détecter classification vs régression)
            algorithm = self.config['algorithm']
            is_regression = algorithm in ['linear_regression']
            
            if is_regression:
                results = self.evaluate_regression(X_test, y_test)
            else:
                results = self.evaluate(X_test, y_test)
            
            # 6. Sauvegarder le modèle
            model_path = self.save_model(experiment_id, project_id)
            
            # 7. ✅ NOUVEAU : Sauvegarder les transformations
            transformations_path = self.save_transformations(experiment_id, project_id)
            
            return {
                'status': 'completed',
                'metrics': results['metrics'],
                'confusion_matrix': results.get('confusion_matrix'),
                'roc_data': results.get('roc_data'),
                'residuals': results.get('residuals'),
                'predictions': results.get('predictions'),
                'training_time': training_time,
                'model_path': model_path,
                'transformations_path': transformations_path  # ✅ NOUVEAU
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur entraînement: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'failed',
                'error_message': str(e)
            }