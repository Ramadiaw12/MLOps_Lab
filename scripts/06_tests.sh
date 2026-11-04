#!/bin/bash
# Tests pytest dans un conteneur Python (aucune installation sur le Mac) :
#  1) unitaires + API   2) intégration contre la pile Docker (via host.docker.internal)
cd "$(dirname "$0")/.." && mkdir -p docs
docker run --rm -v "$PWD:/work" -w /work python:3.12-slim bash -c \
  "pip install -q -r requirements.txt >/dev/null 2>&1 && python -m pytest tests/test_training.py tests/test_api.py -v" 2>&1 | tee docs/tests_unit_api.log
echo "--- intégration (pile Docker démarrée, accès via host.docker.internal) ---"
docker run --rm -v "$PWD:/work" -w /work -e API_URL=http://host.docker.internal:5001 -e FRONT_URL=http://host.docker.internal:8501 python:3.12-slim bash -c \
  "pip install -q pytest >/dev/null 2>&1 && python -m pytest tests/test_integration.py -v" 2>&1 | tee docs/tests_integration.log
