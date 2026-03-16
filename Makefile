PYTHON ?= python3
COMPOSE ?= podman compose

.PHONY: help install dev-up dev-down dev-logs dev-build \
        auth-up vacancy-up migrate \
        lint format test typecheck \
        frontend-dev frontend-build \
        clean

help:
	@echo "Career Navigator — Podman targets"
	@echo ""
	@echo "  make dev-up          Start all infrastructure + services"
	@echo "  make dev-down        Stop and remove containers"
	@echo "  make dev-build       Rebuild all service images"
	@echo "  make dev-logs        Follow logs for all services"
	@echo "  make dev-logs s=auth-service   Follow logs for one service"
	@echo ""
	@echo "  make infra-up        Start only infrastructure (postgres, redis, etc.)"
	@echo "  make infra-down      Stop infrastructure"
	@echo ""
	@echo "  make lint            Compile-check all Python files"
	@echo "  make format          Run ruff formatter"
	@echo "  make test            Run unit tests"
	@echo "  make typecheck       TypeScript check in frontend/"
	@echo ""
	@echo "  make bootstrap       Copy .env.example → .env if missing"
	@echo "  make clean           Remove __pycache__ and .pyc files"

# ── Bootstrap ────────────────────────────────────────────────────────────────

bootstrap:
	@bash scripts/bootstrap.sh

# ── Container orchestration ──────────────────────────────────────────────────

dev-up: bootstrap
	$(COMPOSE) up -d

dev-down:
	$(COMPOSE) down

dev-build: bootstrap
	$(COMPOSE) build

dev-logs:
ifdef s
	$(COMPOSE) logs -f $(s)
else
	$(COMPOSE) logs -f
endif

dev-restart:
ifdef s
	$(COMPOSE) restart $(s)
else
	$(COMPOSE) restart
endif

# Start only infrastructure services (postgres, redis, rabbitmq, clickhouse, minio)
infra-up: bootstrap
	$(COMPOSE) up -d postgres redis rabbitmq clickhouse minio

infra-down:
	$(COMPOSE) stop postgres redis rabbitmq clickhouse minio

# ── Database migrations (run inside service containers) ──────────────────────

migrate-auth:
	$(COMPOSE) exec auth-service alembic upgrade head

migrate-profile:
	$(COMPOSE) exec profile-service alembic upgrade head

migrate-source:
	$(COMPOSE) exec source-service alembic upgrade head

migrate-vacancy:
	$(COMPOSE) exec vacancy-service alembic upgrade head

migrate-recommendation:
	$(COMPOSE) exec recommendation-service alembic upgrade head

migrate-all: migrate-auth migrate-profile migrate-source migrate-vacancy migrate-recommendation

# ── Code quality ─────────────────────────────────────────────────────────────

install:
	$(PYTHON) -m pip install -e .

lint:
	$(PYTHON) -m compileall packages services workers

format:
	$(PYTHON) -m ruff format packages services workers || true
	$(PYTHON) -m ruff check --fix packages services workers || true

test:
	$(PYTHON) -m unittest discover -s services -p "test_*.py"

# ── Frontend ─────────────────────────────────────────────────────────────────

frontend-dev:
	cd frontend && npm install && npm run dev

frontend-build:
	cd frontend && npm install && npm run build

typecheck:
	cd frontend && npm run typecheck

# ── Utilities ────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
