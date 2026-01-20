from typing import Dict
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    from CHAID import Tree as CHAIDTree
    CHAID_AVAILABLE = True
except ImportError:
    CHAID_AVAILABLE = False
    logger.warning("CHAID library not installed. Install with: pip install CHAID")


class CHAIDWrapper:
    """Wrapper pour CHAID qui imite l'API sklearn"""
    
    def __init__(self, max_depth=5, min_samples_split=30, min_samples_leaf=10, alpha_merge=0.05):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.alpha_merge = alpha_merge
        self.tree = None
        self.feature_names = None
        self.classes_ = None
        
    def fit(self, X, y):
        """Entraîner le modèle CHAID"""
        if not CHAID_AVAILABLE:
            raise ImportError("CHAID library not installed. Please run: pip install CHAID")
        
        # Convertir en DataFrame pour CHAID
        if not isinstance(X, pd.DataFrame):
            self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            X_df = pd.DataFrame(X, columns=self.feature_names)
        else:
            X_df = X.copy()
            self.feature_names = X.columns.tolist()
        
        # Ajouter la target
        X_df['target'] = y
        
        # Classes uniques
        self.classes_ = np.unique(y)
        
        # Déterminer les types de variables (toutes en nominal pour simplifier)
        variable_types = {col: 'nominal' for col in self.feature_names}
        
        # Créer l'arbre CHAID
        self.tree = CHAIDTree.from_pandas_df(
            X_df,
            variable_types,
            'target',
            max_depth=self.max_depth,
            min_parent_node_size=self.min_samples_split,
            min_child_node_size=self.min_samples_leaf,
            alpha_merge=self.alpha_merge
        )
        
        logger.info(f"CHAID tree created with depth {self.max_depth}")
        return self
    
    def predict(self, X):
        """Prédire avec le modèle CHAID"""
        if self.tree is None:
            raise ValueError("Model not fitted yet")
        
        if not isinstance(X, pd.DataFrame):
            X_df = pd.DataFrame(X, columns=self.feature_names)
        else:
            X_df = X.copy()
        
        predictions = []
        for _, row in X_df.iterrows():
            # Convertir la ligne en dictionnaire
            row_dict = row.to_dict()
            try:
                pred = self.tree.node_predictions(row_dict)
                predictions.append(pred)
            except Exception as e:
                logger.warning(f"Prediction error for row, using majority class: {e}")
                # En cas d'erreur, utiliser la classe majoritaire
                predictions.append(self.classes_[0])
        
        return np.array(predictions)
    
    def predict_proba(self, X):
        """Prédire les probabilités"""
        predictions = self.predict(X)
        n_samples = len(predictions)
        n_classes = len(self.classes_)
        
        proba = np.zeros((n_samples, n_classes))
        for i, pred in enumerate(predictions):
            class_idx = np.where(self.classes_ == pred)[0]
            if len(class_idx) > 0:
                proba[i, class_idx[0]] = 1.0
            else:
                # Si classe inconnue, probabilité uniforme
                proba[i, :] = 1.0 / n_classes
        
        return proba


class CHAIDAlgorithm:
    """Algorithme CHAID (Chi-squared Automatic Interaction Detection)"""
    
    @staticmethod
    def create_model(hyperparameters: Dict):
        """Crée un modèle CHAID"""
        
        if not CHAID_AVAILABLE:
            from sklearn.tree import DecisionTreeClassifier
            logger.warning("CHAID library not available. Using Decision Tree approximation with Gini criterion")
            
            # Fallback vers Decision Tree avec paramètres adaptés pour simuler CHAID
            max_depth = hyperparameters.get('max_depth', 5)
            min_samples_split = hyperparameters.get('min_samples_split', 30)
            min_samples_leaf = hyperparameters.get('min_samples_leaf', 10)
            
            model = DecisionTreeClassifier(
                criterion='gini',
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                random_state=42
            )
            return model
        
        # Paramètres CHAID
        max_depth = hyperparameters.get('max_depth', 5)
        min_samples_split = hyperparameters.get('min_samples_split', 30)
        min_samples_leaf = hyperparameters.get('min_samples_leaf', 10)
        alpha_merge = hyperparameters.get('alpha_merge', 0.05)
        
        model = CHAIDWrapper(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            alpha_merge=alpha_merge
        )
        
        return model
    
    @staticmethod
    def get_default_params() -> Dict:
        return {
            'max_depth': 5,
            'min_samples_split': 30,
            'min_samples_leaf': 10,
            'alpha_merge': 0.05
        }
    
    @staticmethod
    def get_param_ranges() -> Dict:
        return {
            'max_depth': {
                'type': 'int',
                'min': 2,
                'max': 20,
                'default': 5,
                'description': 'Maximum depth of the CHAID tree'
            },
            'min_samples_split': {
                'type': 'int',
                'min': 20,
                'max': 100,
                'default': 30,
                'description': 'Minimum samples required to split a node (CHAID typically needs more samples)'
            },
            'min_samples_leaf': {
                'type': 'int',
                'min': 5,
                'max': 50,
                'default': 10,
                'description': 'Minimum samples required in a leaf node'
            },
            'alpha_merge': {
                'type': 'float',
                'min': 0.01,
                'max': 0.1,
                'default': 0.05,
                'description': 'Significance level for Chi-square test (merging categories)'
            }
        }