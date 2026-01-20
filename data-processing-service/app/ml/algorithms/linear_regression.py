from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from typing import Dict

class LinearRegressionAlgorithm:
    """Algorithme de régression linéaire (simple et multiple)"""
    
    @staticmethod
    def create_model(hyperparameters: Dict):
        """Crée un modèle de régression linéaire"""
        
        # Type de régression
        regression_type = hyperparameters.get('regression_type', 'linear')
        
        if regression_type == 'polynomial':
            # Régression polynomiale
            degree = hyperparameters.get('degree', 2)
            poly_features = PolynomialFeatures(degree=degree)
            model = LinearRegression(
                fit_intercept=hyperparameters.get('fit_intercept', True)
            )
            # Retourner un wrapper qui applique la transformation polynomiale
            return PolynomialRegressionWrapper(model, poly_features)
        else:
            # Régression linéaire simple/multiple
            model = LinearRegression(
                fit_intercept=hyperparameters.get('fit_intercept', True),
                n_jobs=hyperparameters.get('n_jobs', -1)
            )
            return model
    
    @staticmethod
    def get_default_params() -> Dict:
        return {
            'regression_type': 'linear',
            'fit_intercept': True,
            'degree': 2
        }
    
    @staticmethod
    def get_param_ranges() -> Dict:
        return {
            'regression_type': {
                'type': 'select',
                'options': ['linear', 'polynomial'],
                'default': 'linear',
                'description': 'Linear: simple/multiple regression, Polynomial: polynomial features'
            },
            'fit_intercept': {
                'type': 'boolean',
                'default': True,
                'description': 'Whether to calculate the intercept'
            },
            'degree': {
                'type': 'int',
                'min': 2,
                'max': 5,
                'default': 2,
                'description': 'Degree of polynomial features (only for polynomial regression)'
            }
        }


class PolynomialRegressionWrapper:
    """Wrapper pour régression polynomiale"""
    
    def __init__(self, model, poly_features):
        self.model = model
        self.poly_features = poly_features
        
    def fit(self, X, y):
        X_poly = self.poly_features.fit_transform(X)
        self.model.fit(X_poly, y)
        return self
    
    def predict(self, X):
        X_poly = self.poly_features.transform(X)
        return self.model.predict(X_poly)
    
    def score(self, X, y):
        X_poly = self.poly_features.transform(X)
        return self.model.score(X_poly, y)