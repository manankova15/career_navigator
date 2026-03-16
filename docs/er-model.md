# ER Model

## Identity and profile

- `users`
- `user_identities`
- `roles`
- `user_roles`
- `sessions`
- `refresh_tokens`
- `profiles`
- `profile_preferences`
- `skills`
- `profile_skills`
- `work_experiences`
- `educations`

## Vacancy domain

- `vacancy_sources`
- `source_sync_jobs`
- `raw_vacancies`
- `vacancies`
- `vacancy_versions`
- `vacancy_skills`
- `vacancy_duplicates`
- `user_vacancy_events`

## Recommendation and learning

- `recommendation_batches`
- `recommendations`
- `skill_gaps`
- `career_paths`
- `courses`
- `course_skill_links`
- `assessments`
- `assessment_items`
- `assessment_attempts`
- `assessment_answers`
- `assessment_feedback`

## Operations

- `notifications`
- `notification_deliveries`
- `admin_audit_logs`
- `system_events`

## Key relationships

- one `user` has one active `profile`.
- one `user` can have many `user_identities`.
- one `profile` can map to many `skills` through `profile_skills`.
- one `vacancy_source` can produce many `raw_vacancies`.
- one `raw_vacancy` resolves to one canonical `vacancy`.
- one `vacancy` can map to many skills and many user events.
- one `assessment` contains many `assessment_items`.
- one `assessment_attempt` belongs to one user and one assessment.
