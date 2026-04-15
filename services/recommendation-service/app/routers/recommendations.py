from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import (
    apply_feedback,
    get_active_likes,
    get_latest_session,
    get_latest_skill_gaps,
    soft_unlike,
    upsert_like,
)
from ..database import get_db
from ..orchestrator import run_recommendation
from ..schemas import (
    FeedbackIn,
    LikedVacancyOut,
    RecommendFeedPage,
    RecommendationOut,
    SkillGapOut,
    SkillGapReportOut,
    VacancyLikeIn,
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


@router.post("/likes/{vacancy_id}", response_model=LikedVacancyOut, status_code=status.HTTP_201_CREATED)
async def like_vacancy(
    vacancy_id: UUID,
    body: VacancyLikeIn = VacancyLikeIn(),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Persist a vacancy like for personalization."""
    row = upsert_like(
        db,
        user_id,
        vacancy_id,
        body.vacancy_title,
        body.vacancy_skills,
    )
    skills = list(row.vacancy_skills or [])
    return LikedVacancyOut(
        id=row.id,
        vacancy_id=row.vacancy_id,
        vacancy_title=row.vacancy_title,
        vacancy_skills=skills,
        liked_at=row.liked_at,
    )


@router.delete("/likes/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_vacancy(
    vacancy_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    soft_unlike(db, user_id, vacancy_id)
    return None


@router.get("/likes", response_model=list[LikedVacancyOut])
async def list_my_likes(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = get_active_likes(db, user_id)
    return [
        LikedVacancyOut(
            id=r.id,
            vacancy_id=r.vacancy_id,
            vacancy_title=r.vacancy_title,
            vacancy_skills=list(r.vacancy_skills or []),
            liked_at=r.liked_at,
        )
        for r in rows
    ]


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
