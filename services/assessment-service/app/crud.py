"""
CRUD operations for assessment-service.
All write operations go through the auto-check engine on attempt submission.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .checker import (
    CheckResult,
    build_recommended_materials,
    build_summary,
    build_weak_skills,
    check_answer,
)
from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentFeedback,
    AssessmentItem,
)
from .schemas import AssessmentCreate, AssessmentItemCreate, AssessmentUpdate, AnswerIn


# ── Assessments ───────────────────────────────────────────────────────────────

def create_assessment(db: Session, payload: AssessmentCreate) -> Assessment:
    assessment = Assessment(
        title=payload.title,
        description=payload.description,
        topic=payload.topic,
        difficulty=payload.difficulty,
        related_skills=payload.related_skills,
        is_published=payload.is_published,
    )
    db.add(assessment)
    db.flush()

    for pos, item_data in enumerate(payload.items):
        _add_item(db, assessment.id, item_data, position=item_data.position or pos)

    db.commit()
    db.refresh(assessment)
    return assessment


def _add_item(
    db: Session,
    assessment_id: UUID,
    item_data: AssessmentItemCreate,
    position: int,
) -> AssessmentItem:
    item = AssessmentItem(
        assessment_id=assessment_id,
        position=position,
        prompt=item_data.prompt,
        mode=item_data.mode,
        options=[o.model_dump() for o in item_data.options],
        correct_option_ids=item_data.correct_option_ids,
        expected_keywords=item_data.expected_keywords,
        rubric_checklist=[r.model_dump() for r in item_data.rubric_checklist],
        max_score=item_data.max_score,
        related_skills=item_data.related_skills,
        explanation=item_data.explanation,
    )
    db.add(item)
    return item


def add_item_to_assessment(
    db: Session,
    assessment_id: UUID,
    item_data: AssessmentItemCreate,
) -> AssessmentItem:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        return None  # type: ignore[return-value]
    position = item_data.position or len(assessment.items)
    item = _add_item(db, assessment_id, item_data, position)
    db.commit()
    db.refresh(item)
    return item


def get_assessment(db: Session, assessment_id: UUID) -> Assessment | None:
    return db.query(Assessment).filter(Assessment.id == assessment_id).first()


def list_assessments(
    db: Session,
    *,
    topic: str | None = None,
    difficulty: str | None = None,
    published_only: bool = True,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Assessment], int]:
    q = db.query(Assessment)
    if published_only:
        q = q.filter(Assessment.is_published.is_(True))
    if topic:
        q = q.filter(Assessment.topic.ilike(f"%{topic}%"))
    if difficulty:
        q = q.filter(Assessment.difficulty == difficulty)
    total = q.count()
    items = q.order_by(Assessment.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def update_assessment(
    db: Session, assessment_id: UUID, payload: AssessmentUpdate
) -> Assessment | None:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        return None
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(assessment, field, value)
    assessment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assessment)
    return assessment


def delete_assessment(db: Session, assessment_id: UUID) -> bool:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        return False
    db.delete(assessment)
    db.commit()
    return True


# ── Attempts ──────────────────────────────────────────────────────────────────

def start_attempt(db: Session, user_id: UUID, assessment: Assessment) -> AssessmentAttempt:
    """Create an in-progress attempt so the user can save and resume later."""
    attempt = AssessmentAttempt(
        user_id=user_id,
        assessment_id=assessment.id,
        status="in_progress",
        progress_answers=[],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def save_attempt_progress(
    db: Session,
    attempt_id: UUID,
    user_id: UUID,
    progress_answers: list[dict],
) -> AssessmentAttempt | None:
    """Save partial answers for an in-progress attempt."""
    attempt = get_attempt(db, attempt_id)
    if not attempt or attempt.user_id != user_id or attempt.status != "in_progress":
        return None
    attempt.progress_answers = progress_answers
    db.commit()
    db.refresh(attempt)
    return attempt


def get_in_progress_attempt(
    db: Session, user_id: UUID, assessment_id: UUID
) -> AssessmentAttempt | None:
    return (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.assessment_id == assessment_id,
            AssessmentAttempt.status == "in_progress",
        )
        .order_by(AssessmentAttempt.created_at.desc())
        .first()
    )


def submit_attempt(
    db: Session,
    user_id: UUID,
    assessment: Assessment,
    answers_in: list[AnswerIn],
    existing_attempt: AssessmentAttempt | None = None,
) -> AssessmentAttempt:
    """
    Core flow:
      1. Use existing in_progress attempt if given, else create new.
      2. Look up each item by id within this assessment.
      3. Run the auto-check engine for each answer.
      4. Persist attempt + answers.
      5. Compute aggregate scores and weak skills.
      6. Generate and persist feedback.
    """
    items_by_id: dict[UUID, AssessmentItem] = {item.id: item for item in assessment.items}

    if existing_attempt and existing_attempt.status == "in_progress":
        attempt = existing_attempt
        attempt.status = "completed"
        attempt.completed_at = datetime.utcnow()
        attempt.progress_answers = []
        db.flush()
    else:
        attempt = AssessmentAttempt(
            user_id=user_id,
            assessment_id=assessment.id,
            status="completed",
            completed_at=datetime.utcnow(),
        )
        db.add(attempt)
        db.flush()

    total_earned = 0.0
    total_max = 0.0
    item_data_list: list[dict] = []
    results = []

    for answer_in in answers_in:
        item = items_by_id.get(answer_in.item_id)
        if item is None:
            continue

        item_dict = {
            "mode": item.mode,
            "correct_option_ids": item.correct_option_ids or [],
            "expected_keywords": item.expected_keywords or [],
            "rubric_checklist": item.rubric_checklist or [],
            "max_score": item.max_score,
            "related_skills": item.related_skills or [],
            "options": item.options or [],
            "explanation": item.explanation or "",
        }

        result = check_answer(
            item_dict,
            answer_in.selected_option_ids,
            answer_in.text_answer,
        )

        answer = AssessmentAnswer(
            attempt_id=attempt.id,
            item_id=item.id,
            mode=item.mode,
            selected_option_ids=answer_in.selected_option_ids,
            text_answer=answer_in.text_answer,
            is_correct=result.is_correct,
            earned_score=result.earned_score,
            auto_feedback=result.auto_feedback,
        )
        db.add(answer)

        total_earned += result.earned_score
        total_max += item.max_score
        item_data_list.append(item_dict)
        results.append(result)

    # Items not answered by the user still contribute to max_score
    answered_item_ids = {a.item_id for a in answers_in}
    for item in assessment.items:
        if item.id not in answered_item_ids:
            total_max += item.max_score
            item_data_list.append({
                "mode": item.mode,
                "max_score": item.max_score,
                "related_skills": item.related_skills or [],
            })
            results.append(CheckResult(0.0, False, "Not answered."))

    percentage = round(total_earned / total_max * 100, 2) if total_max > 0 else 0.0
    weak_skills = build_weak_skills(item_data_list, results)

    attempt.earned_score = round(total_earned, 3)
    attempt.max_score = round(total_max, 3)
    attempt.percentage = percentage
    attempt.weak_skills = weak_skills

    # Build and persist feedback
    rubric_notes = [r.auto_feedback for r in results if r.auto_feedback]
    recommended = build_recommended_materials(weak_skills)
    summary = build_summary(percentage)

    feedback = AssessmentFeedback(
        attempt_id=attempt.id,
        summary=summary,
        rubric_notes=rubric_notes,
        recommended_materials=recommended,
        weak_skills=weak_skills,
    )
    db.add(feedback)

    db.commit()
    db.refresh(attempt)
    return attempt


def get_attempt(db: Session, attempt_id: UUID) -> AssessmentAttempt | None:
    return db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()


def list_user_attempts(
    db: Session,
    user_id: UUID,
    *,
    assessment_id: UUID | None = None,
    offset: int = 0,
    limit: int = 20,
    load_assessment: bool = False,
) -> tuple[list[AssessmentAttempt], int]:
    q = db.query(AssessmentAttempt).filter(AssessmentAttempt.user_id == user_id)
    if assessment_id:
        q = q.filter(AssessmentAttempt.assessment_id == assessment_id)
    if load_assessment:
        q = q.options(joinedload(AssessmentAttempt.assessment))
    total = q.count()
    items = q.order_by(AssessmentAttempt.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def count_user_attempts_for_assessment(
    db: Session, user_id: UUID, assessment_id: UUID
) -> int:
    return (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.assessment_id == assessment_id,
        )
        .count()
    )


# ── Feedback ──────────────────────────────────────────────────────────────────

def get_feedback_by_attempt(
    db: Session, attempt_id: UUID
) -> AssessmentFeedback | None:
    return (
        db.query(AssessmentFeedback)
        .filter(AssessmentFeedback.attempt_id == attempt_id)
        .first()
    )


def admin_attempt_stats(db: Session) -> dict:
    """Завершённые попытки тестов (status == completed)."""
    completed = (
        db.query(func.count(AssessmentAttempt.id))
        .filter(AssessmentAttempt.status == "completed")
        .scalar()
        or 0
    )
    users_with_completed = (
        db.query(func.count(func.distinct(AssessmentAttempt.user_id)))
        .filter(AssessmentAttempt.status == "completed")
        .scalar()
        or 0
    )
    return {
        "completed_attempts": int(completed),
        "users_with_completed_attempts": int(users_with_completed),
    }
