"""
Input/output contracts for the ML service.
All data arrives via HTTP — the service is stateless (no DB, no external models).
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Inputs ────────────────────────────────────────────────────────────────────

class UserProfileInput(BaseModel):
    user_id: UUID
    skills: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    work_formats: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None
    headline: str | None = None
    summary: str | None = None
    # Derived from server-side interactions, passed to help the role_score
    # contextualise soft preferences (not used in base score — used only to
    # enrich the reasons payload if provided).
    liked_skills_top: list[str] = Field(default_factory=list)
    liked_titles: list[str] = Field(default_factory=list)
    total_likes: int = 0


class VacancyInput(BaseModel):
    vacancy_id: UUID
    title: str
    company: str
    location: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None
    skills: list[str] = Field(default_factory=list)
    employment_type: str | None = None
    description: str | None = None
    published_at: datetime | None = None


class ScoreRequest(BaseModel):
    profile: UserProfileInput
    vacancies: list[VacancyInput]


class SkillGapRequest(BaseModel):
    profile: UserProfileInput
    target_vacancies: list[VacancyInput]


# ── Outputs ───────────────────────────────────────────────────────────────────

class ScoredVacancy(BaseModel):
    vacancy_id: UUID
    score: float = Field(ge=0.0, le=1.0)
    skill_score: float
    role_score: float = 0.0
    location_score: float
    salary_score: float
    seniority_score: float
    format_score: float = 0.0
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]
    features: dict[str, Any] = Field(default_factory=dict)


class ScoreResponse(BaseModel):
    user_id: UUID
    algorithm: str = "content_ahp_v2"
    total_scored: int
    results: list[ScoredVacancy]


class SkillGapItem(BaseModel):
    skill_name: str
    importance_score: float = Field(ge=0.0, le=1.0)
    frequency: int
    recommended_resources: list[str] = Field(default_factory=list)


class SkillGapResponse(BaseModel):
    user_id: UUID
    total_target_vacancies: int
    gaps: list[SkillGapItem]
