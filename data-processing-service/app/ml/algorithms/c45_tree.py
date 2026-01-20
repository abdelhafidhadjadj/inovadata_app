from sklearn.tree import DecisionTreeClassifier
from typing import Dict

class C45Algorithm:
    """Algorithme C4.5 Decision Tree (utilise le critère d'entropie)"""
    
    @staticmethod
    def create_model(hyperparameters: Dict):
        """Crée un modèle C4.5 avec les hyperparamètres donnés"""
        
        # Paramètres
        max_depth = hyperparameters.get('max_depth', None)
        min_samples_split = hyperparameters.get('min_samples_split', 2)
        min_samples_leaf = hyperparameters.get('min_samples_leaf', 1)
        min_impurity_decrease = hyperparameters.get('min_impurity_decrease', 0.0)
        
        # C4.5 utilise le critère d'entropie (Information Gain)
        model = DecisionTreeClassifier(
            criterion='entropy',  # C4.5 utilise l'entropie
            max_depth=max_depth if max_depth and max_depth > 0 else None,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            min_impurity_decrease=min_impurity_decrease,
            splitter='best',
            random_state=42
        )
        
        return model
    
    @staticmethod
    def get_default_params() -> Dict:
        """Retourne les paramètres par défaut"""
        return {
            'max_depth': 5,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'min_impurity_decrease': 0.0
        }
    
    @staticmethod
    def get_param_ranges() -> Dict:
        """Retourne les plages de valeurs possibles pour chaque paramètre"""
        return {
            'max_depth': {
                'type': 'int',
                'min': 1,
                'max': 50,
                'default': 5,
                'description': 'Maximum depth of the tree (leave empty for unlimited)'
            },
            'min_samples_split': {
                'type': 'int',
                'min': 2,
                'max': 20,
                'default': 2,
                'description': 'Minimum number of samples required to split an internal node'
            },
            'min_samples_leaf': {
                'type': 'int',
                'min': 1,
                'max': 20,
                'default': 1,
                'description': 'Minimum number of samples required to be at a leaf node'
            },
            'min_impurity_decrease': {
                'type': 'float',
                'min': 0.0,
                'max': 0.5,
                'default': 0.0,
                'description': 'A node will split if this split induces a decrease of impurity >= this value'
            }
        }