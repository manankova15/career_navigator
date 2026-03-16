"""
Input/output contracts for the ML service.
All data arrives via HTTP — the service is stateless (no DB).
"""

from uuid import UUID

from pydantic import BaseModel, Field


# ── Inputs ────────────────────────────────────────────────────────────────────

class UserProfileInput(BaseModel):
    """Subset of the career profile needed for scoring."""
    user_id: UUID
    skills: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    work_formats: list[str] = Field(default_factory=list)    # remote, office, hybrid
    target_roles: list[str] = Field(default_factory=list)
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None                              # intern/junior/middle/senior/lead


class VacancyInput(BaseModel):
    """Minimal vacancy representation for scoring."""
    vacancy_id: UUID
    title: str
    company: str
    location: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None
    skills: list[str] = Field(default_factory=list)
    employment_type: str | None = None


class ScoreRequest(BaseModel):
    profile: UserProfileInput
    vacancies: list[VacancyInput]


class SkillGapRequest(BaseModel):
    profile: UserProfileInput
    # Vacancies used as the "target market" for gap analysis
    # (typically the top-scored recommendations)
    target_vacancies: list[VacancyInput]


# ── Outputs ───────────────────────────────────────────────────────────────────

class ScoredVacancy(BaseModel):
    vacancy_id: UUID
    score: float = Field(ge=0.0, le=1.0)
    skill_score: float
    location_score: float
    salary_score: float
    seniority_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]


class ScoreResponse(BaseModel):
    user_id: UUID
    algorithm: str = "content_v1"
    total_scored: int
    results: list[ScoredVacancy]


class SkillGapItem(BaseModel):
    skill_name: str
    importance_score: float = Field(ge=0.0, le=1.0)
    # how many of the target vacancies require this skill
    frequency: int
    recommended_resources: list[str] = Field(default_factory=list)


class SkillGapResponse(BaseModel):
    user_id: UUID
    total_target_vacancies: int
    gaps: list[SkillGapItem]
