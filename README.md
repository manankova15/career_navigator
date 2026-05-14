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

Перед первым запуском: `podman machine init` и `podman machine start`.

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
