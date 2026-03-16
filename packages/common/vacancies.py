from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class VacancySourceConfig(BaseModel):
    source_id: UUID = Field(default_factory=uuid4)
    name: str
    source_type: Literal["api", "html", "telegram"]
    schedule: str
    ttl_hours: int = 24
    enabled: bool = True


class RawVacancyPayload(BaseModel):
    raw_id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    external_id: str
    canonical_url: str
    payload: dict[str, Any] = Field(default_factory=dict)


class CanonicalVacancy(BaseModel):
    vacancy_id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    title: str
    company: str
    canonical_url: str
    location: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None
    status: Literal["new", "active", "expired", "archived", "blocked"] = "new"
    skills: list[str] = Field(default_factory=list)


class DeduplicationCandidate(BaseModel):
    primary_vacancy_id: UUID
    duplicate_vacancy_id: UUID
    similarity_score: float
