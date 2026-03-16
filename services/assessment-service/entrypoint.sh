#!/bin/bash
set -e

echo "[assessment-service] Waiting for PostgreSQL..."
until python3 -c "
import psycopg2, os, sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close(); sys.exit(0)
except Exception: sys.exit(1)
" 2>/dev/null; do
  echo "[assessment-service] PostgreSQL not ready, retrying in 2s..."
  sleep 2
done

echo "[assessment-service] Running Alembic migrations..."
alembic upgrade head

echo "[assessment-service] Starting service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8007
