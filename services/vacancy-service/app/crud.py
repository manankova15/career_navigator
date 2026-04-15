import math
from datetime import datetime, timedelta
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


def _skills_or_match(skills: list[str]):
    cleaned = [s.strip() for s in skills if s and s.strip()]
    if not cleaned:
        return None
    return or_(
        *[
            func.array_to_string(CanonicalVacancy.skills, "\x01").ilike(f"%{s}%")
            for s in cleaned
        ]
    )


def search_vacancies(db: Session, params: VacancySearchParams):
    q = db.query(CanonicalVacancy).filter(CanonicalVacancy.status == params.status)

    qt = (params.query or "").strip()
    if qt:
        ts_query = func.plainto_tsquery("simple", qt)
        q = q.filter(
            or_(
                func.lower(CanonicalVacancy.title).contains(qt.lower()),
                func.lower(CanonicalVacancy.company).contains(qt.lower()),
                CanonicalVacancy.search_vector.op("@@")(ts_query),
            )
        )
    else:
        if params.title:
            q = q.filter(
                func.lower(CanonicalVacancy.title).contains(params.title.lower())
            )
        if params.q:
            ts_query = func.plainto_tsquery("simple", params.q)
            q = q.filter(CanonicalVacancy.search_vector.op("@@")(ts_query))

    if params.profession_area:
        q = q.filter(CanonicalVacancy.profession_area.in_(params.profession_area))

    if params.specialization:
        spec = params.specialization.strip().lower()
        q = q.filter(
            or_(
                func.lower(CanonicalVacancy.specialization) == spec,
                func.lower(CanonicalVacancy.specialization).contains(spec),
            )
        )

    if params.city:
        c = params.city.strip().lower()
        q = q.filter(
            or_(
                func.lower(CanonicalVacancy.location_city).contains(c),
                func.lower(CanonicalVacancy.location).contains(c),
            )
        )

    if params.country:
        c = params.country.strip().lower()
        q = q.filter(
            or_(
                func.lower(CanonicalVacancy.location_country).contains(c),
                func.lower(CanonicalVacancy.location).contains(c),
            )
        )

    if params.work_format:
        q = q.filter(
            CanonicalVacancy.work_format.isnot(None),
            CanonicalVacancy.work_format.overlap(params.work_format),
        )

    if params.employment_type:
        q = q.filter(
            CanonicalVacancy.employment_type.isnot(None),
            CanonicalVacancy.employment_type.overlap(params.employment_type),
        )

    if params.schedule_type:
        q = q.filter(CanonicalVacancy.schedule_type.in_(params.schedule_type))

    if params.experience_level:
        q = q.filter(CanonicalVacancy.experience_level == params.experience_level)

    if params.salary_from is not None:
        q = q.filter(
            or_(
                CanonicalVacancy.salary_from >= params.salary_from,
                CanonicalVacancy.salary_to >= params.salary_from,
            )
        )

    if params.salary_currency:
        cur = params.salary_currency.strip().upper()
        if cur == "OTHER":
            q = q.filter(
                CanonicalVacancy.salary_currency.isnot(None),
                ~CanonicalVacancy.salary_currency.in_(["RUB", "USD", "EUR", "KZT"]),
            )
        else:
            q = q.filter(CanonicalVacancy.salary_currency == cur)

    if params.has_salary:
        q = q.filter(
            or_(
                CanonicalVacancy.salary_from.isnot(None),
                CanonicalVacancy.salary_to.isnot(None),
            )
        )

    if params.skills:
        sm = _skills_or_match(params.skills)
        if sm is not None:
            q = q.filter(sm)

    if params.english_level:
        q = q.filter(CanonicalVacancy.english_level == params.english_level)

    if params.education_level:
        q = q.filter(CanonicalVacancy.education_level == params.education_level)

    if params.published_within:
        days_map = {"1d": 1, "3d": 3, "7d": 7, "30d": 30}
        days = days_map.get(params.published_within.strip().lower())
        if days is not None:
            since = datetime.utcnow() - timedelta(days=days)
            q = q.filter(
                CanonicalVacancy.published_at.isnot(None),
                CanonicalVacancy.published_at >= since,
            )

    if params.source_id:
        q = q.filter(CanonicalVacancy.source_id == params.source_id)

    if params.seniority:
        q = q.filter(CanonicalVacancy.seniority == params.seniority)

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
    # Сначала canonical + CASCADE (таблица dedup_log ссылается на canonical_vacancies), затем raw.
    db.execute(text("TRUNCATE TABLE canonical_vacancies RESTART IDENTITY CASCADE"))
    db.execute(text("TRUNCATE TABLE raw_vacancies RESTART IDENTITY CASCADE"))
    db.commit()
    return raw_count, canonical_count
