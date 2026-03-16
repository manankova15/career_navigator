#!/bin/bash
set -e
echo "[api-gateway] Starting..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
