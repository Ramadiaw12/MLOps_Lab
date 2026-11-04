#!/bin/bash
# Vérifie l'API et le frontend ; écrit docs/check.txt
cd "$(dirname "$0")/.." && mkdir -p docs
{
echo "=== docker compose ps ==="; docker compose ps
echo; echo "=== GET /health (direct 5000) ==="; curl -s http://127.0.0.1:5001/health; echo
echo "=== GET /api/health (via Nginx 8501) ==="; curl -s http://127.0.0.1:8501/api/health; echo
echo "=== POST /api/predict ==="; curl -s -X POST http://127.0.0.1:8501/api/predict -H "Content-Type: application/json" -d '{"note": 14, "absences": 2, "participation": 8}'; echo
echo "=== POST /api/predict (invalide) ==="; curl -s -X POST http://127.0.0.1:8501/api/predict -H "Content-Type: application/json" -d '{"note": 25, "absences": 2, "participation": 8}'; echo
echo "=== GET / (frontend) ==="; curl -s -o /dev/null -w "HTTP %{http_code}, %{size_download} octets\n" http://127.0.0.1:8501/
echo "=== docker images ==="; docker images | grep -E "mlops|REPOSITORY"
} 2>&1 | tee docs/check.txt
