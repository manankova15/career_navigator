# Career Navigator

Веб‑платформа для карьерной навигации: профиль и навыки, вакансии, рекомендации и анализ «пробелов» по навыкам, оценки, уведомления, админка; часть сценариев можно вести через Telegram‑бота.

## Из чего состоит репозиторий

- `frontend/` — основной React‑клиент (Vite).
- `admin-frontend/` — панель администратора.
- `services/` — backend‑сервисы (auth, profile, источники вакансий, вакансии, ML, рекомендации, API‑шлюз, оценки, аналитика, уведомления, админ‑API, бот).
- `workers/ingestion-workers/` — фоновая загрузка и обработка вакансий.
- `packages/common/`, `packages/events/` — общий Python‑код и контракты событий.
- `infra/` — манифесты инфраструктуры.
- `docs/` — архитектура и описание API.

## Что нужно для запуска

- [Podman](https://podman.io/) 4.1+ с поддержкой `podman compose` **или** Docker Compose — в `Makefile` по умолчанию `COMPOSE ?= podman compose`; при Docker: `make COMPOSE="docker compose" dev-up`.
- Python 3.12+ и Node.js 20+ — для локальных скриптов, тестов и фронтенда вне контейнеров.

На macOS с Podman перед первым запуском: `podman machine init` и `podman machine start`.

## Быстрый старт

```bash
make bootstrap          # копирует .env из .env.example, если .env ещё нет
# при необходимости отредактируйте .env (секреты, SMTP, Telegram и т.д.)

make dev-build
make dev-up
make dev-logs           # опционально: логи всех сервисов
```

После подъёма контейнеров:

- пользовательский UI: http://localhost:3000  
- админка: http://localhost:3001  
- API через шлюз (Swagger): http://localhost:8000/docs  

Отдельные сервисы (для отладки): `auth-service` — 8001, `profile-service` — 8002, `source-service` — 8003, `vacancy-service` — 8004, `recommendation-service` — 8005, `ml-service` — 8006, `assessment-service` — 8007, `notification-service` — 8008, `bot-service` — 8009, `admin-service` — 8010, `analytics-service` — 8011. Инфраструктура: PostgreSQL 5432, Redis 6379, RabbitMQ (в т.ч. UI 15672), ClickHouse 8123, MinIO (консоль 9001).

Миграции БД: `make migrate-all`.

Только инфраструктура: `make infra-up` / `make infra-down`.

## Фронтенд без Docker

На `http://localhost:8000` должен отвечать `api-gateway` (проще всего - уже поднятый стек: `make dev-up`).

```bash
make frontend-dev     # из корня: npm install && npm run dev в frontend/
```
