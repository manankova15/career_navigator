"""
Input/output contracts for the ML service.
All data arrives via HTTP — the service is stateless (no DB).
"""

from datetime import datetime
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
    headline: str | None = None
    summary: str | None = None
    liked_skills_top: list[str] = Field(default_factory=list)
    liked_titles: list[str] = Field(default_factory=list)
    total_likes: int = 0


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
    description: str | None = None
    published_at: datetime | None = None


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


# ── Hybrid ranking ─────────────────────────────────────────────────────────────

class RankRequest(BaseModel):
    """Re-rank content-scored vacancies with LightGBM."""
    profile: UserProfileInput
    vacancies: list[VacancyInput]
    content_results: list[ScoredVacancy]
    user_stats: dict[str, float] | None = None
    vacancy_stats: dict[str, dict[str, float]] | None = None


class RankedVacancy(ScoredVacancy):
    """Scored vacancy with ML layer."""
    ml_score: float = Field(ge=0.0, le=1.0)
    content_score: float = Field(ge=0.0, le=1.0)
    rank_explanation: list[str] = Field(default_factory=list)


class RankResponse(BaseModel):
    user_id: UUID
    algorithm: str = "hybrid_lgb_v1"
    total_ranked: int
    results: list[RankedVacancy]
    used_ml_model: bool = True
