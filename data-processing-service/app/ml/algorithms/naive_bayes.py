from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from typing import Dict

class NaiveBayesAlgorithm:
    """Algorithme Naive Bayes"""
    
    @staticmethod
    def create_model(hyperparameters: Dict):
        """Crée un modèle Naive Bayes avec les hyperparamètres donnés"""
        
        # Type de Naive Bayes
        nb_type = hyperparameters.get('nb_type', 'gaussian')
        
        if nb_type == 'gaussian':
            # Pour features continues
            var_smoothing = hyperparameters.get('var_smoothing', 1e-9)
            model = GaussianNB(var_smoothing=var_smoothing)
            
        elif nb_type == 'multinomial':
            # Pour features discrètes/comptages
            alpha = hyperparameters.get('alpha', 1.0)
            model = MultinomialNB(alpha=alpha)
            
        elif nb_type == 'bernoulli':
            # Pour features binaires
            alpha = hyperparameters.get('alpha', 1.0)
            binarize = hyperparameters.get('binarize', 0.0)
            model = BernoulliNB(alpha=alpha, binarize=binarize)
        else:
            model = GaussianNB()
        
        return model
    
    @staticmethod
    def get_default_params() -> Dict:
        """Retourne les paramètres par défaut"""
        return {
            'nb_type': 'gaussian',
            'var_smoothing': 1e-9,
            'alpha': 1.0
        }
    
    @staticmethod
    def get_param_ranges() -> Dict:
        """Retourne les plages de valeurs possibles pour chaque paramètre"""
        return {
            'nb_type': {
                'type': 'select',
                'options': ['gaussian', 'multinomial', 'bernoulli'],
                'default': 'gaussian',
                'description': 'Gaussian: continuous features, Multinomial: discrete counts, Bernoulli: binary features'
            },
            'var_smoothing': {
                'type': 'float',
                'min': 1e-12,
                'max': 1e-6,
                'default': 1e-9,
                'description': 'Portion of the largest variance added to variances for stability (Gaussian only)'
            },
            'alpha': {
                'type': 'float',
                'min': 0.1,
                'max': 10.0,
                'default': 1.0,
                'description': 'Additive smoothing parameter (Multinomial & Bernoulli)'
            }
        }