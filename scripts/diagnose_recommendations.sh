#!/usr/bin/env bash
# Diagnose why GET /recommendations/me returns an empty feed
# ("Рекомендации пока не готовы").
#
# Run from the repo root after `docker compose up` (or podman compose up).
# All container names default to the docker-compose service names;
# override via the env variables at the top if you renamed something.

set -euo pipefail

PG_VACANCY_CONTAINER="${PG_VACANCY_CONTAINER:-postgres-vacancy}"
PG_VACANCY_USER="${PG_VACANCY_USER:-postgres}"
PG_VACANCY_DB="${PG_VACANCY_DB:-vacancy_db}"

PG_REC_CONTAINER="${PG_REC_CONTAINER:-postgres-recommendation}"
PG_REC_USER="${PG_REC_USER:-postgres}"
PG_REC_DB="${PG_REC_DB:-recommendation_db}"

REC_SERVICE_CONTAINER="${REC_SERVICE_CONTAINER:-recommendation-service}"
ML_SERVICE_CONTAINER="${ML_SERVICE_CONTAINER:-ml-service}"
VAC_SERVICE_CONTAINER="${VAC_SERVICE_CONTAINER:-vacancy-service}"

# Auto-pick the container runtime: prefer docker, fall back to podman.
if [[ -z "${DOCKER:-}" ]]; then
    if command -v docker >/dev/null 2>&1; then
        DOCKER="docker"
    elif command -v podman >/dev/null 2>&1; then
        DOCKER="podman"
    else
        echo "Neither 'docker' nor 'podman' found in PATH. Set DOCKER=... before running." >&2
        exit 1
    fi
fi
echo "Using container runtime: $DOCKER"

heading() {
    printf '\n\033[1;36m=== %s ===\033[0m\n' "$*"
}

heading "1. How many ACTIVE canonical vacancies exist (status='active')?"
$DOCKER exec -i "$PG_VACANCY_CONTAINER" \
    psql -U "$PG_VACANCY_USER" -d "$PG_VACANCY_DB" -c "
        SELECT status, count(*) FROM canonical_vacancies GROUP BY status ORDER BY status;
    "

heading "2. Breakdown of active vacancies by source (channel name) — to spot TG-only situation"
$DOCKER exec -i "$PG_VACANCY_CONTAINER" \
    psql -U "$PG_VACANCY_USER" -d "$PG_VACANCY_DB" -c "
        SELECT s.name AS source, count(*) AS n_active
          FROM canonical_vacancies v
          LEFT JOIN sources s ON s.id = v.source_id
         WHERE v.status = 'active'
         GROUP BY s.name
         ORDER BY n_active DESC;
    " || true

heading "3. Are any active vacancies expired by expires_at?"
$DOCKER exec -i "$PG_VACANCY_CONTAINER" \
    psql -U "$PG_VACANCY_USER" -d "$PG_VACANCY_DB" -c "
        SELECT count(*) FILTER (WHERE expires_at IS NULL)        AS no_expiry,
               count(*) FILTER (WHERE expires_at > now())         AS not_yet_expired,
               count(*) FILTER (WHERE expires_at <= now())        AS already_expired
          FROM canonical_vacancies WHERE status = 'active';
    "

heading "4. Last 5 ACTIVE TG titles (post-cleanup verification)"
$DOCKER exec -i "$PG_VACANCY_CONTAINER" \
    psql -U "$PG_VACANCY_USER" -d "$PG_VACANCY_DB" -c "
        SELECT title FROM canonical_vacancies
         WHERE status='active' AND canonical_url LIKE 'https://t.me/%'
         ORDER BY created_at DESC LIMIT 5;
    " || true

heading "5. Latest recommendation sessions per user (last 5 rows)"
$DOCKER exec -i "$PG_REC_CONTAINER" \
    psql -U "$PG_REC_USER" -d "$PG_REC_DB" -c "
        SELECT user_id, algorithm, total_scored, created_at
          FROM recommendation_sessions
          ORDER BY created_at DESC LIMIT 5;
    "

heading "6. How many recommendations attached to the latest session?"
$DOCKER exec -i "$PG_REC_CONTAINER" \
    psql -U "$PG_REC_USER" -d "$PG_REC_DB" -c "
        WITH s AS (
            SELECT id FROM recommendation_sessions
            ORDER BY created_at DESC LIMIT 1
        )
        SELECT count(*) AS rec_rows FROM vacancy_recommendations
         WHERE session_id = (SELECT id FROM s);
    "

heading "7. Recent recommendation-service logs (last 80 lines, errors highlighted)"
$DOCKER logs --tail 80 "$REC_SERVICE_CONTAINER" 2>&1 | \
    grep -E "ERROR|WARNING|recommendation|Failed|502|empty|fetch_candidate" -i || true

heading "8. Recent ml-service logs (last 40 lines)"
$DOCKER logs --tail 40 "$ML_SERVICE_CONTAINER" 2>&1 | tail -n 40 || true

heading "9. Recent vacancy-service logs (last 40 lines)"
$DOCKER logs --tail 40 "$VAC_SERVICE_CONTAINER" 2>&1 | tail -n 40 || true

echo
echo "If section #1 shows zero active vacancies, OR section #2 shows TG count zero,"
echo "OR section #6 returns 0 — recommendations are empty because the candidate pool is empty."
echo "If sections #7-9 contain HTTP 502 / Connection refused / timeouts — that is the root cause."
