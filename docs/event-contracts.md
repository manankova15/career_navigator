# Event Contracts

## Principles

- Events are immutable.
- Event names are namespaced by domain.
- Every event includes `event_id`, `event_type`, `event_version`, `occurred_at`, and `trace_id`.

## Core events

- `identity.user_registered.v1`
- `identity.telegram_linked.v1`
- `profile.profile_updated.v1`
- `vacancy.source_sync_requested.v1`
- `vacancy.source_sync_completed.v1`
- `vacancy.canonicalized.v1`
- `vacancy.catalog_updated.v1`
- `recommendation.batch_generated.v1`
- `assessment.attempt_submitted.v1`
- `assessment.feedback_generated.v1`
- `notification.dispatch_requested.v1`
- `notification.dispatch_completed.v1`
- `admin.entity_moderated.v1`

## Routing guidance

- source sync events are consumed by `ingestion-workers`.
- vacancy catalog events trigger recommendation refresh.
- assessment events feed analytics and skill-gap recalculation.
- notification events are emitted after recommendation or admin workflows.
