"""Tests unitaires : dataset, reproductibilité, absence de fuite, rechargement du modèle."""
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "training"))
from generate_dataset import generate  # noqa: E402

ART = os.path.join(ROOT, "artifacts")
FEATURES = ["note", "absences", "participation"]


def test_dataset_shape_and_ranges():
    df = generate(500, seed=1)
    assert df.shape == (500, 4)
    assert df.note.between(0, 20).all()
    assert df.absences.between(0, 30).all()
    assert df.participation.between(0, 10).all()
    assert set(df.reussite.unique()) <= {0, 1}


def test_dataset_reproducible():
    a, b = generate(300, seed=7), generate(300, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_dataset_drift_changes_distribution():
    base, drifted = generate(2000, seed=3), generate(2000, seed=3, drift=0.8)
    assert drifted.note.mean() > base.note.mean()


def test_no_data_leakage_in_split():
    from sklearn.model_selection import train_test_split
    df = generate(400, seed=5)
    X_tr, X_te, _, _ = train_test_split(df[FEATURES], df.reussite, test_size=0.2, random_state=42)
    assert set(X_tr.index).isdisjoint(set(X_te.index))


def test_artifacts_exist():
    for f in ("model.joblib", "metrics.json", "metadata.json"):
        assert os.path.exists(os.path.join(ART, f)), f"artefact manquant : {f}"


def test_metrics_are_consistent():
    m = json.load(open(os.path.join(ART, "metrics.json")))
    cm = np.array(m["confusion_matrix"])
    assert cm.sum() == m["n_test"]
    assert abs(np.trace(cm) / cm.sum() - m["accuracy"]) < 1e-3
    assert 0.5 <= m["accuracy"] <= 1.0


def test_model_reload_and_predict():
    model = joblib.load(os.path.join(ART, "model.joblib"))
    X = pd.DataFrame([{"note": 18, "absences": 0, "participation": 9},
                      {"note": 4, "absences": 20, "participation": 1}], columns=FEATURES)
    preds = model.predict(X)
    assert preds[0] == 1 and preds[1] == 0
    proba = model.predict_proba(X)[:, 1]
    assert proba[0] > 0.8 and proba[1] < 0.2


def test_predictions_deterministic():
    model = joblib.load(os.path.join(ART, "model.joblib"))
    X = generate(50, seed=9)[FEATURES]
    assert (model.predict(X) == model.predict(X)).all()
