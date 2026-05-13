from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..crud import (
    expire_vacancies,
    get_unprocessed_raw,
    get_vacancy,
    ingest_raw,
    mark_raw_processed,
    search_vacancies,
    truncate_all_vacancies,
    upsert_canonical,
)
from ..database import get_db
from ..deps import require_admin
from ..schemas import (
    CanonicalVacancyIn,
    CanonicalVacancyOut,
    RawVacancyIn,
    RawVacancyOut,
    VacancyPage,
    VacancySearchParams,
)

router = APIRouter(tags=["vacancies"])


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


# ── Public search ────────────────────────────────────────────────────────────

@router.get("/vacancies", response_model=VacancyPage)
async def search(
    query: str | None = Query(None, description="Поиск по title, company, description, skills"),
    title: str | None = Query(None, description="Legacy: подстрока в названии"),
    q: str | None = Query(None, description="Legacy: полнотекстовый поиск"),
    profession_area: str | None = Query(
        None,
        description="CSV: it,analytics,finance",
    ),
    specialization: str | None = Query(None),
    city: str | None = Query(None),
    country: str | None = Query(None),
    location: str | None = Query(None, description="Alias для city (совместимость)"),
    work_format: str | None = Query(None, description="CSV: remote,hybrid,office,field"),
    employment_type: str | None = Query(
        None,
        description="CSV: full_time,part_time,contract,project,internship,temporary,volunteering",
    ),
    schedule_type: str | None = Query(
        None,
        description="CSV: full_day,flexible,shift,weekend,watch,custom",
    ),
    experience_level: str | None = Query(None),
    seniority: str | None = Query(None, description="Legacy: junior/middle/…"),
    salary_from: int | None = Query(None, ge=0),
    salary_currency: str | None = Query(None),
    has_salary: bool | None = Query(None),
    source_id: UUID | None = Query(None),
    sort: str = Query(
        "relevance",
        description="relevance | date | salary",
        pattern="^(relevance|date|salary)$",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    params = VacancySearchParams(
        query=query or None,
        title=title or None,
        q=q or None,
        profession_area=_split_csv(profession_area),
        specialization=specialization or None,
        city=(city or location or None),
        country=country or None,
        work_format=_split_csv(work_format),
        employment_type=_split_csv(employment_type),
        schedule_type=_split_csv(schedule_type),
        experience_level=experience_level or None,
        seniority=seniority or None,
        salary_from=salary_from,
        salary_currency=salary_currency or None,
        has_salary=has_salary,
        source_id=source_id,
        sort=sort or "relevance",
        page=page,
        page_size=page_size,
    )
    items, total, pages = search_vacancies(db, params)
    return VacancyPage(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/vacancies/{vacancy_id}", response_model=CanonicalVacancyOut)
async def get_by_id(vacancy_id: UUID, db: Session = Depends(get_db)):
    vacancy = get_vacancy(db, vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy


# ── Internal ingestion endpoints (called by ingestion-worker) ───────────────

@router.post("/internal/raw", response_model=RawVacancyOut, status_code=status.HTTP_201_CREATED)
async def ingest_raw_vacancy(
    data: RawVacancyIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    raw, _ = ingest_raw(db, data)
    return raw


@router.get("/internal/raw/unprocessed", response_model=list[RawVacancyOut])
async def list_unprocessed(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    return get_unprocessed_raw(db, limit=limit)


@router.post(
    "/internal/canonical",
    response_model=CanonicalVacancyOut,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_canonical_vacancy(
    data: CanonicalVacancyIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    vacancy, _ = upsert_canonical(db, data)
    return vacancy


@router.post("/internal/raw/{raw_id}/mark-processed", status_code=status.HTTP_204_NO_CONTENT)
async def mark_processed(
    raw_id: UUID,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    mark_raw_processed(db, raw_id)


@router.post("/internal/expire", tags=["admin"])
async def run_expiry(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    count = expire_vacancies(db)
    return {"expired": count}


@router.post("/internal/truncate", tags=["admin"])
async def truncate_vacancies(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Delete all raw and canonical vacancies (for full re-seed)."""
    raw_deleted, canonical_deleted = truncate_all_vacancies(db)
    return {"raw_deleted": raw_deleted, "canonical_deleted": canonical_deleted}
