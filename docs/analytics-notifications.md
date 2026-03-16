# Analytics And Notifications

## Primary product metrics

- `daily_active_users`
- `recommendation_ctr`
- `vacancy_freshness`
- `assessment_completion`
- `profile_completion_rate`
- `notification_delivery_success_rate`

## ClickHouse sinks

- user vacancy interaction events
- assessment submission events
- notification delivery events
- source synchronization events

## Shared models

- `MetricDefinition`
- `NotificationDelivery`

These shared models live in `packages/common/analytics.py`.

## Notification channels

- email digests
- Telegram instant updates

## Delivery rules

- recommendations trigger digest or instant dispatch
- assessment feedback can trigger Telegram summaries
- failed deliveries are retained for retry and analytics
