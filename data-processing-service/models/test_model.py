import joblib
import numpy as np

# Charger le NOUVEAU modèle (expérience 25)
model = joblib.load('./project_4/model_25_20260107_121505.pkl')

print("=" * 60)
print("TEST DU MODÈLE - Expérience 25")
print("=" * 60)

# Test 1 : Très sain
print("\n🟢 Test 1 : Profil TRÈS SAIN")
data_healthy = np.array([[0, 70, 60, 20, 80, 20.0, 0.1, 22]])
pred = model.predict(data_healthy)
proba = model.predict_proba(data_healthy)
print(f"Prédiction: {pred[0]} ({'Non diabétique' if pred[0] == 0 else 'Diabétique'})")
print(f"Probabilités: Classe 0 = {proba[0][0]:.2%}, Classe 1 = {proba[0][1]:.2%}")

# Test 2 : Diabétique
print("\n🔴 Test 2 : Profil DIABÉTIQUE")
data_diabetic = np.array([[6, 148, 72, 35, 0, 33.6, 0.627, 50]])
pred = model.predict(data_diabetic)
proba = model.predict_proba(data_diabetic)
print(f"Prédiction: {pred[0]} ({'Non diabétique' if pred[0] == 0 else 'Diabétique'})")
print(f"Probabilités: Classe 0 = {proba[0][0]:.2%}, Classe 1 = {proba[0][1]:.2%}")

# Test 3 : Moyen
print("\n🟡 Test 3 : Profil MOYEN")
data_medium = np.array([[1, 89, 66, 23, 94, 23.1, 0.167, 28]])
pred = model.predict(data_medium)
proba = model.predict_proba(data_medium)
print(f"Prédiction: {pred[0]} ({'Non diabétique' if pred[0] == 0 else 'Diabétique'})")
print(f"Probabilités: Classe 0 = {proba[0][0]:.2%}, Classe 1 = {proba[0][1]:.2%}")

# Test 4 : Extrêmement sain
print("\n💚 Test 4 : Profil EXTRÊMEMENT SAIN")
data_super_healthy = np.array([[0, 65, 55, 15, 70, 19.5, 0.08, 20]])
pred = model.predict(data_super_healthy)
proba = model.predict_proba(data_super_healthy)
print(f"Prédiction: {pred[0]} ({'Non diabétique' if pred[0] == 0 else 'Diabétique'})")
print(f"Probabilités: Classe 0 = {proba[0][0]:.2%}, Classe 1 = {proba[0][1]:.2%}")

print("\n" + "=" * 60)
print("Informations du modèle:")
print(f"Type: {type(model).__name__}")
if hasattr(model, 'n_classes_'):
    print(f"Nombre de classes: {model.n_classes_}")
    print(f"Classes: {model.classes_}")
if hasattr(model, 'n_features_in_'):
    print(f"Nombre de features: {model.n_features_in_}")
print("=" * 60)