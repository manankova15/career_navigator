from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RawVacancyIn(BaseModel):
    source_id: UUID
    external_id: str
    canonical_url: str
    payload: dict[str, Any]


class RawVacancyOut(BaseModel):
    id: UUID
    source_id: UUID
    external_id: str
    canonical_url: str
    fetched_at: datetime
    processed: bool

    model_config = {"from_attributes": True}


class CanonicalVacancyIn(BaseModel):
    source_id: UUID
    external_id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    company: str = Field(min_length=1, max_length=300)
    canonical_url: str
    location: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    salary_currency: str | None = "RUB"
    seniority: str | None = None
    employment_type: list[str] | None = None
    work_format: list[str] = Field(default_factory=list)
    schedule_type: str | None = None
    experience_level: str | None = None
    salary_gross_type: str | None = None
    salary_period: str | None = None
    profession_area: str | None = None
    specialization: str | None = None
    location_country: str | None = None
    location_city: str | None = None
    education_level: str | None = None
    english_level: str | None = None
    company_industry: str | None = None
    source_name: str | None = None
    description: str | None = None
    skills: list[str] = Field(default_factory=list)
    status: str = "active"
    published_at: datetime | None = None
    expires_at: datetime | None = None


class CanonicalVacancyOut(BaseModel):
    id: UUID
    source_id: UUID
    external_id: str | None
    title: str
    company: str
    canonical_url: str
    location: str | None
    salary_from: int | None
    salary_to: int | None
    salary_currency: str | None
    seniority: str | None
    employment_type: list[str] | None
    work_format: list[str]
    schedule_type: str | None
    experience_level: str | None
    salary_gross_type: str | None
    salary_period: str | None
    profession_area: str | None
    specialization: str | None
    location_country: str | None
    location_city: str | None
    education_level: str | None
    english_level: str | None
    company_industry: str | None
    source_name: str | None
    description: str | None
    skills: list[str]
    status: str
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VacancySearchParams(BaseModel):
    """Параметры поиска по ТЗ (п. 7.2)."""

    query: str | None = Field(None, description="Текст: title, company, description, skills")
    title: str | None = Field(None, description="Legacy: подстрока в title")
    q: str | None = Field(None, description="Legacy: полнотекстовый запрос")
    profession_area: list[str] = Field(default_factory=list)
    specialization: str | None = None
    city: str | None = None
    country: str | None = None
    work_format: list[str] = Field(default_factory=list)
    employment_type: list[str] = Field(default_factory=list)
    schedule_type: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    salary_from: int | None = None
    salary_currency: str | None = None
    has_salary: bool | None = None
    skills: list[str] = Field(default_factory=list)
    english_level: str | None = None
    education_level: str | None = None
    published_within: str | None = Field(
        None,
        description="1d | 3d | 7d | 30d",
    )
    seniority: str | None = Field(None, description="Legacy: junior / middle / …")
    source_id: UUID | None = None
    status: str = "active"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class VacancyPage(BaseModel):
    items: list[CanonicalVacancyOut]
    total: int
    page: int
    page_size: int
    pages: int
