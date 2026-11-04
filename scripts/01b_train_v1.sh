#!/bin/bash
# (Ré)entraîne la version 1 (régression logistique) dans un conteneur Python.
# Produit exactement les mêmes résultats que le notebook Colab (graine 42),
# avec les versions de bibliothèques de l'image Docker (aucune incompatibilité).
cd "$(dirname "$0")/.." && mkdir -p docs
docker run --rm -v "$PWD:/work" -w /work python:3.12-slim bash -c \
  "pip install -q -r api/requirements.txt matplotlib >/dev/null 2>&1 && python training/train.py --version 1" 2>&1 | tee docs/train_v1.log
