from sklearn.neural_network import MLPClassifier
from typing import Dict

class NeuralNetworkAlgorithm:
    """Algorithme Neural Network (Multi-layer Perceptron)"""
    
    @staticmethod
    def create_model(hyperparameters: Dict):
        """Crée un modèle MLP avec les hyperparamètres donnés"""
        
        # Hidden layers configuration
        hidden_layers_str = hyperparameters.get('hidden_layers', '100')
        hidden_layer_sizes = tuple(map(int, hidden_layers_str.split(',')))
        
        activation = hyperparameters.get('activation', 'relu')
        learning_rate = hyperparameters.get('learning_rate', 'constant')
        learning_rate_init = hyperparameters.get('learning_rate_init', 0.001)
        max_iter = hyperparameters.get('max_iter', 200)
        alpha = hyperparameters.get('alpha', 0.0001)
        
        model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=activation,
            learning_rate=learning_rate,
            learning_rate_init=learning_rate_init,
            max_iter=max_iter,
            alpha=alpha,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
        
        return model
    
    @staticmethod
    def get_default_params() -> Dict:
        """Retourne les paramètres par défaut"""
        return {
            'hidden_layers': '100',
            'activation': 'relu',
            'learning_rate': 'constant',
            'learning_rate_init': 0.001,
            'max_iter': 200,
            'alpha': 0.0001
        }
    
    @staticmethod
    def get_param_ranges() -> Dict:
        """Retourne les plages de valeurs possibles pour chaque paramètre"""
        return {
            'hidden_layers': {
                'type': 'text',
                'default': '100',
                'description': 'Hidden layer sizes (comma-separated). Ex: "100" or "100,50" for 2 layers'
            },
            'activation': {
                'type': 'select',
                'options': ['relu', 'tanh', 'logistic'],
                'default': 'relu',
                'description': 'Activation function for hidden layers'
            },
            'learning_rate': {
                'type': 'select',
                'options': ['constant', 'adaptive'],
                'default': 'constant',
                'description': 'Learning rate schedule'
            },
            'learning_rate_init': {
                'type': 'float',
                'min': 0.0001,
                'max': 0.1,
                'default': 0.001,
                'description': 'Initial learning rate'
            },
            'max_iter': {
                'type': 'int',
                'min': 50,
                'max': 1000,
                'default': 200,
                'description': 'Maximum number of iterations'
            },
            'alpha': {
                'type': 'float',
                'min': 0.00001,
                'max': 0.01,
                'default': 0.0001,
                'description': 'L2 penalty (regularization) parameter'
            }
        }