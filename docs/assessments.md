# Assessments

## Supported task modes

- `quiz`
- `multi-select`
- `short-text`
- `case`

`code-task` remains future scope until an isolated execution environment is introduced.

## Shared models

- `AssessmentItem`
- `AssessmentAttemptRecord`
- `AssessmentFeedbackRecord`

These shared models live in `packages/common/assessments.py`.

## Feedback rules

- objective modes return deterministic scoring
- short-text and case modes return rubric-driven notes
- every attempt stores weak skills for later skill-gap recalculation
- recommendation-service may attach follow-up materials based on weak skills
