#!/bin/bash
# Retour arrière vers une version précédente puis retour à la version active
# Usage : bash scripts/09_rollback.sh 1     (sert model_v1.joblib)
#         bash scripts/09_rollback.sh       (revient à model.joblib = version active)
cd "$(dirname "$0")/.." && mkdir -p docs
if [ -n "$1" ]; then export MODEL_FILE="model_v$1.joblib"; else export MODEL_FILE="model.joblib"; fi
echo "=== Service api avec MODEL_FILE=$MODEL_FILE ==="
docker compose up -d api
sleep 10
curl -s http://127.0.0.1:5001/health; echo
