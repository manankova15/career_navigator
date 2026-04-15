from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..crud_resume import (
    apply_resume_draft,
    create_resume_upload,
    get_draft_by_id,
    get_draft_for_file,
    get_latest_result_for_file,
    get_parse_job,
    get_resume_file,
    list_resume_files,
)
from ..database import get_db
from ..deps import get_current_user_id
from ..models import ResumeParseJob, ResumeParseResult
from ..resume_tasks import process_resume_parse_job
from ..schemas_resume import (
    ApplyResumeDraftIn,
    ApplyResumeDraftResponse,
    ProfileImportDraftOut,
    ResumeFileOut,
    ResumeParseJobOut,
    ResumeParseResultOut,
    ResumeStatusBundle,
    ResumeUploadResponse,
)

# Mounted under profiles router with prefix "/me/resume" → full path /profiles/me/resume/*
router = APIRouter(tags=["resume-import"])


def _file_out(rf) -> ResumeFileOut:
    return ResumeFileOut.model_validate(rf)


def _job_out(j) -> ResumeParseJobOut:
    return ResumeParseJobOut.model_validate(j)


def _result_out(r: ResumeParseResult) -> ResumeParseResultOut:
    w = r.warnings_json
    if w is None:
        warnings: list[str] = []
    elif isinstance(w, list):
        warnings = [str(x) for x in w]
    else:
        warnings = [str(w)]
    parsed = r.parsed_json if isinstance(r.parsed_json, dict) else None
    sections: list[str] = []
    if parsed:
        sections = list(parsed.get("rawSectionsDetected") or [])
    return ResumeParseResultOut(
        id=r.id,
        resume_file_id=r.resume_file_id,
        is_hh_resume=r.is_hh_resume,
        hh_confidence_score=r.hh_confidence_score,
        warnings=warnings,
        sections_detected=sections,
        parsed=parsed,
    )


def _draft_out(d) -> ProfileImportDraftOut:
    return ProfileImportDraftOut.model_validate(d)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    data = await file.read()
    try:
        rf, job, abs_path = create_resume_upload(
            db,
            user_id,
            file.filename or "resume.pdf",
            file.content_type or "application/pdf",
            data,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    background_tasks.add_task(process_resume_parse_job, job.id, str(abs_path))
    return ResumeUploadResponse(resume_file=_file_out(rf), parse_job=_job_out(job))


@router.get("/files", response_model=list[ResumeFileOut])
def list_files(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return [_file_out(x) for x in list_resume_files(db, user_id)]


@router.get("/files/{file_id}/status", response_model=ResumeStatusBundle)
def file_status(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rf = get_resume_file(db, user_id, file_id)
    if not rf:
        raise HTTPException(status_code=404, detail="Файл не найден")
    pj = (
        db.query(ResumeParseJob)
        .filter(ResumeParseJob.resume_file_id == file_id)
        .order_by(ResumeParseJob.id.desc())
        .first()
    )
    pr = get_latest_result_for_file(db, file_id)
    draft = get_draft_for_file(db, user_id, file_id)
    return ResumeStatusBundle(
        resume_file=_file_out(rf),
        parse_job=_job_out(pj) if pj else None,
        parse_result=_result_out(pr) if pr else None,
        draft=_draft_out(draft) if draft else None,
    )


@router.get("/parse-jobs/{job_id}", response_model=ResumeParseJobOut)
def parse_job_status(
    job_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    job = get_parse_job(db, user_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return _job_out(job)


@router.get("/drafts/{draft_id}", response_model=ProfileImportDraftOut)
def get_draft(
    draft_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    d = get_draft_by_id(db, user_id, draft_id)
    if not d:
        raise HTTPException(status_code=404, detail="Черновик не найден")
    return _draft_out(d)


@router.post("/drafts/{draft_id}/apply", response_model=ApplyResumeDraftResponse)
def apply_draft(
    draft_id: UUID,
    body: ApplyResumeDraftIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        apply_resume_draft(db, user_id, draft_id, body)
    except LookupError:
        raise HTTPException(status_code=404, detail="Черновик не найден")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApplyResumeDraftResponse(draft_id=draft_id, status="applied")
