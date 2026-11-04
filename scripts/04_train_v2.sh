#!/bin/bash
# Réentraîne une v2 (dérive + forêt aléatoire) DANS un conteneur Python (pas besoin de Python sur le Mac)
cd "$(dirname "$0")/.." && mkdir -p docs
docker run --rm -v "$PWD:/work" -w /work python:3.12-slim bash -c "pip install -q -r api/requirements.txt matplotlib >/dev/null 2>&1 && python training/train.py --version 2 --drift 0.6 --n 1500 --model rf" 2>&1 | tee docs/train_v2.log
