from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from .schemas import EducationIn, ProfileIn, ProfilePreferenceIn, ProfileSkillIn, WorkExperienceIn


class ResumeFileOut(BaseModel):
    id: UUID
    user_id: UUID
    original_name: str
    mime_type: str
    extension: str
    size: int
    sha256: str
    source_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ResumeParseJobOut(BaseModel):
    id: UUID
    resume_file_id: UUID
    status: str
    error_message: str | None
    parser_version: str
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class ResumeParseResultOut(BaseModel):
    id: UUID
    resume_file_id: UUID
    is_hh_resume: bool
    hh_confidence_score: float
    warnings: list[str] = Field(default_factory=list)
    sections_detected: list[str] = Field(default_factory=list)
    parsed: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class ProfileImportDraftOut(BaseModel):
    id: UUID
    user_id: UUID
    resume_file_id: UUID
    draft_json: dict[str, Any]
    field_confidence_json: dict[str, Any] | None
    status: str
    created_at: datetime
    applied_at: datetime | None

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    resume_file: ResumeFileOut
    parse_job: ResumeParseJobOut


class ResumeStatusBundle(BaseModel):
    """Latest parse job + result for a file (if any)."""

    resume_file: ResumeFileOut
    parse_job: ResumeParseJobOut | None = None
    parse_result: ResumeParseResultOut | None = None
    draft: ProfileImportDraftOut | None = None


class ApplyResumeDraftIn(BaseModel):
    profile: ProfileIn | None = None
    preferences: ProfilePreferenceIn | None = None
    skills: list[ProfileSkillIn] | None = None
    skills_mode: Literal["none", "append", "replace"] = "append"
    work_experience: list[WorkExperienceIn] | None = None
    work_experience_mode: Literal["none", "append", "replace"] = "append"
    education: list[EducationIn] | None = None
    education_mode: Literal["none", "append", "replace"] = "append"


class ApplyResumeDraftResponse(BaseModel):
    draft_id: UUID
    status: str
    message: str = "Изменения применены к профилю."
