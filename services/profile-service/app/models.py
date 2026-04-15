import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    patronymic = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    target_role = Column(String(200), nullable=True)
    target_industry = Column(String(200), nullable=True)
    headline = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    preferences = relationship(
        "ProfilePreference",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )
    skills = relationship("ProfileSkill", back_populates="profile", cascade="all, delete-orphan")
    work_experiences = relationship(
        "WorkExperience", back_populates="profile", cascade="all, delete-orphan"
    )
    educations = relationship(
        "Education", back_populates="profile", cascade="all, delete-orphan"
    )


class ProfilePreference(Base):
    __tablename__ = "profile_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    preferred_locations = Column(ARRAY(String(100)), nullable=False, server_default="{}")
    work_formats = Column(ARRAY(String(50)), nullable=False, server_default="{}")
    target_roles = Column(ARRAY(String(100)), nullable=False, server_default="{}")
    salary_from = Column(Integer, nullable=True)
    salary_to = Column(Integer, nullable=True)
    seniority = Column(String(50), nullable=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    profile = relationship("Profile", back_populates="preferences")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    normalized_name = Column(String(100), nullable=False, unique=True)
    category = Column(String(100), nullable=True)

    profile_skills = relationship("ProfileSkill", back_populates="skill")


class ProfileSkill(Base):
    __tablename__ = "profile_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id = Column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    self_assessed_level = Column(Integer, nullable=False, server_default="1")  # 1-5
    confirmed = Column(Boolean, default=False, nullable=False)
    years_of_experience = Column(Integer, nullable=True)

    profile = relationship("Profile", back_populates="skills")
    skill = relationship("Skill", back_populates="profile_skills")


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    company = Column(String(200), nullable=False)
    title = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("Profile", back_populates="work_experiences")


class Education(Base):
    __tablename__ = "educations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    institution = Column(String(200), nullable=False)
    degree = Column(String(100), nullable=True)
    field = Column(String(100), nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("Profile", back_populates="educations")


class ResumeFile(Base):
    __tablename__ = "resume_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    original_name = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    extension = Column(String(16), nullable=False)
    size = Column(Integer, nullable=False)
    storage_path = Column(String(1024), nullable=False)
    sha256 = Column(String(64), nullable=False)
    source_type = Column(String(32), nullable=False, default="hh_resume")
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ResumeParseJob(Base):
    __tablename__ = "resume_parse_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_file_id = Column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(32), nullable=False)
    error_message = Column(Text, nullable=True)
    parser_version = Column(String(32), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)


class ResumeParseResult(Base):
    __tablename__ = "resume_parse_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_file_id = Column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False
    )
    is_hh_resume = Column(Boolean, nullable=False, default=False)
    hh_confidence_score = Column(Float, nullable=False, default=0.0)
    raw_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    parsed_json = Column(JSONB, nullable=True)
    warnings_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProfileImportDraft(Base):
    __tablename__ = "profile_import_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    resume_file_id = Column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False
    )
    draft_json = Column(JSONB, nullable=False)
    field_confidence_json = Column(JSONB, nullable=True)
    status = Column(String(32), nullable=False, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    applied_at = Column(DateTime, nullable=True)


class ProfileImportAuditLog(Base):
    __tablename__ = "profile_import_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    resume_file_id = Column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="SET NULL"), nullable=True
    )
    draft_id = Column(
        UUID(as_uuid=True), ForeignKey("profile_import_drafts.id", ondelete="SET NULL"), nullable=True
    )
    field_name = Column(String(256), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    source = Column(String(64), nullable=False, default="hh_resume_import")
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
