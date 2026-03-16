# Vacancy Pipeline

## Stages

1. fetch vacancy payload from API, HTML, or Telegram source
2. persist raw payload with source metadata
3. normalize common fields
4. enrich salary, location, seniority, and skills
5. deduplicate against canonical catalog
6. publish `vacancy.catalog_updated.v1`
7. archive expired items by source TTL

## Key records

- `VacancySourceConfig`
- `RawVacancyPayload`
- `CanonicalVacancy`
- `DeduplicationCandidate`

These shared models live in `packages/common/vacancies.py`.

## Deduplication heuristics

- same `source_id` and `external_id`
- same `canonical_url`
- title + company similarity
- normalized text fingerprint similarity

## Operational rules

- each source has its own `ttl_hours`
- blocked vacancies do not re-enter recommendation batches
- manual admin moderation overrides automated status changes
