#!/bin/bash
set -e

echo "[bot-service] Starting..."

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "[bot-service] WARNING: TELEGRAM_BOT_TOKEN is not set. Bot will run in stub mode."
fi

exec uvicorn app.main:fastapi_app --host 0.0.0.0 --port 8009
