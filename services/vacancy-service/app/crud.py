import math
from uuid import UUID

from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from .models import CanonicalVacancy, RawVacancy
from .schemas import CanonicalVacancyIn, RawVacancyIn, VacancySearchParams


# ── Raw vacancies ────────────────────────────────────────────────────────────

def ingest_raw(db: Session, data: RawVacancyIn) -> tuple[RawVacancy, bool]:
    """Upsert raw vacancy. Returns (record, created)."""
    existing = (
        db.query(RawVacancy)
        .filter(
            RawVacancy.source_id == data.source_id,
            RawVacancy.external_id == data.external_id,
        )
        .first()
    )
    if existing:
        existing.payload = data.payload
        db.commit()
        db.refresh(existing)
        return existing, False

    raw = RawVacancy(**data.model_dump())
    db.add(raw)
    db.commit()
    db.refresh(raw)
    return raw, True


def get_unprocessed_raw(db: Session, limit: int = 100) -> list[RawVacancy]:
    return (
        db.query(RawVacancy)
        .filter(RawVacancy.processed == False)  # noqa: E712
        .limit(limit)
        .all()
    )


def mark_raw_processed(db: Session, raw_id: UUID) -> None:
    raw = db.query(RawVacancy).filter(RawVacancy.id == raw_id).first()
    if raw:
        raw.processed = True
        db.commit()


# ── Canonical vacancies ──────────────────────────────────────────────────────

def upsert_canonical(db: Session, data: CanonicalVacancyIn) -> tuple[CanonicalVacancy, bool]:
    """Upsert canonical vacancy. Returns (record, created)."""
    existing = None
    if data.external_id:
        existing = (
            db.query(CanonicalVacancy)
            .filter(
                CanonicalVacancy.source_id == data.source_id,
                CanonicalVacancy.external_id == data.external_id,
            )
            .first()
        )

    if existing:
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False

    vacancy = CanonicalVacancy(**data.model_dump())
    db.add(vacancy)
    db.commit()
    db.refresh(vacancy)
    return vacancy, True


def get_vacancy(db: Session, vacancy_id: UUID) -> CanonicalVacancy | None:
    return (
        db.query(CanonicalVacancy)
        .filter(CanonicalVacancy.id == vacancy_id)
        .first()
    )


def search_vacancies(db: Session, params: VacancySearchParams):
    q = db.query(CanonicalVacancy).filter(CanonicalVacancy.status == params.status)

    if params.q:
        # PostgreSQL full-text search: support both Russian and English
        ts_query = func.plainto_tsquery("simple", params.q)
        q = q.filter(CanonicalVacancy.search_vector.op("@@")(ts_query))

    if params.location:
        q = q.filter(
            func.lower(CanonicalVacancy.location).contains(params.location.lower())
        )

    if params.seniority:
        q = q.filter(CanonicalVacancy.seniority == params.seniority)

    if params.salary_from is not None:
        q = q.filter(
            or_(
                CanonicalVacancy.salary_from >= params.salary_from,
                CanonicalVacancy.salary_to >= params.salary_from,
            )
        )

    if params.skills:
        for skill in params.skills:
            q = q.filter(CanonicalVacancy.skills.any(skill.lower()))

    if params.source_id:
        q = q.filter(CanonicalVacancy.source_id == params.source_id)

    total = q.count()
    pages = max(1, math.ceil(total / params.page_size))
    offset = (params.page - 1) * params.page_size

    items = (
        q.order_by(CanonicalVacancy.published_at.desc().nullslast())
        .offset(offset)
        .limit(params.page_size)
        .all()
    )

    return items, total, pages


def expire_vacancies(db: Session) -> int:
    """Mark vacancies with expires_at in the past as expired."""
    result = db.execute(
        text("""
            UPDATE canonical_vacancies
            SET status = 'expired', updated_at = now()
            WHERE status = 'active'
              AND expires_at IS NOT NULL
              AND expires_at < now()
        """)
    )
    db.commit()
    return result.rowcount


def truncate_all_vacancies(db: Session) -> tuple[int, int]:
    """Delete all raw and canonical vacancies. Returns (raw_deleted, canonical_deleted)."""
    raw_count = db.query(RawVacancy).count()
    canonical_count = db.query(CanonicalVacancy).count()
    db.query(RawVacancy).delete()
    db.query(CanonicalVacancy).delete()
    db.commit()
    return raw_count, canonical_count
