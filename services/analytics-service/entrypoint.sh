#!/bin/bash
set -e
echo "[analytics-service] Waiting for PostgreSQL..."
until python3 -c "import psycopg2,os,sys; conn=psycopg2.connect(os.environ['DATABASE_URL']); conn.close(); sys.exit(0)" 2>/dev/null; do
  echo "[analytics-service] retrying..."; sleep 2
done
echo "[analytics-service] Running migrations..."
alembic upgrade head
echo "[analytics-service] Starting..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8011
