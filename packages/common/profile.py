from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProfilePreference(BaseModel):
    preferred_locations: list[str] = Field(default_factory=list)
    work_formats: list[str] = Field(default_factory=list)
    salary_expectation_from: int | None = None
    salary_expectation_to: int | None = None
    target_roles: list[str] = Field(default_factory=list)


class ProfileSkill(BaseModel):
    profile_skill_id: UUID = Field(default_factory=uuid4)
    skill_name: str
    self_assessed_level: int = 1
    confirmed: bool = False


class CareerProfile(BaseModel):
    user_id: UUID
    headline: str
    summary: str | None = None
    preference: ProfilePreference = Field(default_factory=ProfilePreference)
    skills: list[ProfileSkill] = Field(default_factory=list)
