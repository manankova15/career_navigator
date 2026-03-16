# Operations

## Admin responsibilities

- moderate vacancies and assessments
- manage source schedules
- review audit logs
- trigger manual resynchronization

## Observability baseline

- service health and readiness endpoints
- Prometheus scraping
- structured logs with trace IDs
- queue backlog monitoring
- sync failure alerts

## CI/CD baseline

- GitHub Actions compile and typecheck jobs
- environment-based deployments after passing checks
- migration step before public traffic cutover

## Backup and recovery

- daily PostgreSQL backup
- analytics snapshot policy
- object storage backup for exported artifacts
- documented recovery drill with target `RTO <= 1 hour`
