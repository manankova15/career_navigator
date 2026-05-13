from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..config import settings
from ..crud import (
    add_item_to_assessment,
    admin_attempt_stats,
    count_user_attempts_for_assessment,
    create_assessment,
    delete_assessment,
    delete_item,
    get_assessment,
    get_attempt,
    get_in_progress_attempt,
    list_assessments,
    start_attempt,
    submit_attempt,
    update_assessment,
    update_item,
)
from ..database import get_db
from ..schemas import (
    AdminAssessmentStatsOut,
    AssessmentCreate,
    AssessmentItemAdminOut,
    AssessmentItemCreate,
    AssessmentItemOut,
    AssessmentItemUpdate,
    AssessmentOut,
    AssessmentPage,
    AssessmentUpdate,
    AssessmentWithItemsAdminOut,
    AssessmentWithItemsOut,
    AttemptOut,
    AttemptSubmit,
)
from ..security import get_current_user_id, require_admin

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _assessment_out(assessment) -> AssessmentOut:
    return AssessmentOut(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        topic=assessment.topic,
        difficulty=assessment.difficulty,
        related_skills=assessment.related_skills or [],
        is_published=assessment.is_published,
        item_count=len(assessment.items),
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


# ── List assessments ──────────────────────────────────────────────────────────

@router.get("", response_model=AssessmentPage)
def list_all_assessments(
    topic: str | None = Query(None),
    difficulty: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Return paginated list of published assessments."""
    offset = (page - 1) * page_size
    items, total = list_assessments(
        db,
        topic=topic,
        difficulty=difficulty,
        published_only=True,
        offset=offset,
        limit=page_size,
    )
    return AssessmentPage(
        items=[_assessment_out(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/admin", response_model=AssessmentPage)
def list_all_assessments_admin(
    topic: str | None = Query(None),
    difficulty: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: list all assessments including unpublished."""
    offset = (page - 1) * page_size
    items, total = list_assessments(
        db,
        topic=topic,
        difficulty=difficulty,
        published_only=False,
        offset=offset,
        limit=page_size,
    )
    return AssessmentPage(
        items=[_assessment_out(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/admin/stats", response_model=AdminAssessmentStatsOut)
def admin_assessment_stats(
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    data = admin_attempt_stats(db)
    return AdminAssessmentStatsOut(**data)


# ── Create assessment ─────────────────────────────────────────────────────────

@router.post("", response_model=AssessmentWithItemsAdminOut, status_code=status.HTTP_201_CREATED)
def create_new_assessment(
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: create a new assessment optionally with items."""
    assessment = create_assessment(db, payload)
    return _build_admin_with_items(assessment)


# ── Get single assessment ─────────────────────────────────────────────────────

@router.get("/{assessment_id}", response_model=AssessmentWithItemsOut)
def get_single_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """Return assessment with items (correct answers hidden)."""
    assessment = get_assessment(db, assessment_id)
    if not assessment or not assessment.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return _build_user_with_items(assessment)


@router.get("/{assessment_id}/admin", response_model=AssessmentWithItemsAdminOut)
def get_single_assessment_admin(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: return assessment with full item data including answer keys."""
    assessment = get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return _build_admin_with_items(assessment)


# ── Update / delete assessment ────────────────────────────────────────────────

@router.patch("/{assessment_id}", response_model=AssessmentOut)
def patch_assessment(
    assessment_id: UUID,
    payload: AssessmentUpdate,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    assessment = update_assessment(db, assessment_id, payload)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return _assessment_out(assessment)


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    if not delete_assessment(db, assessment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")


# ── Add item ──────────────────────────────────────────────────────────────────

@router.post(
    "/{assessment_id}/items",
    response_model=AssessmentItemAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def add_item(
    assessment_id: UUID,
    payload: AssessmentItemCreate,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: add a single item to an existing assessment."""
    item = add_item_to_assessment(db, assessment_id, payload)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return _item_admin_out(item)


@router.patch(
    "/items/{item_id}",
    response_model=AssessmentItemAdminOut,
)
def patch_assessment_item(
    item_id: UUID,
    payload: AssessmentItemUpdate,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: update fields of a single assessment item."""
    item = update_item(db, item_id, payload)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return _item_admin_out(item)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_assessment_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: delete a single assessment item."""
    if not delete_item(db, item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


# ── Start attempt (for save/resume) ────────────────────────────────────────────

@router.post(
    "/{assessment_id}/start",
    response_model=AttemptOut,
    status_code=status.HTTP_201_CREATED,
)
def start_assessment_attempt(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Start an assessment; returns an in_progress attempt. Use progress save and submit with attempt_id to complete."""
    assessment = get_assessment(db, assessment_id)
    if not assessment or not assessment.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    existing = get_in_progress_attempt(db, user_id, assessment_id)
    if existing:
        return AttemptOut.from_orm_with_passed(existing)
    attempt = start_attempt(db, user_id, assessment)
    return AttemptOut.from_orm_with_passed(attempt)


# ── Submit attempt ────────────────────────────────────────────────────────────

@router.post(
    "/{assessment_id}/submit",
    response_model=AttemptOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_assessment_attempt(
    assessment_id: UUID,
    payload: AttemptSubmit,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Submit all answers for an assessment in one request.
    If attempt_id is provided, completes that in-progress attempt.
    Returns the completed attempt with per-answer auto-check results.
    """
    assessment = get_assessment(db, assessment_id)
    if not assessment or not assessment.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    existing_attempt = None
    if payload.attempt_id:
        existing_attempt = get_attempt(db, payload.attempt_id)
        if not existing_attempt or existing_attempt.user_id != user_id or existing_attempt.assessment_id != assessment_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attempt_id")
        if existing_attempt.status != "in_progress":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt already completed")

    if not existing_attempt and settings.max_attempts_per_assessment > 0:
        used = count_user_attempts_for_assessment(db, user_id, assessment_id)
        if used >= settings.max_attempts_per_assessment:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Maximum attempts ({settings.max_attempts_per_assessment}) "
                        "reached for this assessment."
                    ),
                )

    attempt = submit_attempt(db, user_id, assessment, payload.answers, existing_attempt=existing_attempt)
    # Событие в analytics (дашборд)
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(
                f"{settings.analytics_service_url.rstrip('/')}/analytics/events/assessment-completed",
                json={
                    "user_id": str(user_id),
                    "assessment_id": str(assessment_id),
                    "topic": assessment.topic,
                    "percentage": float(attempt.percentage),
                },
                headers={"X-Internal-Token": settings.internal_token},
            )
    except Exception:
        pass  # не ломаем ответ при недоступности analytics
    return AttemptOut.from_orm_with_passed(attempt)


# ── Internal serialisers ──────────────────────────────────────────────────────

def _item_out(item) -> AssessmentItemOut:
    from ..schemas import OptionSchema
    return AssessmentItemOut(
        id=item.id,
        assessment_id=item.assessment_id,
        position=item.position,
        prompt=item.prompt,
        mode=item.mode,
        options=[OptionSchema(**o) for o in (item.options or [])],
        max_score=item.max_score,
        related_skills=item.related_skills or [],
        created_at=item.created_at,
    )


def _item_admin_out(item) -> AssessmentItemAdminOut:
    from ..schemas import OptionSchema, RubricCriterion
    return AssessmentItemAdminOut(
        id=item.id,
        assessment_id=item.assessment_id,
        position=item.position,
        prompt=item.prompt,
        mode=item.mode,
        options=[OptionSchema(**o) for o in (item.options or [])],
        correct_option_ids=item.correct_option_ids or [],
        expected_keywords=item.expected_keywords or [],
        rubric_checklist=[RubricCriterion(**r) for r in (item.rubric_checklist or [])],
        max_score=item.max_score,
        related_skills=item.related_skills or [],
        created_at=item.created_at,
    )


def _build_user_with_items(assessment) -> AssessmentWithItemsOut:
    return AssessmentWithItemsOut(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        topic=assessment.topic,
        difficulty=assessment.difficulty,
        related_skills=assessment.related_skills or [],
        is_published=assessment.is_published,
        item_count=len(assessment.items),
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        items=[_item_out(i) for i in assessment.items],
    )


def _build_admin_with_items(assessment) -> AssessmentWithItemsAdminOut:
    return AssessmentWithItemsAdminOut(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        topic=assessment.topic,
        difficulty=assessment.difficulty,
        related_skills=assessment.related_skills or [],
        is_published=assessment.is_published,
        item_count=len(assessment.items),
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        items=[_item_admin_out(i) for i in assessment.items],
    )
