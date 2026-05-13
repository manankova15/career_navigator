import math
import re
from uuid import UUID

from sqlalchemy import Integer, String, bindparam, case, func, literal, or_, text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import Session

from .models import CanonicalVacancy, RawVacancy
from .salary_parser import (
    compute_rub_amounts,
    normalize_period_to_month,
    parse_salary,
)
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

def _enrich_salary_fields(payload: dict) -> dict:
    """Поля зарплаты: месячный эквивалент, RUB для сортировки; parse_salary если сумм нет; приоритет у явных полей от клиента"""
    salary_from = payload.get("salary_from")
    salary_to = payload.get("salary_to")
    currency = payload.get("salary_currency") or "RUB"
    period = payload.get("salary_period") or "month"

    # 1) Парсинг из title+description, если сумм нет
    if salary_from is None and salary_to is None:
        text_blob = " ".join(
            p
            for p in (
                payload.get("title") or "",
                payload.get("description") or "",
            )
            if p
        )
        parsed = parse_salary(text_blob)
        if parsed is not None:
            payload.setdefault("salary_from", parsed.salary_from)
            payload.setdefault("salary_to", parsed.salary_to)
            payload["salary_currency"] = parsed.salary_currency
            payload["salary_period"] = parsed.salary_period
            if not payload.get("salary_gross_type"):
                payload["salary_gross_type"] = parsed.salary_gross_type
            payload["salary_from_rub"] = parsed.salary_from_rub
            payload["salary_to_rub"] = parsed.salary_to_rub
            return payload

    # 2) Период ≠ month → нормализация к месяцу
    if (salary_from or salary_to) and period and period != "month":
        salary_from, salary_to, period = normalize_period_to_month(
            salary_from, salary_to, period
        )
        payload["salary_from"] = salary_from
        payload["salary_to"] = salary_to
        payload["salary_period"] = period

    # 3) RUB-эквивалент при отсутствии явных rub-полей
    if payload.get("salary_from_rub") is None and payload.get("salary_to_rub") is None:
        sf_rub, st_rub = compute_rub_amounts(
            payload.get("salary_from"), payload.get("salary_to"), currency
        )
        payload["salary_from_rub"] = sf_rub
        payload["salary_to_rub"] = st_rub

    return payload


def upsert_canonical(db: Session, data: CanonicalVacancyIn) -> tuple[CanonicalVacancy, bool]:
    """Upsert canonical vacancy. Returns (record, created)."""
    payload = _enrich_salary_fields(data.model_dump())

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
        for key, value in payload.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False

    vacancy = CanonicalVacancy(**payload)
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


_WORD_SPLIT_RE = re.compile(r"\s+")


def _query_words(qt: str) -> list[str]:
    """Слова длины ≥2 из запроса, порядок сохранён, без дублей"""
    words: list[str] = []
    seen: set[str] = set()
    for raw in _WORD_SPLIT_RE.split(qt.strip()):
        w = raw.strip(" \t\n\"'`«»()[]{}.,!?:;").lower()
        if len(w) < 2 or w in seen:
            continue
        seen.add(w)
        words.append(w)
    return words


def _word_match_clause(word: str):
    """Подстрока без учёта регистра: title, company, description, location, skills"""
    pattern = f"%{word}%"
    return or_(
        func.lower(CanonicalVacancy.title).like(pattern),
        func.lower(CanonicalVacancy.company).like(pattern),
        func.lower(func.coalesce(CanonicalVacancy.description, "")).like(pattern),
        func.lower(func.coalesce(CanonicalVacancy.location, "")).like(pattern),
        func.lower(func.coalesce(CanonicalVacancy.location_city, "")).like(pattern),
        func.lower(
            func.coalesce(func.array_to_string(CanonicalVacancy.skills, " "), "")
        ).like(pattern),
    )


def _array_overlap(column, values: list[str], param_name: str):
    """`column && ARRAY[...]` для ARRAY/pg ARRAY"""
    bound = bindparam(param_name, value=values, type_=PG_ARRAY(String), unique=True)
    return column.op("&&")(bound)


def search_vacancies(db: Session, params: VacancySearchParams):
    q = db.query(CanonicalVacancy).filter(CanonicalVacancy.status == params.status)

    # Текстовый поиск: каждое слово ≥2 символов как подстрока (AND по словам); без стемминга
    qt = (params.query or params.title or params.q or "").strip()
    words: list[str] = []
    if qt:
        words = _query_words(qt)
        if not words:
            # Только короткие токены — один запрос как подстрока целиком
            q = q.filter(_word_match_clause(qt.lower()))
        else:
            for word in words:
                q = q.filter(_word_match_clause(word))

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
            _array_overlap(CanonicalVacancy.work_format, params.work_format, "wf"),
        )

    if params.employment_type:
        q = q.filter(
            CanonicalVacancy.employment_type.isnot(None),
            _array_overlap(CanonicalVacancy.employment_type, params.employment_type, "et"),
        )

    if params.schedule_type:
        q = q.filter(CanonicalVacancy.schedule_type.in_(params.schedule_type))

    if params.experience_level:
        q = q.filter(CanonicalVacancy.experience_level == params.experience_level)

    if params.salary_from is not None:
        # «От» в рублях против salary_*_rub (любая исходная валюта)
        q = q.filter(
            or_(
                CanonicalVacancy.salary_from_rub >= params.salary_from,
                CanonicalVacancy.salary_to_rub >= params.salary_from,
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
                CanonicalVacancy.salary_from_rub.isnot(None),
                CanonicalVacancy.salary_to_rub.isnot(None),
                CanonicalVacancy.salary_from.isnot(None),
                CanonicalVacancy.salary_to.isnot(None),
            )
        )

    if params.source_id:
        q = q.filter(CanonicalVacancy.source_id == params.source_id)

    if params.seniority:
        q = q.filter(CanonicalVacancy.seniority == params.seniority)

    total = q.count()
    pages = max(1, math.ceil(total / params.page_size))
    offset = (params.page - 1) * params.page_size

    sort_mode = (params.sort or "relevance").lower()
    order_clauses = _build_order_clauses(sort_mode, qt, words)

    items = (
        q.order_by(*order_clauses)
        .offset(offset)
        .limit(params.page_size)
        .all()
    )

    return items, total, pages


def _build_order_clauses(sort_mode: str, query_text: str, query_words: list[str]):
    """ORDER BY: date | salary (через RUB) | relevance (первое слово в title)"""
    sort_mode = sort_mode if sort_mode in {"relevance", "date", "salary"} else "relevance"

    if sort_mode == "date":
        return [CanonicalVacancy.published_at.desc().nullslast()]

    if sort_mode == "salary":
        # Зарплата: сравнение по RUB, иначе USD/EUR «внизу» из-за сырых чисел
        salary_expr = func.coalesce(
            CanonicalVacancy.salary_to_rub,
            CanonicalVacancy.salary_from_rub,
            CanonicalVacancy.salary_to,
            CanonicalVacancy.salary_from,
        )
        return [
            salary_expr.desc().nullslast(),
            CanonicalVacancy.published_at.desc().nullslast(),
        ]

    # relevance
    if query_text and query_words:
        first_word = f"%{query_words[0]}%"
        title_match_score = case(
            (func.lower(CanonicalVacancy.title).like(first_word), literal(0, type_=Integer())),
            else_=literal(1, type_=Integer()),
        )
        return [
            title_match_score.asc(),
            CanonicalVacancy.published_at.desc().nullslast(),
        ]

    return [CanonicalVacancy.published_at.desc().nullslast()]


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
    # TRUNCATE: сначала canonical (CASCADE на dedup_log), потом raw
    db.execute(text("TRUNCATE TABLE canonical_vacancies RESTART IDENTITY CASCADE"))
    db.execute(text("TRUNCATE TABLE raw_vacancies RESTART IDENTITY CASCADE"))
    db.commit()
    return raw_count, canonical_count
