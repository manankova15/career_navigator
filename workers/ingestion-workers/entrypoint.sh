#!/bin/bash
set -e

echo "[ingestion-worker] Waiting for PostgreSQL..."
until python3 -c "
import psycopg2, os, sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close(); sys.exit(0)
except Exception: sys.exit(1)
" 2>/dev/null; do
  echo "[ingestion-worker] PostgreSQL not ready, retrying in 2s..."
  sleep 2
done

echo "[ingestion-worker] Waiting for Redis..."
until python3 -c "
import redis, os, sys
try:
    r = redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379/0'))
    r.ping(); sys.exit(0)
except Exception: sys.exit(1)
" 2>/dev/null; do
  echo "[ingestion-worker] Redis not ready, retrying in 2s..."
  sleep 2
done

echo "[ingestion-worker] Starting Celery worker + beat..."
exec celery -A app.celery_app worker --beat --loglevel=info --concurrency=2
