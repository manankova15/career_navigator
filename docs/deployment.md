# Deployment

## Environments

- `local`: podman compose and local service processes.
- `staging`: integration verification and contract testing.
- `production`: managed database, broker, object storage, and monitoring.

## Deployment sequence

1. Provision PostgreSQL, Redis, RabbitMQ, ClickHouse, and S3-compatible storage.
2. Apply schema migrations.
3. Deploy domain services.
4. Deploy `api-gateway` and `bot-service`.
5. Enable background workers.
6. Validate health endpoints and smoke tests.

## Backup and recovery

- Daily PostgreSQL backups.
- ClickHouse snapshot schedule for analytics.
- Object storage lifecycle policy for model artifacts.
- Recovery drills should validate `RTO <= 1 hour`.
