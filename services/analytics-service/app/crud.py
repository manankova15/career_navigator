from __future__ import annotations
from datetime import datetime
from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session
from .models import AssessmentStat, DailyActiveUsers, UserEvent


def ingest_event(db: Session, user_id: UUID, event_type: str, resource_type: str | None,
                 resource_id: str | None, properties: dict, occurred_at: datetime | None = None) -> UserEvent:
    event = UserEvent(
        user_id=user_id, event_type=event_type,
        resource_type=resource_type, resource_id=resource_id,
        properties=properties, occurred_at=occurred_at or datetime.utcnow(),
    )
    db.add(event)

    # Update DAU
    date_str = (occurred_at or datetime.utcnow()).strftime("%Y-%m-%d")
    dau = db.query(DailyActiveUsers).filter(DailyActiveUsers.date == date_str).first()
    if dau is None:
        dau = DailyActiveUsers(date=date_str, user_count=0, event_count=0)
        db.add(dau)
    dau.event_count += 1
    dau.updated_at = datetime.utcnow()
    db.flush()

    # Refresh distinct user count for that day
    user_count = db.query(func.count(func.distinct(UserEvent.user_id))).filter(
        func.date_trunc("day", UserEvent.occurred_at) == func.date_trunc("day", func.cast(date_str, UserEvent.occurred_at.type))
    ).scalar() or 0
    dau.user_count = user_count

    db.commit()
    db.refresh(event)
    return event


def upsert_assessment_stat(db: Session, user_id: UUID, assessment_id: UUID,
                            topic: str | None, percentage: float) -> AssessmentStat:
    stat = db.query(AssessmentStat).filter(
        AssessmentStat.user_id == user_id,
        AssessmentStat.assessment_id == assessment_id,
    ).first()
    now = datetime.utcnow()
    if stat is None:
        stat = AssessmentStat(user_id=user_id, assessment_id=assessment_id, topic=topic,
                               attempts_count=1, best_percentage=percentage,
                               last_percentage=percentage, avg_percentage=percentage,
                               last_attempted_at=now)
        db.add(stat)
    else:
        stat.attempts_count += 1
        stat.last_percentage = percentage
        stat.best_percentage = max(stat.best_percentage, percentage)
        # Running average
        stat.avg_percentage = round(
            (stat.avg_percentage * (stat.attempts_count - 1) + percentage) / stat.attempts_count, 2
        )
        stat.last_attempted_at = now
        stat.updated_at = now
    db.commit()
    db.refresh(stat)
    return stat


def get_user_assessment_stats(db: Session, user_id: UUID) -> list[AssessmentStat]:
    return db.query(AssessmentStat).filter(
        AssessmentStat.user_id == user_id
    ).order_by(AssessmentStat.last_attempted_at.desc()).all()


def get_user_events(db: Session, user_id: UUID, event_type: str | None = None,
                    limit: int = 50) -> list[UserEvent]:
    q = db.query(UserEvent).filter(UserEvent.user_id == user_id)
    if event_type:
        q = q.filter(UserEvent.event_type == event_type)
    return q.order_by(UserEvent.occurred_at.desc()).limit(limit).all()


def count_user_events_by_type(db: Session, user_id: UUID, event_type: str) -> int:
    """Общее количество событий данного типа для пользователя (для счётчиков на дашборде)."""
    return (
        db.query(func.count(UserEvent.id))
        .filter(UserEvent.user_id == user_id, UserEvent.event_type == event_type)
        .scalar()
        or 0
    )


def get_product_metrics(db: Session) -> dict:
    total_events = db.query(func.count(UserEvent.id)).scalar() or 0
    total_users = db.query(func.count(func.distinct(UserEvent.user_id))).scalar() or 0
    total_assessments_completed = db.query(func.count(UserEvent.id)).filter(
        UserEvent.event_type == "assessment_completed"
    ).scalar() or 0
    total_vacancy_views = db.query(func.count(UserEvent.id)).filter(
        UserEvent.event_type == "vacancy_viewed"
    ).scalar() or 0
    total_recommendation_clicks = db.query(func.count(UserEvent.id)).filter(
        UserEvent.event_type == "recommendation_clicked"
    ).scalar() or 0

    last_dau = db.query(DailyActiveUsers).order_by(DailyActiveUsers.date.desc()).first()

    return {
        "total_events": total_events,
        "total_users_with_events": total_users,
        "assessments_completed": total_assessments_completed,
        "vacancy_views": total_vacancy_views,
        "recommendation_clicks": total_recommendation_clicks,
        "last_dau": last_dau.user_count if last_dau else 0,
        "last_dau_date": last_dau.date if last_dau else None,
    }


def get_dau_series(db: Session, days: int = 30) -> list[dict]:
    rows = db.query(DailyActiveUsers).order_by(DailyActiveUsers.date.desc()).limit(days).all()
    return [{"date": r.date, "users": r.user_count, "events": r.event_count} for r in rows]
