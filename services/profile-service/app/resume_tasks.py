"""Background resume parsing."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import ProfileImportDraft, ResumeFile, ResumeParseJob, ResumeParseResult
from .resume.pipeline import run_resume_pipeline

logger = logging.getLogger(__name__)


def _job_terminal_status(confidence: float) -> str:
    if confidence < 0.45:
        return "invalid"
    return "parsed"


def process_resume_parse_job(job_id: UUID, storage_abs_path: str) -> None:
    db: Session = SessionLocal()
    try:
        job = db.query(ResumeParseJob).filter(ResumeParseJob.id == job_id).first()
        if not job:
            return
        if job.status != "pending":
            return
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()

        path = Path(storage_abs_path)
        if not path.is_file():
            job.status = "failed"
            job.error_message = "Файл не найден на диске"
            job.finished_at = datetime.utcnow()
            db.commit()
            return

        result = run_resume_pipeline(path)
        confidence = float(result["confidence"])
        parsed = result["parsed"]
        warnings = result.get("warnings") or []

        pr = ResumeParseResult(
            resume_file_id=job.resume_file_id,
            is_hh_resume=bool(result["is_hh_resume"]),
            hh_confidence_score=confidence,
            raw_text=result.get("raw_text"),
            normalized_text=result.get("normalized_text"),
            parsed_json=parsed,
            warnings_json=warnings,
        )
        db.add(pr)

        job.status = _job_terminal_status(confidence)
        job.finished_at = datetime.utcnow()
        job.error_message = None

        if confidence >= 0.45:
            rf = db.query(ResumeFile).filter(ResumeFile.id == job.resume_file_id).first()
            user_id = rf.user_id if rf else None
            if user_id:
                draft_body = {
                    "parsed": parsed,
                    "parseMeta": {
                        "extractionMethod": result.get("extraction_method"),
                        "sectionsDetected": result.get("sections_detected", []),
                        "canAutofill": confidence >= 0.45,
                        "needsReview": confidence < 0.75,
                    },
                }
                draft = ProfileImportDraft(
                    user_id=user_id,
                    resume_file_id=job.resume_file_id,
                    draft_json=draft_body,
                    field_confidence_json=result.get("field_confidence"),
                    status="draft",
                )
                db.add(draft)

        db.commit()
    except Exception as e:
        logger.exception("Resume parse failed: %s", e)
        try:
            job = db.query(ResumeParseJob).filter(ResumeParseJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)[:2000]
                job.finished_at = datetime.utcnow()
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()
