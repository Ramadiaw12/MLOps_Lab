"""API Flask « Student Success » — sert le modèle scikit-learn exporté par le notebook.

Routes :
  GET  /health   → état de l'API et version du modèle chargé
  GET  /metadata → métadonnées + métriques du modèle actif
  GET  /metrics  → compteurs de monitoring (requêtes, erreurs, latence)
  POST /predict  → {"note": 14, "absences": 2, "participation": 8} → prédiction
  GET  /logs     → 50 dernières prédictions (monitoring pédagogique)
  GET  /versions → toutes les versions de modèle disponibles (v1, v2…)
"""
import json
import logging
import os
import time
from collections import deque
from datetime import datetime, timezone

import joblib
import pandas as pd
from flask import Flask, jsonify, request

ART_DIR = os.environ.get("ARTIFACTS_DIR", os.path.join(os.path.dirname(__file__), "..", "artifacts"))
MODEL_FILE = os.environ.get("MODEL_FILE", "model.joblib")

# ---------- Logs structurés (JSON, une ligne par événement) ----------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                   "level": record.levelname, "msg": record.getMessage()}
        if hasattr(record, "extra"):
            payload.update(record.extra)
        return json.dumps(payload, ensure_ascii=False)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
log = logging.getLogger("student-success-api")
log.setLevel(logging.INFO)
log.handlers = [handler]
log.propagate = False

# ---------- Chargement du modèle ----------
def load_artifacts():
    """Charge le modèle et SES métadonnées/métriques.
    MODEL_FILE=model_v1.joblib → metadata_v1.json + metrics_v1.json (retour arrière cohérent) ;
    MODEL_FILE=model.joblib (défaut) → metadata.json + metrics.json (version active)."""
    model = joblib.load(os.path.join(ART_DIR, MODEL_FILE))
    suffix = MODEL_FILE[len("model"):-len(".joblib")]          # "" ou "_v1", "_v2"…
    with open(os.path.join(ART_DIR, f"metadata{suffix}.json"), encoding="utf-8") as f:
        metadata = json.load(f)
    with open(os.path.join(ART_DIR, f"metrics{suffix}.json"), encoding="utf-8") as f:
        metrics = json.load(f)
    return model, metadata, metrics

MODEL, METADATA, METRICS = load_artifacts()
FEATURES = METADATA["features"]
RANGES = METADATA["feature_ranges"]
log.info("model loaded", extra={"extra": {"version": METADATA["version"], "model_type": METADATA["model_type"]}})

# ---------- Monitoring en mémoire ----------
STATS = {"requests": 0, "predictions": 0, "errors": 0, "latency_ms_sum": 0.0, "latency_ms_max": 0.0,
         "class_counts": {"0": 0, "1": 0}, "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
HISTORY = deque(maxlen=50)

app = Flask(__name__)


def validate(payload):
    """Retourne (dict_valide, None) ou (None, message_erreur)."""
    if not isinstance(payload, dict):
        return None, "Le corps de la requête doit être un objet JSON."
    clean = {}
    for f in FEATURES:
        if f not in payload:
            return None, f"Champ manquant : '{f}'."
        v = payload[f]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            try:
                v = float(v)
            except (TypeError, ValueError):
                return None, f"Le champ '{f}' doit être un nombre (reçu : {payload[f]!r})."
        lo, hi = RANGES[f]
        if not (lo <= v <= hi):
            return None, f"Le champ '{f}' doit être compris entre {lo} et {hi} (reçu : {v})."
        clean[f] = float(v)
    return clean, None


@app.get("/health")
def health():
    STATS["requests"] += 1
    return jsonify({"status": "ok", "model_version": METADATA["version"],
                    "model_type": METADATA["model_type"], "time": datetime.now(timezone.utc).isoformat(timespec="seconds")})


@app.get("/metadata")
def metadata():
    STATS["requests"] += 1
    return jsonify({"metadata": METADATA, "metrics": METRICS})


@app.get("/metrics")
def metrics():
    STATS["requests"] += 1
    n = max(STATS["predictions"], 1)
    return jsonify({**STATS, "latency_ms_avg": round(STATS["latency_ms_sum"] / n, 2),
                    "model_version": METADATA["version"]})


@app.get("/versions")
def versions():
    """Liste toutes les versions de modèle disponibles dans artifacts/ (metrics_v*.json)."""
    STATS["requests"] += 1
    out = []
    for name in sorted(os.listdir(ART_DIR)):
        if name.startswith("metrics_v") and name.endswith(".json"):
            with open(os.path.join(ART_DIR, name), encoding="utf-8") as f:
                m = json.load(f)
            meta_file = os.path.join(ART_DIR, name.replace("metrics", "metadata"))
            meta = json.load(open(meta_file, encoding="utf-8")) if os.path.exists(meta_file) else {}
            out.append({"metrics": m, "metadata": meta, "active": m.get("version") == METADATA["version"]})
    return jsonify(out)


@app.get("/logs")
def logs():
    STATS["requests"] += 1
    return jsonify(list(HISTORY))


@app.post("/predict")
def predict():
    STATS["requests"] += 1
    t0 = time.perf_counter()
    payload = request.get_json(silent=True)
    clean, err = validate(payload)
    if err:
        STATS["errors"] += 1
        log.warning("invalid input", extra={"extra": {"error": err, "payload": payload}})
        return jsonify({"error": err}), 400

    X = pd.DataFrame([clean], columns=FEATURES)
    pred = int(MODEL.predict(X)[0])
    proba = float(MODEL.predict_proba(X)[0][1])
    latency = (time.perf_counter() - t0) * 1000

    STATS["predictions"] += 1
    STATS["latency_ms_sum"] += latency
    STATS["latency_ms_max"] = max(STATS["latency_ms_max"], latency)
    STATS["class_counts"][str(pred)] += 1

    result = {"input": clean, "prediction": pred,
              "label": "Réussite probable" if pred == 1 else "Risque d'échec",
              "probability_success": round(proba, 4), "model_version": METADATA["version"],
              "model_type": METADATA["model_type"], "latency_ms": round(latency, 2),
              "mode": "Modèle réel",
              "disclaimer": METADATA.get("disclaimer")}
    HISTORY.appendleft({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **result})
    log.info("prediction", extra={"extra": {"input": clean, "prediction": pred,
                                            "proba": round(proba, 4), "latency_ms": round(latency, 2)}})
    return jsonify(result)


@app.errorhandler(404)
def not_found(_):
    STATS["errors"] += 1
    return jsonify({"error": "Route inconnue. Routes : /health, /metadata, /metrics, /logs, POST /predict"}), 404


@app.errorhandler(405)
def bad_method(_):
    STATS["errors"] += 1
    return jsonify({"error": "Méthode non autorisée (ex. : /predict attend un POST)."}), 405


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
