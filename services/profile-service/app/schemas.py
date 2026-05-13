from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileIn(BaseModel):
    full_name: str | None = Field(None, max_length=200)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    patronymic: str | None = Field(None, max_length=100)
    # Код города (CITIES)
    location: str | None = Field(None, max_length=64)
    # Код специализации (SPECIALIZATION_OPTIONS)
    specialization: str | None = Field(None, max_length=64)
    # Код области (PROFESSION_AREAS)
    target_industry: str | None = Field(None, max_length=64)


class ProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str | None
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    location: str | None
    specialization: str | None
    target_industry: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfilePreferenceIn(BaseModel):
    work_formats: list[str] = Field(default_factory=list)
    salary_from: int | None = None
    salary_to: int | None = None
    seniority: str | None = None


class ProfilePreferenceOut(ProfilePreferenceIn):
    id: UUID

    model_config = {"from_attributes": True}


class ProfileSkillIn(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    self_assessed_level: int = Field(default=1, ge=1, le=5)
    years_of_experience: int | None = None


class ProfileSkillOut(BaseModel):
    id: UUID
    skill_id: UUID
    skill_name: str
    self_assessed_level: int
    confirmed: bool
    years_of_experience: int | None

    model_config = {"from_attributes": True}


class WorkExperienceIn(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None


class WorkExperienceOut(WorkExperienceIn):
    id: UUID
    profile_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class EducationIn(BaseModel):
    institution: str = Field(min_length=1, max_length=200)
    degree: str | None = None
    field: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class EducationOut(EducationIn):
    id: UUID
    profile_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
