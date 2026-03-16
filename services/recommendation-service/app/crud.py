from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from .models import RecommendationSession, SkillGapRecord, VacancyRecommendation


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
            skill_score=item.get("skill_score", 0),
            location_score=item.get("location_score", 0),
            salary_score=item.get("salary_score", 0),
            seniority_score=item.get("seniority_score", 0),
            matched_skills=item.get("matched_skills", []),
            missing_skills=item.get("missing_skills", []),
            reasons=item.get("reasons", []),
        )
        db.add(rec)

    db.commit()
    db.refresh(session)
    return session


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


def get_latest_skill_gaps(db: Session, user_id: UUID) -> tuple[list[SkillGapRecord], RecommendationSession | None]:
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
    db.commit()
    db.refresh(rec)
    return rec
