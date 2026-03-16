#!/bin/bash
set -e

echo "[notification-service] Waiting for PostgreSQL..."
until python3 -c "
import psycopg2, os, sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close(); sys.exit(0)
except Exception: sys.exit(1)
" 2>/dev/null; do
  echo "[notification-service] PostgreSQL not ready, retrying in 2s..."
  sleep 2
done

echo "[notification-service] Running Alembic migrations..."
alembic upgrade head

echo "[notification-service] Starting service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8008
