#!/bin/bash
cd "$(dirname "$0")/.." && mkdir -p docs
docker run --rm -v "$PWD:/work" -w /work -e API_URL=http://host.docker.internal:5001 -e FRONT_URL=http://host.docker.internal:8501 python:3.12-slim bash -c \
  "pip install -q pytest >/dev/null 2>&1 && python -m pytest tests/test_integration.py -v" 2>&1 | tee docs/tests_integration.log
