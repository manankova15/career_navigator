from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import (
    apply_feedback,
    get_active_likes,
    get_latest_session,
    get_latest_skill_gaps,
    soft_unlike,
    update_scores_in_place,
    upsert_like,
    upsert_signal,
)
from ..database import get_db
from ..models import VacancyRecommendation
from ..orchestrator import run_recommendation, run_recommendation_from_db_profile

CURRENT_ALGORITHM = "hybrid_ahp_v3"
from ..personalization import build_affinity, score_with_personalization
from ..schemas import (
    FeedbackIn,
    InteractionIn,
    InteractionOut,
    LikedVacancyOut,
    RecommendFeedPage,
    RecommendationOut,
    SkillGapOut,
    SkillGapReportOut,
    VacancyLikeIn,
)
from ..security import get_current_user_id, get_raw_token

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


_SENTIMENT_MAP = {
    "positive": (1.0, "interested"),
    "negative": (-1.0, "not_interested"),
    "neutral": (0.0, "viewed"),
}


def _rec_to_out(
    rec: VacancyRecommendation,
    final_score: float | None = None,
    personal_boost: float = 0.0,
    direct_signal: float | None = None,
) -> RecommendationOut:
    score = round(float(final_score), 4) if final_score is not None else float(rec.score)
    features = rec.features or {}
    return RecommendationOut(
        id=rec.id,
        vacancy_id=rec.vacancy_id,
        score=score,
        base_score=float(rec.base_score or rec.score or 0.0),
        personal_boost=round(float(personal_boost), 4),
        direct_signal=direct_signal,
        ml_score=rec.ml_score,
        category_score=float(features.get("category_score", 0.5)),
        specialization_score=float(features.get("specialization_score", 0.5)),
        skill_score=float(rec.skill_score or 0),
        role_score=float(rec.role_score or 0),
        location_score=float(rec.location_score or 0),
        salary_score=float(rec.salary_score or 0),
        seniority_score=float(rec.seniority_score or 0),
        format_score=float(rec.format_score or 0),
        matched_skills=list(rec.matched_skills or []),
        missing_skills=list(rec.missing_skills or []),
        reasons=list(rec.reasons or []),
        feedback=rec.feedback,
        created_at=rec.created_at,
    )


def _live_rescore(
    db: Session, user_id: UUID, recs: list[VacancyRecommendation]
) -> list[tuple[VacancyRecommendation, float, float, float | None]]:
    """Пересчёт финального скора по AffinityProfile без вызова ml-service (модель v3 §5)"""
    affinity = build_affinity(db, user_id)
    scored: list[tuple[VacancyRecommendation, float, float, float | None]] = []
    persist: dict[UUID, float] = {}
    for rec in recs:
        features = rec.features or {}
        final, boost, direct = score_with_personalization(
            affinity,
            base_score=float(rec.base_score or rec.score or 0),
            vacancy_id=rec.vacancy_id,
            vacancy_skills=list(features.get("vacancy_skills") or []),
            vacancy_title=features.get("vacancy_title") or "",
            vacancy_category=features.get("vacancy_category"),
            vacancy_specialization=features.get("vacancy_specialization"),
        )
        scored.append((rec, final, boost, direct))
        if abs(float(rec.score or 0) - final) > 1e-4:
            persist[rec.id] = final
    if persist:
        update_scores_in_place(db, persist)
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


@router.get("/me", response_model=RecommendFeedPage)
async def get_my_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Последняя сессия; персонализация пересчитывается на каждый запрос из текущих реакций"""
    session = get_latest_session(db, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations yet. Call POST /recommendations/refresh first.",
        )
    # Пустая сессия после сбоя пайплайна — отдаём 404, фронт дергает refresh
    if not session.recommendations or (session.total_scored or 0) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations yet. Call POST /recommendations/refresh first.",
        )
    # Старый algorithm — тихий пересчёт из кэша профиля в БД
    if session.algorithm != CURRENT_ALGORITHM:
        try:
            refreshed = run_recommendation_from_db_profile(db, user_id)
        except HTTPException:
            refreshed = None
        if refreshed is not None:
            session = refreshed
    rescored = _live_rescore(db, user_id, list(session.recommendations))
    offset = (page - 1) * page_size
    page_slice = rescored[offset: offset + page_size]
    return RecommendFeedPage(
        items=[_rec_to_out(r, f, b, d) for (r, f, b, d) in page_slice],
        session_id=session.id,
        session_created_at=session.created_at,
        total=len(rescored),
        algorithm=session.algorithm,
    )


@router.post("/refresh", response_model=RecommendFeedPage, status_code=status.HTTP_201_CREATED)
async def refresh_recommendations(
    user_id: UUID = Depends(get_current_user_id),
    user_token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    session = run_recommendation(db, user_id, user_token)
    rescored = _live_rescore(db, user_id, list(session.recommendations))[:20]
    return RecommendFeedPage(
        items=[_rec_to_out(r, f, b, d) for (r, f, b, d) in rescored],
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
    rec = apply_feedback(db, rec_id, user_id, body.feedback)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return _rec_to_out(rec)


@router.post("/likes/{vacancy_id}", response_model=LikedVacancyOut, status_code=status.HTTP_201_CREATED)
async def like_vacancy(
    vacancy_id: UUID,
    body: VacancyLikeIn = VacancyLikeIn(),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = upsert_like(
        db,
        user_id,
        vacancy_id,
        body.vacancy_title,
        body.vacancy_skills,
        vacancy_category=body.vacancy_category,
        vacancy_specialization=body.vacancy_specialization,
    )
    return LikedVacancyOut(
        id=row.id,
        vacancy_id=row.vacancy_id,
        vacancy_title=row.vacancy_title,
        vacancy_skills=list(row.vacancy_skills or []),
        vacancy_category=row.vacancy_category,
        vacancy_specialization=row.vacancy_specialization,
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
            vacancy_category=r.vacancy_category,
            vacancy_specialization=r.vacancy_specialization,
            liked_at=r.liked_at,
        )
        for r in rows
    ]


@router.post(
    "/interactions/{vacancy_id}",
    response_model=InteractionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register an interest signal ('Да, интересно' / 'Нет, не подходит')",
)
async def register_interaction(
    vacancy_id: UUID,
    body: InteractionIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    sentiment, kind = _SENTIMENT_MAP[body.sentiment]
    row = upsert_signal(
        db,
        user_id=user_id,
        vacancy_id=vacancy_id,
        sentiment=sentiment,
        kind=kind,
        source=body.source or "detail_page",
        vacancy_title=body.vacancy_title,
        vacancy_skills=body.vacancy_skills,
        vacancy_category=body.vacancy_category,
        vacancy_specialization=body.vacancy_specialization,
    )
    db.commit()
    return InteractionOut(
        id=row.id,
        vacancy_id=row.vacancy_id,
        sentiment=row.sentiment,
        kind=row.kind,
        updated_at=row.updated_at,
    )


@router.get("/skill-gap", response_model=SkillGapReportOut)
async def get_skill_gap(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
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
