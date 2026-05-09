"""Resume import HTTP surface with CRUD patched."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.deps import get_current_user_id
from app.main import app


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def api_client(user_id, tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path / "rs"))

    def _db():
        yield MagicMock()

    app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[get_db] = _db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_upload_resume(api_client, user_id, tmp_path):
    rf = MagicMock()
    rf.id = uuid4()
    rf.user_id = user_id
    rf.original_name = "cv.pdf"
    rf.mime_type = "application/pdf"
    rf.extension = ".pdf"
    rf.size = 4
    rf.sha256 = "0" * 64
    rf.source_type = "hh_resume"
    rf.uploaded_at = MagicMock()

    job = MagicMock()
    job.id = uuid4()
    job.resume_file_id = rf.id
    job.status = "pending"
    job.error_message = None
    job.parser_version = "1"
    job.started_at = None
    job.finished_at = None

    pdf_path = tmp_path / "up.pdf"
    pdf_path.write_bytes(b"%PDF")

    with patch(
        "app.routers.resume_import.create_resume_upload",
        return_value=(rf, job, pdf_path),
    ):
        with patch("app.routers.resume_import.process_resume_parse_job"):
            files = {"file": ("cv.pdf", b"%PDF", "application/pdf")}
            r = api_client.post(
                "/profiles/me/resume/upload",
                headers={"Authorization": "Bearer x"},
                files=files,
            )
    assert r.status_code == 200
    body = r.json()
    assert body["resume_file"]["id"] == str(rf.id)


def test_upload_bad_file_returns_400(api_client):
    with patch(
        "app.routers.resume_import.create_resume_upload",
        side_effect=ValueError("Допустим только PDF"),
    ):
        files = {"file": ("cv.bin", b"x", "application/octet-stream")}
        r = api_client.post(
            "/profiles/me/resume/upload",
            headers={"Authorization": "Bearer x"},
            files=files,
        )
    assert r.status_code == 400


def test_list_files(api_client, user_id):
    rf = MagicMock()
    rf.id = uuid4()
    rf.user_id = user_id
    rf.original_name = "a.pdf"
    rf.mime_type = "application/pdf"
    rf.extension = ".pdf"
    rf.size = 1
    rf.sha256 = "1" * 64
    rf.source_type = "hh_resume"
    rf.uploaded_at = MagicMock()

    with patch("app.routers.resume_import.list_resume_files", return_value=[rf]):
        r = api_client.get("/profiles/me/resume/files", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_file_status_and_errors(api_client, user_id):
    fid = uuid4()
    rf = MagicMock()
    rf.id = fid
    rf.user_id = user_id
    rf.original_name = "a.pdf"
    rf.mime_type = "application/pdf"
    rf.extension = ".pdf"
    rf.size = 1
    rf.sha256 = "1" * 64
    rf.source_type = "hh_resume"
    rf.uploaded_at = MagicMock()

    pr = MagicMock()
    pr.id = uuid4()
    pr.resume_file_id = fid
    pr.is_hh_resume = True
    pr.hh_confidence_score = 0.9
    pr.warnings_json = None
    pr.parsed_json = {"rawSectionsDetected": ["contacts"]}

    pj = MagicMock()
    pj.id = uuid4()
    pj.resume_file_id = fid
    pj.status = "parsed"
    pj.error_message = None
    pj.parser_version = "1"
    pj.started_at = None
    pj.finished_at = None

    mock_db = MagicMock()
    q = MagicMock()
    q.filter.return_value.order_by.return_value.first.return_value = pj
    mock_db.query.return_value = q

    def _db():
        yield mock_db

    app.dependency_overrides[get_db] = _db

    with patch("app.routers.resume_import.get_resume_file", return_value=rf):
        with patch("app.routers.resume_import.get_latest_result_for_file", return_value=pr):
            with patch("app.routers.resume_import.get_draft_for_file", return_value=None):
                with TestClient(app) as client:
                    r = client.get(
                        f"/profiles/me/resume/files/{fid}/status",
                        headers={"Authorization": "Bearer x"},
                    )
    assert r.status_code == 200

    app.dependency_overrides.pop(get_db, None)

    with patch("app.routers.resume_import.get_resume_file", return_value=None):
        r = api_client.get(
            f"/profiles/me/resume/files/{uuid4()}/status",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 404


def test_parse_job_and_draft(api_client, user_id):
    jid = uuid4()
    job = MagicMock()
    job.id = jid
    job.resume_file_id = uuid4()
    job.status = "pending"
    job.error_message = None
    job.parser_version = "1"
    job.started_at = None
    job.finished_at = None

    with patch("app.routers.resume_import.get_parse_job", return_value=job):
        r = api_client.get(
            f"/profiles/me/resume/parse-jobs/{jid}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 200

    with patch("app.routers.resume_import.get_parse_job", return_value=None):
        r = api_client.get(
            f"/profiles/me/resume/parse-jobs/{uuid4()}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 404

    did = uuid4()
    draft = MagicMock()
    draft.id = did
    draft.user_id = user_id
    draft.resume_file_id = uuid4()
    draft.draft_json = {"parsed": {}}
    draft.field_confidence_json = None
    draft.status = "draft"
    draft.created_at = MagicMock()
    draft.applied_at = None

    with patch("app.routers.resume_import.get_draft_by_id", return_value=draft):
        r = api_client.get(
            f"/profiles/me/resume/drafts/{did}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 200

    with patch("app.routers.resume_import.get_draft_by_id", return_value=None):
        r = api_client.get(
            f"/profiles/me/resume/drafts/{uuid4()}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 404


def test_apply_draft(api_client):
    did = uuid4()
    with patch("app.routers.resume_import.apply_resume_draft"):
        r = api_client.post(
            f"/profiles/me/resume/drafts/{did}/apply",
            headers={"Authorization": "Bearer x"},
            json={"skills_mode": "none"},
        )
    assert r.status_code == 200

    with patch("app.routers.resume_import.apply_resume_draft", side_effect=LookupError):
        r = api_client.post(
            f"/profiles/me/resume/drafts/{did}/apply",
            headers={"Authorization": "Bearer x"},
            json={"skills_mode": "none"},
        )
    assert r.status_code == 404

    with patch("app.routers.resume_import.apply_resume_draft", side_effect=ValueError("bad")):
        r = api_client.post(
            f"/profiles/me/resume/drafts/{did}/apply",
            headers={"Authorization": "Bearer x"},
            json={"skills_mode": "none"},
        )
    assert r.status_code == 400
