from sklearn.neighbors import KNeighborsClassifier
from typing import Dict

class KNNAlgorithm:
    """Algorithme K-Nearest Neighbors"""
    
    @staticmethod
    def create_model(hyperparameters: Dict):
        """Crée un modèle KNN avec les hyperparamètres donnés"""
        
        # Valeurs par défaut
        n_neighbors = hyperparameters.get('n_neighbors', 5)
        weights = hyperparameters.get('weights', 'uniform')
        metric = hyperparameters.get('metric', 'euclidean')
        
        # Créer le modèle
        model = KNeighborsClassifier(
            n_neighbors=n_neighbors,
            weights=weights,
            metric=metric
        )
        
        return model
    
    @staticmethod
    def get_default_params() -> Dict:
        """Retourne les paramètres par défaut"""
        return {
            'n_neighbors': 5,
            'weights': 'uniform',
            'metric': 'euclidean'
        }
    
    @staticmethod
    def get_param_ranges() -> Dict:
        """Retourne les plages de valeurs possibles pour chaque paramètre"""
        return {
            'n_neighbors': {'type': 'int', 'min': 1, 'max': 20, 'default': 5},
            'weights': {'type': 'select', 'options': ['uniform', 'distance'], 'default': 'uniform'},
            'metric': {'type': 'select', 'options': ['euclidean', 'manhattan'], 'default': 'euclidean'}
        }