"""Tests de l'API Flask (client de test, sans Docker)."""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "api"))
os.environ.setdefault("ARTIFACTS_DIR", os.path.join(ROOT, "artifacts"))
from app import app  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok" and "model_version" in body


def test_metadata(client):
    body = client.get("/metadata").get_json()
    assert body["metadata"]["features"] == ["note", "absences", "participation"]
    assert "accuracy" in body["metrics"]


def test_predict_success(client):
    r = client.post("/predict", json={"note": 16, "absences": 1, "participation": 9})
    assert r.status_code == 200
    body = r.get_json()
    assert body["prediction"] == 1 and body["mode"] == "Modèle réel"
    assert 0 <= body["probability_success"] <= 1


def test_predict_failure_case(client):
    body = client.post("/predict", json={"note": 3, "absences": 25, "participation": 1}).get_json()
    assert body["prediction"] == 0


@pytest.mark.parametrize("payload,fragment", [
    ({"note": 14, "absences": 2}, "manquant"),
    ({"note": "abc", "absences": 2, "participation": 5}, "nombre"),
    ({"note": 25, "absences": 2, "participation": 5}, "entre 0 et 20"),
    ({"note": 14, "absences": -1, "participation": 5}, "entre 0 et 30"),
    ({"note": 14, "absences": 2, "participation": 11}, "entre 0 et 10"),
    ("pas un objet", "objet JSON"),
])
def test_predict_invalid(client, payload, fragment):
    r = client.post("/predict", json=payload)
    assert r.status_code == 400
    assert fragment in r.get_json()["error"]


def test_predict_requires_post(client):
    assert client.get("/predict").status_code == 405


def test_unknown_route(client):
    assert client.get("/inconnu").status_code == 404


def test_metrics_and_logs_updated(client):
    before = client.get("/metrics").get_json()["predictions"]
    client.post("/predict", json={"note": 12, "absences": 5, "participation": 6})
    after = client.get("/metrics").get_json()
    assert after["predictions"] == before + 1
    assert after["latency_ms_avg"] >= 0
    assert len(client.get("/logs").get_json()) >= 1


def test_rollback_loads_matching_metadata(monkeypatch):
    """MODEL_FILE=model_v1.joblib doit charger metadata_v1.json (version 1)."""
    import importlib, app as appmod
    monkeypatch.setenv("MODEL_FILE", "model_v1.joblib")
    m = importlib.reload(appmod)
    assert m.METADATA["version"] == 1 and m.METRICS["version"] == 1
    monkeypatch.setenv("MODEL_FILE", "model.joblib")
    importlib.reload(appmod)
