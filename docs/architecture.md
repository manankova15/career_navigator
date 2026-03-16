# Architecture

## Overview

Career Navigator uses a microservice-oriented architecture with explicit domain boundaries:

- `api-gateway` for web orchestration.
- domain services for auth, profile, vacancies, recommendations, assessments, analytics, notifications, and administration.
- `bot-service` for Telegram interaction.
- `ingestion-workers` for offline vacancy ingestion.
- shared infrastructure: PostgreSQL, Redis, RabbitMQ, ClickHouse, and S3-compatible storage.

## Service interaction

- Synchronous user-facing traffic flows through `api-gateway`.
- Telegram commands flow through `bot-service`.
- Background jobs and integration events are exchanged through RabbitMQ.
- Operational data lives in PostgreSQL.
- Product events are replicated into ClickHouse for analytics.

## Service boundaries

- `auth-service`: identity, tokens, sessions, RBAC.
- `profile-service`: user profile, preferences, skills, experience.
- `source-service`: source registry and sync configuration.
- `vacancy-service`: vacancy catalog, normalization outputs, deduplication results.
- `recommendation-service`: ranking orchestration and recommendation persistence.
- `ml-service`: models, feature extraction, inference.
- `assessment-service`: tests, attempts, answers, feedback.
- `analytics-service`: dashboards, analytics APIs, aggregations.
- `notification-service`: outbound email and Telegram messaging.
- `admin-service`: back-office moderation and audit access.

## Delivery principles

- Every service exposes `/health` and `/ready`.
- Events must be versioned.
- Admin actions must be audited.
- Secrets never live in source control.
