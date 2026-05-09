"""Background resume job processing with mocked DB and pipeline."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models import ResumeFile, ResumeParseJob
from app.resume_tasks import _job_terminal_status, process_resume_parse_job


def test_job_terminal_status():
    assert _job_terminal_status(0.1) == "invalid"
    assert _job_terminal_status(0.5) == "parsed"


def test_process_job_not_found():
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    with patch("app.resume_tasks.SessionLocal", return_value=session):
        process_resume_parse_job(uuid4(), "/tmp/x.pdf")
    session.close.assert_called_once()


def test_process_job_non_pending():
    jid = uuid4()
    job = MagicMock()
    job.id = jid
    job.status = "done"
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = job
    with patch("app.resume_tasks.SessionLocal", return_value=session):
        process_resume_parse_job(jid, "/tmp/x.pdf")
    session.commit.assert_not_called()
    session.close.assert_called_once()


def test_process_job_missing_file(tmp_path):
    job_id = uuid4()
    job = MagicMock(spec=ResumeParseJob)
    job.id = job_id
    job.status = "pending"
    job.resume_file_id = uuid4()

    session = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        if model is ResumeParseJob:
            q.filter.return_value.first.return_value = job
        return q

    session.query.side_effect = query_side_effect
    missing = tmp_path / "nope.pdf"

    with patch("app.resume_tasks.SessionLocal", return_value=session):
        process_resume_parse_job(job_id, str(missing))

    assert job.status == "failed"
    assert job.error_message
    session.close.assert_called_once()


def test_process_job_success_creates_draft(tmp_path):
    job_id = uuid4()
    file_id = uuid4()
    user_id = uuid4()

    job = MagicMock(spec=ResumeParseJob)
    job.id = job_id
    job.status = "pending"
    job.resume_file_id = file_id

    rf = MagicMock(spec=ResumeFile)
    rf.user_id = user_id

    pdf = tmp_path / "f.pdf"
    pdf.write_bytes(b"%PDF")

    pipeline_out = {
        "raw_text": "t",
        "normalized_text": "t",
        "extraction_method": "pypdf",
        "is_hh_resume": True,
        "confidence": 0.9,
        "warnings": [],
        "parsed": {"profile": {}, "rawSectionsDetected": ["contacts"]},
        "field_confidence": {},
        "sections_detected": ["contacts"],
    }

    session = MagicMock()
    calls = {"job_query": 0}

    def query_side_effect(model):
        q = MagicMock()
        if model is ResumeParseJob:
            q.filter.return_value.first.return_value = job
        elif model is ResumeFile:
            q.filter.return_value.first.return_value = rf
        return q

    session.query.side_effect = query_side_effect

    with patch("app.resume_tasks.SessionLocal", return_value=session):
        with patch("app.resume_tasks.run_resume_pipeline", return_value=pipeline_out):
            process_resume_parse_job(job_id, str(pdf))

    assert job.status == "parsed"
    session.add.assert_called()
    session.commit.assert_called()
    session.close.assert_called_once()


def test_process_job_pipeline_exception(tmp_path):
    job_id = uuid4()
    job = MagicMock(spec=ResumeParseJob)
    job.id = job_id
    job.status = "pending"
    job.resume_file_id = uuid4()

    pdf = tmp_path / "f.pdf"
    pdf.write_bytes(b"%PDF")

    session = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        if model is ResumeParseJob:
            q.filter.return_value.first.return_value = job
        return q

    session.query.side_effect = query_side_effect

    with patch("app.resume_tasks.SessionLocal", return_value=session):
        with patch("app.resume_tasks.run_resume_pipeline", side_effect=RuntimeError("boom")):
            process_resume_parse_job(job_id, str(pdf))

    assert job.status == "failed"
    assert "boom" in (job.error_message or "")


def test_process_job_exception_inner_commit_fails_triggers_rollback(tmp_path):
    job_id = uuid4()
    job = MagicMock(spec=ResumeParseJob)
    job.id = job_id
    job.status = "pending"
    job.resume_file_id = uuid4()

    pdf = tmp_path / "f.pdf"
    pdf.write_bytes(b"%PDF")

    session = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        if model is ResumeParseJob:
            q.filter.return_value.first.return_value = job
        return q

    session.query.side_effect = query_side_effect
    session.commit.side_effect = [None, RuntimeError("commit failed")]

    with patch("app.resume_tasks.SessionLocal", return_value=session):
        with patch("app.resume_tasks.run_resume_pipeline", side_effect=RuntimeError("pipeline")):
            process_resume_parse_job(job_id, str(pdf))

    session.rollback.assert_called_once()
