#!/bin/bash
# Construit les images et démarre la pile (api + frontend)
cd "$(dirname "$0")/.." && mkdir -p docs
docker compose up -d --build 2>&1 | tee docs/build.log
echo "--- docker compose ps ---"; docker compose ps | tee -a docs/build.log
