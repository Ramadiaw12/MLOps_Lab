"""Génère le notebook Colab `mlops_lab_student_success.ipynb` (exécuté ensuite localement)."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code = lambda s: cells.append(nbf.v4.new_code_cell(s))

md("""# 🎓 MLOps Lab — Student Success
**ENSET Mohammedia — Université Hassan II de Casablanca — Prof. Azeddine KHIAT**

Ce notebook est la **phase d'expérimentation** du laboratoire MLOps : nous allons créer des données, entraîner un modèle de
Machine Learning, l'évaluer, puis **exporter des artefacts** (modèle, métriques, métadonnées) qui seront ensuite
déployés dans une API Flask conteneurisée avec Docker.

> ⚠️ **Avertissement pédagogique** : le dataset est 100 % synthétique et le modèle est une démonstration.
> Il ne doit **jamais** servir à prendre une décision académique réelle sur un étudiant.

## Objectifs
1. Générer un dataset synthétique (`note`, `absences`, `participation` → `reussite`).
2. Explorer et visualiser les données.
3. Prétraiter et séparer entraînement / test.
4. Entraîner une **régression logistique** (classification binaire).
5. Évaluer : accuracy, précision, rappel, F1, matrice de confusion.
6. Exporter `model.joblib`, `metrics.json`, `metadata.json` et les télécharger.
""")

md("## 1. Installation et versions des dépendances\nLes graines aléatoires fixes et les versions documentées garantissent la **reproductibilité**.")
code("""!pip -q install "scikit-learn>=1.4" "pandas>=2.0" joblib matplotlib 2>/dev/null
import sys, platform, numpy as np, pandas as pd, sklearn, joblib, matplotlib
print("Python      :", platform.python_version())
print("numpy       :", np.__version__)
print("pandas      :", pd.__version__)
print("scikit-learn:", sklearn.__version__)
print("joblib      :", joblib.__version__)
SEED = 42""")

md("""## 2. Génération du dataset synthétique
Chaque étudiant fictif reçoit une **note** (sur 20), un nombre d'**absences** et un score de **participation** (sur 10).
La réussite est tirée au sort à partir d'un score latent : la note pèse le plus, les absences pénalisent, la participation aide.
C'est exactement la logique qu'un modèle devra *redécouvrir* à partir des données.""")
code("""def generate(n=1000, seed=SEED, drift=0.0):
    rng = np.random.default_rng(seed)
    note = np.clip(rng.normal(11.5 + drift, 3.2, n), 0, 20).round(1)
    absences = np.clip(rng.poisson(5 + 2 * drift, n), 0, 30)
    participation = np.clip(rng.normal(6 + drift, 2.0, n), 0, 10).round(1)
    score = 0.55 * (note - 10) - 0.18 * (absences - 5) + 0.35 * (participation - 5)
    proba = 1 / (1 + np.exp(-score))
    reussite = (rng.random(n) < proba).astype(int)
    return pd.DataFrame({"note": note, "absences": absences,
                         "participation": participation, "reussite": reussite})

df = generate()
df.to_csv("students_v1.csv", index=False)
print(df.shape)
df.head(10)""")

md("## 3. Exploration des données\n`describe()` donne les statistiques ; `value_counts()` la répartition des classes.")
code("""display(df.describe().round(2))
print("Répartition de la cible :")
print(df["reussite"].value_counts(normalize=True).round(3))""")

md("## 4. Visualisations\nHistogrammes par classe : plus les distributions sont séparées, plus la variable est informative.")
code("""import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))
for ax, col in zip(axes, ["note", "absences", "participation"]):
    ax.hist(df[df.reussite == 1][col], bins=20, alpha=.6, label="Réussite (1)", color="#16a34a")
    ax.hist(df[df.reussite == 0][col], bins=20, alpha=.6, label="Échec (0)", color="#dc2626")
    ax.set_title(col); ax.legend()
plt.tight_layout(); plt.savefig("distributions_v1.png", dpi=130); plt.show()""")

md("""## 5. Prétraitement
- **Features** (X) = `note`, `absences`, `participation`  **Target** (y) = `reussite`.
- Les variables ont des échelles différentes (0-20, 0-30, 0-10) → on les **standardise** avec `StandardScaler`.
- Le scaler est placé **dans un Pipeline** : il sera sauvegardé avec le modèle et appliqué automatiquement à l'inférence (pas de fuite ni d'oubli).""")
code("""from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

FEATURES = ["note", "absences", "participation"]; TARGET = "reussite"
X, y = df[FEATURES], df[TARGET]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
print("Entraînement :", X_train.shape, " Test :", X_test.shape)""")

md("## 6. Entraînement\nLa régression logistique est un modèle **simple et explicable** : chaque variable reçoit un poids.")
code("""model = Pipeline([("scaler", StandardScaler()),
                  ("clf", LogisticRegression(max_iter=1000, random_state=SEED))])
model.fit(X_train, y_train)
coefs = dict(zip(FEATURES, model.named_steps["clf"].coef_[0].round(3).tolist()))
print("Poids appris :", coefs)""")

md("## 7. Prédictions\nLe modèle n'a **jamais vu** les données de test : c'est le seul moyen honnête de mesurer sa qualité.")
code("""y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]
pd.DataFrame({"note": X_test.note.values[:8], "absences": X_test.absences.values[:8],
              "participation": X_test.participation.values[:8],
              "réel": y_test.values[:8], "prédit": y_pred[:8], "proba_réussite": y_proba[:8].round(3)})""")

md("""## 8. Évaluation
| Métrique | Question à laquelle elle répond |
|---|---|
| **Accuracy** | Quelle proportion de prédictions est correcte ? |
| **Précision** | Parmi les étudiants prédits « réussite », combien réussissent vraiment ? |
| **Rappel** | Parmi les étudiants qui réussissent vraiment, combien le modèle a-t-il détectés ? |
| **F1** | Moyenne harmonique précision / rappel |""")
code("""from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import json
metrics = {
  "version": 1, "model_type": "logreg",
  "accuracy": round(accuracy_score(y_test, y_pred), 4),
  "precision": round(precision_score(y_test, y_pred), 4),
  "recall": round(recall_score(y_test, y_pred), 4),
  "f1": round(f1_score(y_test, y_pred), 4),
  "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
  "n_train": int(len(X_train)), "n_test": int(len(X_test)),
}
print(json.dumps(metrics, indent=2))""")

md("## 9. Matrice de confusion\nLignes = réalité, colonnes = prédiction. La diagonale = bonnes réponses.")
code("""cm = np.array(metrics["confusion_matrix"])
fig, ax = plt.subplots(figsize=(4.5, 4))
ax.imshow(cm, cmap="Blues")
for (i, j), v in np.ndenumerate(cm):
    ax.text(j, i, v, ha="center", va="center", fontsize=16, color="white" if v > cm.max()/2 else "black")
ax.set_xticks([0,1]); ax.set_xticklabels(["Prédit 0", "Prédit 1"])
ax.set_yticks([0,1]); ax.set_yticklabels(["Réel 0", "Réel 1"])
ax.set_title("Matrice de confusion — v1"); plt.tight_layout()
plt.savefig("confusion_matrix_v1.png", dpi=150); plt.show()""")

md("""## 10. Interprétation
- Une accuracy autour de **0,75-0,80** est attendue : les étiquettes sont volontairement bruitées (tirage aléatoire).
- Le poids de `note` est le plus fort et positif, celui d'`absences` est négatif : le modèle a retrouvé la logique de génération.
- Les **faux positifs** (réel 0, prédit 1) sont les cas les plus coûteux pédagogiquement : un étudiant en difficulté non détecté.""")

md("## 11. Export des artefacts\nTrois fichiers constituent **une version** du modèle : le modèle, ses métriques et ses métadonnées.")
code("""from datetime import datetime, timezone
metadata = {
  "model_name": "student-success", "version": 1, "model_type": "logreg",
  "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
  "features": FEATURES, "target": TARGET,
  "feature_ranges": {"note": [0, 20], "absences": [0, 30], "participation": [0, 10]},
  "dataset": {"file": "students_v1.csv", "rows": int(len(df)), "drift": 0.0, "seed": SEED},
  "split": {"test_size": 0.2, "random_state": SEED, "stratify": True},
  "libraries": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                "pandas": pd.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
  "disclaimer": "Modèle de démonstration pédagogique — ne pas utiliser pour des décisions académiques réelles."
}
joblib.dump(model, "model.joblib")
json.dump(metrics, open("metrics.json", "w"), indent=2)
json.dump(metadata, open("metadata.json", "w"), indent=2, ensure_ascii=False)
import os; print([f for f in os.listdir(".") if f.endswith((".joblib", ".json", ".csv", ".png"))])""")

md("## 12. Vérification : rechargement du modèle\nUn artefact n'est utile que s'il se **recharge** et donne les mêmes prédictions.")
code("""reloaded = joblib.load("model.joblib")
exemple = pd.DataFrame([{"note": 14.0, "absences": 2, "participation": 8.0}])
print("Prédiction :", int(reloaded.predict(exemple)[0]), " Probabilité de réussite :", round(float(reloaded.predict_proba(exemple)[0,1]), 3))
assert (reloaded.predict(X_test) == y_pred).all(), "Les prédictions diffèrent après rechargement !"
print("✅ Rechargement cohérent")""")

md("## 13. Téléchargement des artefacts (Colab → Mac)\nDans Colab, cette cellule déclenche le téléchargement du zip dans votre dossier *Téléchargements*.")
code("""import zipfile
ARTEFACTS = ["model.joblib", "metrics.json", "metadata.json", "students_v1.csv",
             "confusion_matrix_v1.png", "distributions_v1.png"]
with zipfile.ZipFile("artifacts_v1.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in ARTEFACTS:
        z.write(f)
print("Archive créée :", ARTEFACTS)
try:
    from google.colab import files
    files.download("artifacts_v1.zip")
except ImportError:
    print("Hors Colab : artifacts_v1.zip créé dans le dossier courant.")""")

md("""## 14. Exercices corrigés
**Exercice 1.** Modifiez `test_size` à 0,3. Que devient `n_test` ? *Corrigé : 300 lignes de test, 700 d'entraînement.*

**Exercice 2.** Remplacez `LogisticRegression` par `RandomForestClassifier(n_estimators=200, random_state=42)`. L'accuracy change-t-elle ?
*Corrigé : légèrement (±0,02) ; les étiquettes étant bruitées, aucun modèle ne dépassera ~0,85.*

**Exercice 3.** Que se passe-t-il si l'on retire `StandardScaler` du pipeline ?
*Corrigé : la régression logistique converge quand même ici, mais les poids ne sont plus comparables entre variables.*

**Exercice 4.** Pourquoi `stratify=y` ? *Corrigé : pour garder la même proportion de 0/1 dans train et test.*

**Exercice 5.** Générez un dataset avec `drift=0.6` et évaluez le modèle v1 dessus : c'est la **dérive des données** (module 19).""")

nb["cells"] = cells
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}, "colab": {"name": "mlops_lab_student_success.ipynb"}}
nbf.write(nb, "colab/mlops_lab_student_success.ipynb")
print("Notebook écrit :", len(cells), "cellules")
