#!/bin/bash
# Test arrêt puis redémarrage de la pile (module 24) — écrit docs/restart_test.txt
cd "$(dirname "$0")/.." && mkdir -p docs
{
echo "=== 1. Arrêt : docker compose down ==="; docker compose down
echo; echo "=== 2. Après arrêt (doit échouer) ==="; curl -s --max-time 3 http://127.0.0.1:8501/api/health || echo "→ API injoignable : attendu"
echo; echo "=== 3. Redémarrage : docker compose up -d (sans rebuild) ==="; docker compose up -d
echo; echo "=== 4. Attente healthcheck ==="; sleep 12; docker compose ps
echo; echo "=== 5. Après redémarrage ==="; curl -s http://127.0.0.1:8501/api/health; echo
curl -s -X POST http://127.0.0.1:8501/api/predict -H "Content-Type: application/json" -d '{"note": 14, "absences": 2, "participation": 8}'; echo
} 2>&1 | tee docs/restart_test.txt
