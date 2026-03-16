from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import apply_feedback, get_latest_session, get_latest_skill_gaps
from ..database import get_db
from ..orchestrator import run_recommendation
from ..schemas import (
    FeedbackIn,
    RecommendFeedPage,
    RecommendationOut,
    SkillGapOut,
    SkillGapReportOut,
)
from ..security import get_current_user_id, get_raw_token

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/me", response_model=RecommendFeedPage)
async def get_my_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return the latest recommendation session for this user."""
    session = get_latest_session(db, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations yet. Call POST /recommendations/refresh first.",
        )
    recs = session.recommendations
    offset = (page - 1) * page_size
    page_items = recs[offset: offset + page_size]
    return RecommendFeedPage(
        items=page_items,
        session_id=session.id,
        session_created_at=session.created_at,
        total=len(recs),
        algorithm=session.algorithm,
    )


@router.post("/refresh", response_model=RecommendFeedPage, status_code=status.HTTP_201_CREATED)
async def refresh_recommendations(
    user_id: UUID = Depends(get_current_user_id),
    user_token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    """
    Trigger a fresh recommendation run:
    fetch profile → fetch vacancies → score → persist → return top-20.
    """
    session = run_recommendation(db, user_id, user_token)
    recs = session.recommendations[:20]
    return RecommendFeedPage(
        items=recs,
        session_id=session.id,
        session_created_at=session.created_at,
        total=len(session.recommendations),
        algorithm=session.algorithm,
    )


@router.patch("/{rec_id}/feedback", response_model=RecommendationOut)
async def leave_feedback(
    rec_id: UUID,
    body: FeedbackIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark a recommendation as positive / negative / saved."""
    rec = apply_feedback(db, rec_id, user_id, body.feedback)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return rec


@router.get("/skill-gap", response_model=SkillGapReportOut)
async def get_skill_gap(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return the skill-gap report from the latest recommendation session."""
    gaps, session = get_latest_skill_gaps(db, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No skill-gap data. Call POST /recommendations/refresh first.",
        )
    return SkillGapReportOut(
        session_id=session.id,
        user_id=user_id,
        algorithm=session.algorithm,
        total_target_vacancies=min(30, session.total_scored),
        gaps=[
            SkillGapOut(
                skill_name=g.skill_name,
                importance_score=g.importance_score,
                frequency=g.frequency,
                rank=g.rank,
                recommended_resources=g.recommended_resources or [],
            )
            for g in gaps
        ],
    )
