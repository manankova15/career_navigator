from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..config import settings
from ..crud import (
    add_item_to_assessment,
    count_user_attempts_for_assessment,
    create_assessment,
    delete_assessment,
    get_assessment,
    list_assessments,
    submit_attempt,
    update_assessment,
)
from ..database import get_db
from ..schemas import (
    AssessmentCreate,
    AssessmentItemAdminOut,
    AssessmentItemCreate,
    AssessmentItemOut,
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
    Returns the completed attempt with per-answer auto-check results.
    """
    assessment = get_assessment(db, assessment_id)
    if not assessment or not assessment.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    max_attempts = settings.max_attempts_per_assessment
    if max_attempts > 0:
        used = count_user_attempts_for_assessment(db, user_id, assessment_id)
        if used >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Maximum attempts ({max_attempts}) reached for this assessment.",
            )

    attempt = submit_attempt(db, user_id, assessment, payload.answers)
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
