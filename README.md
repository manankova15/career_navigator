# Career Navigator

Career Navigator is an HR service for personalized career navigation. The project combines vacancy aggregation, recommendation pipelines, interview preparation, analytics, and a Telegram interface in one platform.

## Repository layout

- `frontend/` — React web client.
- `services/` — user-facing and domain microservices.
- `workers/` — ingestion and background pipelines.
- `packages/common/` — shared Python primitives.
- `packages/events/` — event schemas and message contracts.
- `infra/` — local infrastructure manifests.
- `docs/` — architecture, security, data, and API documentation.

## Core capabilities

- Email and Telegram-based identity flows.
- Career profile and skill inventory.
- Vacancy ingestion, normalization, deduplication, and archival.
- Personal recommendations and skill-gap analysis.
- Interview assessments and progress tracking.
- Notifications and analytics.
- Administrative tooling and audit trail.

## Requirements

- [Podman](https://podman.io/) 4.1+ (with `podman compose` support)
- [podman-compose](https://github.com/containers/podman-compose) — install via `pip install podman-compose`
- Python 3.12+
- Node.js 20+

> **macOS:** initialise the Podman VM before first use:
> ```bash
> podman machine init
> podman machine start
> ```

## Quick start

```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env and set real secrets (JWT_SECRET, passwords, etc.)

# 2. Build and start all services
make dev-build
make dev-up

# 3. Follow logs
make dev-logs
```

After startup the following ports are exposed:

| Service | URL |
|---|---|
| auth-service | http://localhost:8001/docs |
| profile-service | http://localhost:8002/docs |
| source-service | http://localhost:8003/docs |
| vacancy-service | http://localhost:8004/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| RabbitMQ UI | http://localhost:15672 |
| MinIO console | http://localhost:9001 |

## Infrastructure only (no service images)

```bash
make infra-up          # starts postgres, redis, rabbitmq, clickhouse, minio
make infra-down        # stops infrastructure
```

## Useful make targets

```bash
make dev-build         # rebuild all service images
make dev-up            # start all containers in background
make dev-down          # stop and remove containers
make dev-logs          # follow all logs
make dev-logs s=auth-service   # follow one service
make migrate-all       # run alembic migrations in all services
make lint              # Python syntax check
make typecheck         # TypeScript check
make clean             # remove __pycache__ / .pyc
```

## Local development standards

- Never commit `.env` files or tokens.
- Keep service contracts in `docs/api-spec/`.
- Use structured logs and health endpoints in every service.
- Prefer backward-compatible event changes.

## Services

| Service | Port | Description |
|---|---|---|
| `api-gateway` | 8000 | BFF / reverse proxy (planned) |
| `auth-service` | 8001 | Registration, login, JWT, RBAC |
| `profile-service` | 8002 | Career profile, skills, experience |
| `source-service` | 8003 | Vacancy source configs |
| `vacancy-service` | 8004 | Canonical vacancies, FTS search |
| `recommendation-service` | 8005 | Personalised recommendations (planned) |
| `ml-service` | 8006 | Skill-gap analysis, ML models (planned) |
| `assessment-service` | 8007 | Quizzes and interview tasks (planned) |
| `analytics-service` | 8008 | Metrics and ClickHouse sinks (planned) |
| `notification-service` | 8009 | Email and Telegram delivery (planned) |
| `admin-service` | 8010 | Admin panel and audit log (planned) |
| `bot-service` | — | Telegram bot via aiogram (planned) |
| `ingestion-workers` | — | Celery fetch/normalize/dedup pipeline |
