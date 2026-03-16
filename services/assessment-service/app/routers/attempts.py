from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import get_attempt, get_feedback_by_attempt, list_user_attempts
from ..database import get_db
from ..schemas import AttemptOut, AttemptPage, AttemptSummaryOut, FeedbackOut
from ..security import get_current_user_id, require_admin

router = APIRouter(prefix="/attempts", tags=["attempts"])


# ── User: own attempts ────────────────────────────────────────────────────────

@router.get("/me", response_model=AttemptPage)
def my_attempts(
    assessment_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Return paginated history of the current user's assessment attempts."""
    offset = (page - 1) * page_size
    items, total = list_user_attempts(
        db,
        user_id,
        assessment_id=assessment_id,
        offset=offset,
        limit=page_size,
    )
    return AttemptPage(
        items=[AttemptSummaryOut.from_orm_with_passed(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{attempt_id}", response_model=AttemptOut)
def get_my_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Return a specific attempt with all per-answer check results."""
    attempt = get_attempt(db, attempt_id)
    if not attempt or attempt.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    return AttemptOut.from_orm_with_passed(attempt)


@router.get("/{attempt_id}/feedback", response_model=FeedbackOut)
def get_my_feedback(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Return auto-generated feedback for a completed attempt."""
    attempt = get_attempt(db, attempt_id)
    if not attempt or attempt.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    feedback = get_feedback_by_attempt(db, attempt_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not available yet",
        )
    return feedback


# ── Admin: any user's attempts ────────────────────────────────────────────────

@router.get("/admin/user/{user_id}", response_model=AttemptPage)
def admin_list_user_attempts(
    user_id: UUID,
    assessment_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: list attempts for any user."""
    offset = (page - 1) * page_size
    items, total = list_user_attempts(
        db,
        user_id,
        assessment_id=assessment_id,
        offset=offset,
        limit=page_size,
    )
    return AttemptPage(
        items=[AttemptSummaryOut.from_orm_with_passed(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/admin/{attempt_id}", response_model=AttemptOut)
def admin_get_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: retrieve any attempt by id."""
    attempt = get_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    return attempt


@router.get("/admin/{attempt_id}/feedback", response_model=FeedbackOut)
def admin_get_feedback(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    _admin_id: UUID = Depends(require_admin),
):
    """Admin: retrieve feedback for any attempt."""
    feedback = get_feedback_by_attempt(db, attempt_id)
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    return feedback
