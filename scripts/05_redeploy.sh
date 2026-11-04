#!/bin/bash
cd "$(dirname "$0")/.." && mkdir -p docs
docker compose up -d --build api 2>&1 | tee docs/redeploy.log
sleep 12; echo "--- /health ---"; curl -s http://127.0.0.1:5001/health; echo; curl -s http://127.0.0.1:5001/versions | head -c 600; echo
