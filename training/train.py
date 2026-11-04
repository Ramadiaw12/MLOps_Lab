"""Entraînement du modèle « Student Success » (v1 ou v2).

Produit dans artifacts/ :
  - model_v<N>.joblib        : pipeline scikit-learn (StandardScaler + LogisticRegression)
  - metrics_v<N>.json        : accuracy, precision, recall, f1, matrice de confusion
  - metadata_v<N>.json       : version, date, graine, versions des bibliothèques, features
  - confusion_matrix_v<N>.png, feature_importance_v<N>.png
  - model.joblib / metrics.json / metadata.json : copie de la version « active »

Usage : python training/train.py --version 1
        python training/train.py --version 2 --drift 0.6 --n 1500 --model rf
"""
import argparse
import json
import os
import platform
import shutil
from datetime import datetime, timezone

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from generate_dataset import generate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
ART = os.path.join(ROOT, "artifacts")
DATA = os.path.join(ROOT, "data")
FEATURES = ["note", "absences", "participation"]
TARGET = "reussite"
SEED = 42


def build_model(kind: str):
    if kind == "rf":
        clf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=SEED)
    else:
        clf = LogisticRegression(max_iter=1000, random_state=SEED)
    return Pipeline([("scaler", StandardScaler()), ("clf", clf)])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--version", type=int, default=1)
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--drift", type=float, default=0.0)
    p.add_argument("--model", choices=["logreg", "rf"], default="logreg")
    p.add_argument("--set-active", action="store_true", default=True)
    a = p.parse_args()

    os.makedirs(ART, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)

    # 1. Données
    df = generate(a.n, SEED + a.version - 1, a.drift)
    csv = os.path.join(DATA, f"students_v{a.version}.csv")
    df.to_csv(csv, index=False)
    X, y = df[FEATURES], df[TARGET]

    # 2. Séparation train/test (stratifiée, graine fixe → reproductible)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)

    # 3. Entraînement
    model = build_model(a.model)
    model.fit(X_train, y_train)

    # 4. Évaluation
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    metrics = {
        "version": a.version,
        "model_type": a.model,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred)), 4),
        "recall": round(float(recall_score(y_test, y_pred)), 4),
        "f1": round(float(f1_score(y_test, y_pred)), 4),
        "confusion_matrix": cm.tolist(),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }

    # 5. Métadonnées
    metadata = {
        "model_name": "student-success",
        "version": a.version,
        "model_type": a.model,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "features": FEATURES,
        "target": TARGET,
        "feature_ranges": {"note": [0, 20], "absences": [0, 30], "participation": [0, 10]},
        "dataset": {"file": os.path.basename(csv), "rows": int(len(df)), "drift": a.drift,
                    "seed": SEED + a.version - 1},
        "split": {"test_size": 0.2, "random_state": SEED, "stratify": True},
        "libraries": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                      "pandas": pd.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
        "disclaimer": "Modèle de démonstration pédagogique — ne pas utiliser pour des décisions académiques réelles.",
    }

    # 6. Figures
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, str(v), ha="center", va="center", fontsize=16,
                color="white" if v > cm.max() / 2 else "black")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Prédit 0 (échec)", "Prédit 1 (réussite)"])
    ax.set_yticklabels(["Réel 0", "Réel 1"])
    ax.set_title(f"Matrice de confusion — modèle v{a.version}")
    fig.tight_layout(); fig.savefig(os.path.join(ART, f"confusion_matrix_v{a.version}.png"), dpi=150)
    plt.close(fig)

    clf = model.named_steps["clf"]
    imp = clf.coef_[0] if hasattr(clf, "coef_") else clf.feature_importances_
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.barh(FEATURES, imp, color=["#2563eb", "#dc2626", "#16a34a"])
    ax.set_title("Poids des variables" if hasattr(clf, "coef_") else "Importance des variables")
    ax.axvline(0, color="#999", lw=0.8)
    fig.tight_layout(); fig.savefig(os.path.join(ART, f"feature_importance_v{a.version}.png"), dpi=150)
    plt.close(fig)

    # 7. Export
    joblib.dump(model, os.path.join(ART, f"model_v{a.version}.joblib"))
    with open(os.path.join(ART, f"metrics_v{a.version}.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    with open(os.path.join(ART, f"metadata_v{a.version}.json"), "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    if a.set_active:
        for name in ("model", "metrics", "metadata"):
            ext = "joblib" if name == "model" else "json"
            shutil.copy(os.path.join(ART, f"{name}_v{a.version}.{ext}"),
                        os.path.join(ART, f"{name}.{ext}"))

    print(json.dumps(metrics, indent=2))
    print(f"✅ Artefacts v{a.version} écrits dans {ART}")


if __name__ == "__main__":
    main()
