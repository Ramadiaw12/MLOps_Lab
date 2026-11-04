"""Tests d'intégration : la pile Docker Compose doit être démarrée
(API via Nginx sur http://127.0.0.1:8501/api/ et directement sur http://127.0.0.1:5001).

Lancer :  docker compose up -d --build   puis   pytest tests/test_integration.py -v
Sautés automatiquement si les services ne répondent pas.
"""
import json
import os
import urllib.error
import urllib.request

import pytest

FRONT = os.environ.get("FRONT_URL", "http://127.0.0.1:8501")
API = os.environ.get("API_URL", "http://127.0.0.1:5001")


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read().decode()


def _post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _up(url):
    try:
        return _get(url)[0] == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _up(f"{API}/health"), reason="pile Docker non démarrée")


def test_api_health_direct():
    status, body = _get(f"{API}/health")
    assert status == 200 and json.loads(body)["status"] == "ok"


def test_frontend_served_by_nginx():
    status, html = _get(f"{FRONT}/")
    assert status == 200 and "<html" in html.lower() and "Student Success" in html


def test_nginx_proxies_api():
    status, body = _get(f"{FRONT}/api/health")
    assert status == 200 and json.loads(body)["status"] == "ok"


def test_predict_through_proxy():
    status, body = _post(f"{FRONT}/api/predict", {"note": 15, "absences": 2, "participation": 8})
    assert status == 200 and body["prediction"] in (0, 1) and body["mode"] == "Modèle réel"


def test_predict_invalid_through_proxy():
    status, body = _post(f"{FRONT}/api/predict", {"note": 99, "absences": 2, "participation": 8})
    assert status == 400 and "error" in body


def test_metrics_endpoint():
    status, body = _get(f"{FRONT}/api/metrics")
    assert status == 200 and "predictions" in json.loads(body)
