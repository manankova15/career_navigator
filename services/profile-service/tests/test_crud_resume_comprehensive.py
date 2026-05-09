"""Tests for app.crud_resume (queries, apply draft, audit)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app import crud_resume
from app.crud_resume import (
    _audit,
    apply_resume_draft,
    create_resume_upload,
    get_draft_by_id,
    get_draft_for_file,
    get_latest_result_for_file,
    get_parse_job,
    get_resume_file,
)
from app.models import Education, ProfilePreference, ResumeParseJob
from app.schemas import EducationIn, ProfileIn, ProfilePreferenceIn, ProfileSkillIn, WorkExperienceIn
from app.schemas_resume import ApplyResumeDraftIn


def _q(first=None, all_list=None):
    m = MagicMock()
    m.filter.return_value = m
    m.order_by.return_value = m
    m.first.return_value = first
    if all_list is not None:
        m.all.return_value = all_list
    return m


def test_audit_adds_row(db):
    uid = uuid4()
    _audit(db, uid, None, None, "f", "old", "new")
    db.add.assert_called_once()
    row = db.add.call_args[0][0]
    assert row.field_name == "f"
    assert row.old_value == "old"
    assert row.new_value == "new"


def test_list_resume_files(db):
    rf = MagicMock()
    db.query.return_value = _q(all_list=[rf])
    assert crud_resume.list_resume_files(db, uuid4()) == [rf]


def test_get_resume_file(db):
    rf = MagicMock()
    db.query.return_value = _q(first=rf)
    assert crud_resume.get_resume_file(db, uuid4(), uuid4()) is rf


def test_get_latest_result_for_file(db):
    pr = MagicMock()
    db.query.return_value = _q(first=pr)
    assert get_latest_result_for_file(db, uuid4()) is pr


def test_get_draft_for_file(db):
    d = MagicMock()
    db.query.return_value = _q(first=d)
    assert get_draft_for_file(db, uuid4(), uuid4()) is d


def test_get_parse_job_missing_job(db):
    db.query.return_value = _q(first=None)
    assert get_parse_job(db, uuid4(), uuid4()) is None


def test_get_parse_job_wrong_resume_owner(db):
    job = MagicMock()
    job.resume_file_id = uuid4()
    rf = MagicMock()
    rf.user_id = uuid4()

    def q(model):
        qq = MagicMock()
        qq.filter.return_value = qq
        qq.first.return_value = job if model is ResumeParseJob else rf
        return qq

    db.query.side_effect = q
    assert get_parse_job(db, uuid4(), job.id) is None


def test_get_parse_job_ok(db):
    uid = uuid4()
    job = MagicMock()
    job.resume_file_id = uuid4()
    rf = MagicMock()
    rf.user_id = uid

    def q(model):
        qq = MagicMock()
        qq.filter.return_value = qq
        qq.first.return_value = job if model is ResumeParseJob else rf
        return qq

    db.query.side_effect = q
    assert get_parse_job(db, uid, job.id) is job


def test_get_draft_by_id_missing_or_wrong_user(db):
    db.query.return_value = _q(first=None)
    assert get_draft_by_id(db, uuid4(), uuid4()) is None
    d = MagicMock()
    d.user_id = uuid4()
    db.query.return_value = _q(first=d)
    assert get_draft_by_id(db, uuid4(), d.id) is None


def test_get_draft_by_id_ok(db):
    uid = uuid4()
    d = MagicMock()
    d.user_id = uid
    db.query.return_value = _q(first=d)
    assert get_draft_by_id(db, uid, d.id) is d


def test_apply_draft_not_found():
    db = MagicMock()
    with patch("app.crud_resume.get_draft_by_id", return_value=None):
        with pytest.raises(LookupError):
            apply_resume_draft(db, uuid4(), uuid4(), ApplyResumeDraftIn())


def test_apply_draft_bad_status():
    db = MagicMock()
    draft = MagicMock()
    draft.status = "applied"
    with patch("app.crud_resume.get_draft_by_id", return_value=draft):
        with pytest.raises(ValueError, match="применён"):
            apply_resume_draft(db, uuid4(), draft.id, ApplyResumeDraftIn())


def test_apply_draft_profile_change_triggers_audit(db):
    uid = uuid4()
    did = uuid4()
    draft = MagicMock()
    draft.status = "draft"
    draft.id = did
    draft.resume_file_id = uuid4()

    profile = MagicMock()
    profile.id = uuid4()
    profile.full_name = "Old"
    profile.preferences = None

    updated = MagicMock()
    updated.full_name = "New"

    with patch("app.crud_resume.get_draft_by_id", return_value=draft):
        with patch("app.crud_resume.get_or_create_profile", return_value=profile):
            with patch("app.crud_resume.upsert_profile", return_value=updated):
                apply_resume_draft(
                    db,
                    uid,
                    did,
                    ApplyResumeDraftIn(profile=ProfileIn(full_name="New")),
                )

    db.add.assert_called()
    db.commit.assert_called()
    db.refresh.assert_called_with(draft)


def test_apply_draft_preferences_with_existing_prefs(db):
    uid = uuid4()
    draft = MagicMock()
    draft.status = "draft"
    draft.id = uuid4()
    draft.resume_file_id = uuid4()

    prefs_before = ProfilePreference(
        profile_id=uuid4(),
        preferred_locations=[],
        work_formats=[],
        target_roles=[],
        salary_from=50,
    )

    profile = MagicMock()
    profile.id = uuid4()
    profile.preferences = prefs_before

    with patch("app.crud_resume.get_draft_by_id", return_value=draft):
        with patch("app.crud_resume.get_or_create_profile", return_value=profile):
            with patch("app.crud_resume.upsert_preferences"):
                apply_resume_draft(
                    db,
                    uid,
                    draft.id,
                    ApplyResumeDraftIn(preferences=ProfilePreferenceIn(salary_from=200)),
                )

    db.add.assert_called()


def test_apply_draft_skills_replace(db):
    uid = uuid4()
    draft = MagicMock()
    draft.status = "draft"
    draft.id = uuid4()
    draft.resume_file_id = uuid4()
    profile = MagicMock()
    profile.id = uuid4()
    profile.preferences = None
    ps = MagicMock()
    ps.id = uuid4()

    with patch("app.crud_resume.get_draft_by_id", return_value=draft):
        with patch("app.crud_resume.get_or_create_profile", return_value=profile):
            with patch("app.crud_resume.list_profile_skills", return_value=[ps]):
                with patch("app.crud_resume.delete_profile_skill", return_value=True) as del_s:
                    with patch("app.crud_resume.add_profile_skill") as add_s:
                        apply_resume_draft(
                            db,
                            uid,
                            draft.id,
                            ApplyResumeDraftIn(
                                skills_mode="replace",
                                skills=[ProfileSkillIn(skill_name="Go", self_assessed_level=3)],
                            ),
                        )
    del_s.assert_called_once()
    add_s.assert_called_once()


def test_apply_draft_skills_append(db):
    uid = uuid4()
    draft = MagicMock()
    draft.status = "draft"
    draft.id = uuid4()
    draft.resume_file_id = uuid4()
    profile = MagicMock()
    profile.id = uuid4()
    profile.preferences = None

    with patch("app.crud_resume.get_draft_by_id", return_value=draft):
        with patch("app.crud_resume.get_or_create_profile", return_value=profile):
            with patch("app.crud_resume.add_profile_skill") as add_s:
                apply_resume_draft(
                    db,
                    uid,
                    draft.id,
                    ApplyResumeDraftIn(
                        skills_mode="append",
                        skills=[ProfileSkillIn(skill_name="Rust", self_assessed_level=2)],
                    ),
                )
    add_s.assert_called_once()


def test_apply_draft_work_replace(db):
    uid = uuid4()
    draft = MagicMock()
    draft.status = "draft"
    draft.id = uuid4()
    draft.resume_file_id = uuid4()
    profile = MagicMock()
    profile.id = uuid4()
    profile.preferences = None
    we = MagicMock()
    we.id = uuid4()

    with patch("app.crud_resume.get_draft_by_id", return_value=draft):
        with patch("app.crud_resume.get_or_create_profile", return_value=profile):
            with patch("app.crud_resume.list_work_experiences", return_value=[we]):
                with patch("app.crud_resume.delete_work_experience", return_value=True) as del_w:
                    with patch("app.crud_resume.add_work_experience") as add_w:
                        apply_resume_draft(
                            db,
                            uid,
                            draft.id,
                            ApplyResumeDraftIn(
                                work_experience_mode="replace",
                                work_experience=[
                                    WorkExperienceIn(company="A", title="T"),
                                ],
                            ),
                        )
    del_w.assert_called_once()
    add_w.assert_called_once()


def test_apply_draft_education_replace(db):
    uid = uuid4()
    draft = MagicMock()
    draft.status = "draft"
    draft.id = uuid4()
    draft.resume_file_id = uuid4()
    profile = MagicMock()
    profile.id = uuid4()
    profile.preferences = None

    eq = MagicMock()
    eq.filter.return_value = eq
    eq.delete = MagicMock(return_value=2)

    def query_side_effect(model):
        if model is Education:
            return eq
        return _q(first=None)

    db.query.side_effect = query_side_effect

    with patch("app.crud_resume.get_draft_by_id", return_value=draft):
        with patch("app.crud_resume.get_or_create_profile", return_value=profile):
            with patch("app.crud_resume.add_education") as add_e:
                apply_resume_draft(
                    db,
                    uid,
                    draft.id,
                    ApplyResumeDraftIn(
                        education_mode="replace",
                        education=[EducationIn(institution="Uni")],
                    ),
                )
    eq.delete.assert_called()
    add_e.assert_called_once()


class _MemUploadSession:
    def add(self, _o):
        pass

    def flush(self):
        pass

    def commit(self):
        pass

    def refresh(self, _o):
        pass


def test_create_resume_upload_empty_mime_uses_default(tmp_path, monkeypatch):
    monkeypatch.setattr(crud_resume.settings, "resume_storage_dir", str(tmp_path / "st"))
    mem = _MemUploadSession()
    uid = uuid4()
    rf, job, path = create_resume_upload(mem, uid, "cv.pdf", "", b"%PDF")
    assert rf.mime_type == "application/pdf"
    assert path.is_file()


def test_create_resume_rejects_bad_mime_when_name_not_pdf_suffix(tmp_path, monkeypatch):
    """Covers MIME guard: suffix is .pdf but basename does not end with '.pdf'."""

    def path_factory(arg):
        s = arg if isinstance(arg, str) else str(arg)
        if s.endswith("resume.final"):
            return SimpleNamespace(suffix=".PDF")
        return Path(s)

    monkeypatch.setattr(crud_resume, "Path", path_factory)
    monkeypatch.setattr(crud_resume.settings, "resume_storage_dir", str(tmp_path / "st"))
    mem = _MemUploadSession()
    with pytest.raises(ValueError, match="тип"):
        create_resume_upload(
            mem, uuid4(), "resume.final", "application/octet-stream", b"%PDF-1.4"
        )


@pytest.fixture
def db():
    return MagicMock()
