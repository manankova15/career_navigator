from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    RecommendationSession,
    SkillGapRecord,
    UserLikedVacancy,
    UserVacancySignal,
    VacancyRecommendation,
)


def get_latest_session(db: Session, user_id: UUID) -> RecommendationSession | None:
    return (
        db.query(RecommendationSession)
        .filter(RecommendationSession.user_id == user_id)
        .order_by(RecommendationSession.created_at.desc())
        .first()
    )


def create_session(
    db: Session,
    user_id: UUID,
    algorithm: str,
    total_scored: int,
    scored_items: list[dict],
) -> RecommendationSession:
    session = RecommendationSession(
        user_id=user_id,
        algorithm=algorithm,
        total_scored=total_scored,
    )
    db.add(session)
    db.flush()

    for item in scored_items:
        rec = VacancyRecommendation(
            session_id=session.id,
            user_id=user_id,
            vacancy_id=item["vacancy_id"],
            score=item["score"],
            base_score=item.get("base_score", item["score"]),
            skill_score=item.get("skill_score", 0),
            role_score=item.get("role_score", 0),
            location_score=item.get("location_score", 0),
            salary_score=item.get("salary_score", 0),
            seniority_score=item.get("seniority_score", 0),
            format_score=item.get("format_score", 0),
            matched_skills=item.get("matched_skills", []),
            missing_skills=item.get("missing_skills", []),
            reasons=item.get("reasons", []),
            features=item.get("features", {}),
        )
        db.add(rec)

    db.commit()
    db.refresh(session)
    return session


def update_scores_in_place(db: Session, scores_by_rec_id: dict[UUID, float]) -> None:
    """Запись пересчитанных score после _live_rescore"""
    if not scores_by_rec_id:
        return
    rows = (
        db.query(VacancyRecommendation)
        .filter(VacancyRecommendation.id.in_(list(scores_by_rec_id.keys())))
        .all()
    )
    for rec in rows:
        new = scores_by_rec_id.get(rec.id)
        if new is not None:
            rec.score = round(float(new), 4)
    db.commit()


def save_skill_gap(
    db: Session,
    session_id: UUID,
    user_id: UUID,
    gaps: list[dict],
) -> list[SkillGapRecord]:
    records = []
    for rank, gap in enumerate(gaps, start=1):
        record = SkillGapRecord(
            session_id=session_id,
            user_id=user_id,
            skill_name=gap["skill_name"],
            importance_score=gap["importance_score"],
            frequency=gap["frequency"],
            recommended_resources=gap.get("recommended_resources", []),
            rank=rank,
        )
        db.add(record)
        records.append(record)
    db.commit()
    return records


def get_latest_skill_gaps(
    db: Session, user_id: UUID
) -> tuple[list[SkillGapRecord], RecommendationSession | None]:
    session = get_latest_session(db, user_id)
    if not session:
        return [], None
    gaps = (
        db.query(SkillGapRecord)
        .filter(SkillGapRecord.session_id == session.id)
        .order_by(SkillGapRecord.rank)
        .all()
    )
    return gaps, session


def apply_feedback(
    db: Session,
    rec_id: UUID,
    user_id: UUID,
    feedback: str,
) -> VacancyRecommendation | None:
    rec = (
        db.query(VacancyRecommendation)
        .filter(
            VacancyRecommendation.id == rec_id,
            VacancyRecommendation.user_id == user_id,
        )
        .first()
    )
    if not rec:
        return None
    rec.feedback = feedback
    rec.feedback_at = datetime.utcnow()
    db.flush()

    # Дублирование в user_vacancy_signals для следующих сессий
    features = rec.features or {}
    sentiment = {"positive": 1.0, "negative": -1.0}.get(feedback, 0.0)
    upsert_signal(
        db,
        user_id=user_id,
        vacancy_id=rec.vacancy_id,
        sentiment=sentiment,
        kind=feedback,
        source="recommendation_card",
        vacancy_title=features.get("vacancy_title"),
        vacancy_skills=list(features.get("vacancy_skills") or rec.matched_skills or []),
        vacancy_category=features.get("vacancy_category"),
        vacancy_specialization=features.get("vacancy_specialization"),
    )
    db.commit()
    db.refresh(rec)
    return rec


def get_active_likes(db: Session, user_id: UUID) -> list[UserLikedVacancy]:
    return (
        db.query(UserLikedVacancy)
        .filter(UserLikedVacancy.user_id == user_id, UserLikedVacancy.unliked_at.is_(None))
        .order_by(UserLikedVacancy.liked_at.desc())
        .all()
    )


def upsert_like(
    db: Session,
    user_id: UUID,
    vacancy_id: UUID,
    vacancy_title: str | None,
    vacancy_skills: list[str] | None,
    vacancy_category: str | None = None,
    vacancy_specialization: str | None = None,
) -> UserLikedVacancy:
    row = (
        db.query(UserLikedVacancy)
        .filter(UserLikedVacancy.user_id == user_id, UserLikedVacancy.vacancy_id == vacancy_id)
        .first()
    )
    title = (vacancy_title or "")[:300]
    skills = vacancy_skills if vacancy_skills is not None else []
    cat = (vacancy_category or "").strip() or None
    spec = (vacancy_specialization or "").strip() or None
    if row:
        row.unliked_at = None
        row.vacancy_title = title or row.vacancy_title
        row.vacancy_skills = skills
        if cat:
            row.vacancy_category = cat
        if spec:
            row.vacancy_specialization = spec
        row.liked_at = datetime.utcnow()
    else:
        row = UserLikedVacancy(
            user_id=user_id,
            vacancy_id=vacancy_id,
            vacancy_title=title or None,
            vacancy_skills=skills,
            vacancy_category=cat,
            vacancy_specialization=spec,
        )
        db.add(row)

    # Лайк → сигнал +1 без отдельного «interested»
    upsert_signal(
        db,
        user_id=user_id,
        vacancy_id=vacancy_id,
        sentiment=1.0,
        kind="like",
        source="like",
        vacancy_title=title or None,
        vacancy_skills=skills,
        vacancy_category=cat,
        vacancy_specialization=spec,
    )
    db.commit()
    db.refresh(row)
    return row


def soft_unlike(db: Session, user_id: UUID, vacancy_id: UUID) -> bool:
    row = (
        db.query(UserLikedVacancy)
        .filter(
            UserLikedVacancy.user_id == user_id,
            UserLikedVacancy.vacancy_id == vacancy_id,
            UserLikedVacancy.unliked_at.is_(None),
        )
        .first()
    )
    if not row:
        return False
    row.unliked_at = datetime.utcnow()
    # Снятие лайка — удалить сигнал kind=like
    sig = (
        db.query(UserVacancySignal)
        .filter(
            UserVacancySignal.user_id == user_id,
            UserVacancySignal.vacancy_id == vacancy_id,
            UserVacancySignal.kind == "like",
        )
        .first()
    )
    if sig:
        db.delete(sig)
    db.commit()
    return True


# ── user_vacancy_signals ────────────────────────────────────────────────────

def upsert_signal(
    db: Session,
    user_id: UUID,
    vacancy_id: UUID,
    sentiment: float,
    kind: str,
    source: str | None,
    vacancy_title: str | None,
    vacancy_skills: list[str] | None,
    vacancy_category: str | None = None,
    vacancy_specialization: str | None = None,
) -> UserVacancySignal:
    row = (
        db.query(UserVacancySignal)
        .filter(
            UserVacancySignal.user_id == user_id,
            UserVacancySignal.vacancy_id == vacancy_id,
        )
        .first()
    )
    title = (vacancy_title or "")[:300] or None
    skills = list(vacancy_skills or [])
    cat = (vacancy_category or "").strip() or None
    spec = (vacancy_specialization or "").strip() or None
    if row:
        row.sentiment = float(sentiment)
        row.kind = kind
        row.source = source
        if title:
            row.vacancy_title = title
        if skills:
            row.vacancy_skills = skills
        if cat:
            row.vacancy_category = cat
        if spec:
            row.vacancy_specialization = spec
        row.updated_at = datetime.utcnow()
    else:
        row = UserVacancySignal(
            user_id=user_id,
            vacancy_id=vacancy_id,
            sentiment=float(sentiment),
            kind=kind,
            source=source,
            vacancy_title=title,
            vacancy_skills=skills,
            vacancy_category=cat,
            vacancy_specialization=spec,
        )
        db.add(row)
    db.flush()
    return row


def list_signals(db: Session, user_id: UUID) -> list[UserVacancySignal]:
    return (
        db.query(UserVacancySignal)
        .filter(UserVacancySignal.user_id == user_id)
        .order_by(UserVacancySignal.updated_at.desc())
        .all()
    )
