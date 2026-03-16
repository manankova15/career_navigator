# Recommendations

## Phase 1

- content-based matching between profile skills and vacancy skills
- rule-based ranking over seniority, location, salary fit, and work format
- skill-gap extraction from repeated vacancy requirements

## Phase 2

- collaborative filtering on user events
- hybrid ranker combining content, behavior, and assessment outcomes
- explainability layer with human-readable reasons
- weekly retraining and offline evaluation

## Shared models

- `SkillGap`
- `VacancyRecommendation`
- `ModelMetrics`

These shared models live in `packages/common/recommendations.py`.

## Data dependencies

- `profile-service`: profile and skills
- `vacancy-service`: canonical vacancies and extracted skills
- `assessment-service`: scores and weak skills
- `analytics-service`: interaction metrics and CTR
