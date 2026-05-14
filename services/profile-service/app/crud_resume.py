from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from .config import settings
from .crud import (
    add_education,
    add_profile_skill,
    add_work_experience,
    delete_profile_skill,
    delete_work_experience,
    get_or_create_profile,
    list_profile_skills,
    list_work_experiences,
    upsert_preferences,
    upsert_profile,
)
from .models import (
    Education,
    ProfileImportAuditLog,
    ProfileImportDraft,
    ResumeFile,
    ResumeParseJob,
    ResumeParseResult,
    Skill,
)
from .schemas import ProfileIn
from .schemas_resume import ApplyResumeDraftIn


ALLOWED_RESUME_EXT = {".pdf"}
ALLOWED_MIME = {"application/pdf", "application/x-pdf"}


def _audit(db: Session, user_id: UUID, resume_file_id: UUID | None, draft_id: UUID | None, field: str, old: Any, new: Any):
    db.add(
        ProfileImportAuditLog(
            user_id=user_id,
            resume_file_id=resume_file_id,
            draft_id=draft_id,
            field_name=field,
            old_value=None if old is None else str(old)[:8000],
            new_value=None if new is None else str(new)[:8000],
            source="hh_resume_import",
        )
    )


def create_resume_upload(
    db: Session,
    user_id: UUID,
    original_name: str,
    mime_type: str,
    data: bytes,
) -> tuple[ResumeFile, ResumeParseJob, Path]:
    if len(data) > settings.resume_max_upload_bytes:
        raise ValueError("Файл слишком большой")
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_RESUME_EXT:
        raise ValueError("Допустим только PDF")
    if mime_type not in ALLOWED_MIME and not original_name.lower().endswith(".pdf"):
        raise ValueError("Неверный тип файла")

    h = hashlib.sha256(data).hexdigest()
    base = Path(settings.resume_storage_dir)
    user_dir = base / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    fid = uuid4()
    storage_rel = f"{user_id}/{fid}{ext}"
    abs_path = base / str(user_id) / f"{fid}{ext}"
    abs_path.write_bytes(data)

    rf = ResumeFile(
        id=fid,
        user_id=user_id,
        original_name=original_name[:512],
        mime_type=mime_type[:128] or "application/pdf",
        extension=ext,
        size=len(data),
        storage_path=storage_rel.replace("\\", "/"),
        sha256=h,
        source_type="hh_resume",
    )
    db.add(rf)
    db.flush()

    job = ResumeParseJob(
        resume_file_id=rf.id,
        status="pending",
        parser_version=settings.resume_parser_version,
    )
    db.add(job)
    db.commit()
    db.refresh(rf)
    db.refresh(job)
    return rf, job, abs_path


def list_resume_files(db: Session, user_id: UUID) -> list[ResumeFile]:
    return (
        db.query(ResumeFile)
        .filter(ResumeFile.user_id == user_id)
        .order_by(ResumeFile.uploaded_at.desc())
        .all()
    )


def get_resume_file(db: Session, user_id: UUID, file_id: UUID) -> ResumeFile | None:
    return (
        db.query(ResumeFile)
        .filter(ResumeFile.id == file_id, ResumeFile.user_id == user_id)
        .first()
    )


def get_parse_job(db: Session, user_id: UUID, job_id: UUID) -> ResumeParseJob | None:
    job = db.query(ResumeParseJob).filter(ResumeParseJob.id == job_id).first()
    if not job:
        return None
    rf = db.query(ResumeFile).filter(ResumeFile.id == job.resume_file_id).first()
    if not rf or rf.user_id != user_id:
        return None
    return job


def get_latest_result_for_file(db: Session, file_id: UUID) -> ResumeParseResult | None:
    return (
        db.query(ResumeParseResult)
        .filter(ResumeParseResult.resume_file_id == file_id)
        .order_by(ResumeParseResult.created_at.desc())
        .first()
    )


def get_draft_for_file(db: Session, user_id: UUID, file_id: UUID) -> ProfileImportDraft | None:
    return (
        db.query(ProfileImportDraft)
        .filter(
            ProfileImportDraft.resume_file_id == file_id,
            ProfileImportDraft.user_id == user_id,
        )
        .order_by(ProfileImportDraft.created_at.desc())
        .first()
    )


def get_draft_by_id(db: Session, user_id: UUID, draft_id: UUID) -> ProfileImportDraft | None:
    d = db.query(ProfileImportDraft).filter(ProfileImportDraft.id == draft_id).first()
    if not d or d.user_id != user_id:
        return None
    return d


def apply_resume_draft(
    db: Session,
    user_id: UUID,
    draft_id: UUID,
    payload: ApplyResumeDraftIn,
) -> ProfileImportDraft:
    draft = get_draft_by_id(db, user_id, draft_id)
    if not draft:
        raise LookupError("Черновик не найден")
    if draft.status != "draft":
        raise ValueError("Черновик уже применён или отменён")

    profile = get_or_create_profile(db, user_id)
    resume_file_id = draft.resume_file_id

    if payload.profile is not None:
        dump = payload.profile.model_dump(exclude_none=True)
        old_vals = {k: getattr(profile, k, None) for k in dump}
        updated = upsert_profile(db, user_id, payload.profile)
        for key in dump:
            if getattr(updated, key, None) != old_vals.get(key):
                _audit(db, user_id, resume_file_id, draft_id, f"profile.{key}", old_vals.get(key), getattr(updated, key, None))

    if payload.preferences is not None:
        prefs_before = profile.preferences
        old_json = None
        if prefs_before:
            cols = [c.name for c in prefs_before.__table__.columns if c.name not in ("id", "profile_id")]
            old_json = json.dumps({k: getattr(prefs_before, k) for k in cols}, default=str)
        upsert_preferences(db, user_id, payload.preferences)
        _audit(db, user_id, resume_file_id, draft_id, "preferences", old_json, "updated")

    if payload.skills_mode != "none" and payload.skills:
        # Фильтруем навыки из резюме по канонической базе (таблица `skills`):
        # в профиль добавляем только те, чьё нормализованное имя уже есть в базе.
        # Сравнение регистронезависимое.
        known_normalized: set[str] = {
            row[0] for row in db.query(Skill.normalized_name).all() if row[0]
        }
        filtered_skills = [
            s for s in payload.skills
            if (s.skill_name or "").strip().lower() in known_normalized
        ]
        if payload.skills_mode == "replace":
            for sid in [ps.id for ps in list_profile_skills(db, user_id)]:
                delete_profile_skill(db, user_id, sid)
        for s in filtered_skills:
            add_profile_skill(db, user_id, s)

    if payload.work_experience_mode != "none" and payload.work_experience:
        if payload.work_experience_mode == "replace":
            for eid in [we.id for we in list_work_experiences(db, user_id)]:
                delete_work_experience(db, user_id, eid)
        for we in payload.work_experience:
            add_work_experience(db, user_id, we)

    if payload.education_mode != "none" and payload.education:
        if payload.education_mode == "replace":
            db.query(Education).filter(Education.profile_id == profile.id).delete()
        for ed in payload.education:
            add_education(db, user_id, ed)

    draft.status = "applied"
    draft.applied_at = datetime.utcnow()
    db.commit()
    db.refresh(draft)
    return draft
