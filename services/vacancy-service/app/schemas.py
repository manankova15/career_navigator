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
    currency: str | None = "RUB"
    seniority: str | None = None
    employment_type: str | None = None
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
    currency: str | None
    seniority: str | None
    employment_type: str | None
    description: str | None
    skills: list[str]
    status: str
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VacancySearchParams(BaseModel):
    q: str | None = Field(None, description="Full-text search query")
    location: str | None = None
    seniority: str | None = None
    salary_from: int | None = None
    skills: list[str] = Field(default_factory=list)
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
