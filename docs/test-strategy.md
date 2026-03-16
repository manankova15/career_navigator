# Test Strategy

## Test layers

- unit tests for domain logic and scoring.
- contract tests for inter-service payloads.
- integration tests for database, broker, and cache flows.
- smoke tests for each service health endpoint.
- end-to-end tests for web and Telegram critical paths.

## Priority scenarios

- registration and login
- Telegram identity linking
- profile update and skill management
- source sync and vacancy normalization
- recommendation batch generation
- assessment submission and feedback
- notification delivery
- admin moderation and audit logging
