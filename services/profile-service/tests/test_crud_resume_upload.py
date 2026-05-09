"""create_resume_upload validation and happy path (in-memory session)."""

from pathlib import Path
from uuid import uuid4

import pytest

from app import crud_resume
from app.crud_resume import create_resume_upload


class _MemSession:
    def __init__(self) -> None:
        self.added: list = []

    def add(self, obj) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        pass

    def refresh(self, _obj) -> None:
        pass


@pytest.fixture
def storage_dir(tmp_path, monkeypatch):
    d = tmp_path / "resumes"
    monkeypatch.setattr(crud_resume.settings, "resume_storage_dir", str(d))
    return d


def test_reject_oversized(storage_dir):
    db = _MemSession()
    big = b"x" * (crud_resume.settings.resume_max_upload_bytes + 1)
    with pytest.raises(ValueError, match="слишком большой"):
        create_resume_upload(db, uuid4(), "cv.pdf", "application/pdf", big)


def test_reject_wrong_extension(storage_dir):
    db = _MemSession()
    with pytest.raises(ValueError, match="только PDF"):
        create_resume_upload(db, uuid4(), "cv.doc", "application/pdf", b"%PDF")


def test_reject_bad_mime_when_name_does_not_end_with_pdf(storage_dir):
    db = _MemSession()
    with pytest.raises(ValueError, match="только PDF"):
        create_resume_upload(db, uuid4(), "cv.bin", "application/octet-stream", b"%PDF")


def test_accepts_pdf_extension_even_if_mime_weird(storage_dir):
    db = _MemSession()
    uid = uuid4()
    data = b"%PDF-1.4 minimal"
    rf, job, abs_path = create_resume_upload(db, uid, "cv.pdf", "application/octet-stream", data)
    assert rf.extension == ".pdf"
    assert abs_path.is_file()
    assert abs_path.read_bytes() == data
    assert job.status == "pending"
    assert len(db.added) == 2
