#!/usr/bin/env bash
set -euo pipefail

cp -n .env.example .env || true
echo "Bootstrap complete. Review .env before starting services."
