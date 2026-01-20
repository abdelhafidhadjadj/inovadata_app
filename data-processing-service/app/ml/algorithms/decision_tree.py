from sklearn.tree import DecisionTreeClassifier
from typing import Dict

class DecisionTreeAlgorithm:
    """Algorithme Decision Tree CART (Classification and Regression Trees)"""
    
    @staticmethod
    def create_model(hyperparameters: Dict):
        """Crée un modèle CART avec les hyperparamètres donnés"""
        
        # Paramètres
        max_depth = hyperparameters.get('max_depth', None)
        min_samples_split = hyperparameters.get('min_samples_split', 2)
        min_samples_leaf = hyperparameters.get('min_samples_leaf', 1)
        criterion = hyperparameters.get('criterion', 'gini')
        
        # CART avec Gini ou Entropy
        model = DecisionTreeClassifier(
            criterion=criterion,
            max_depth=max_depth if max_depth and max_depth > 0 else None,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
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
            'criterion': 'gini'
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
            'criterion': {
                'type': 'select',
                'options': ['gini', 'entropy'],
                'default': 'gini',
                'description': 'Function to measure split quality: Gini impurity or Information Gain'
            }
        }