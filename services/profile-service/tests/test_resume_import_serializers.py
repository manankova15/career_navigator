"""Private serializers on resume_import router (branch coverage)."""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.routers import resume_import as ri


def test_result_out_warnings_none():
    r = MagicMock()
    r.id = uuid4()
    r.resume_file_id = uuid4()
    r.is_hh_resume = True
    r.hh_confidence_score = 0.8
    r.warnings_json = None
    r.parsed_json = None
    out = ri._result_out(r)
    assert out.warnings == []
    assert out.parsed is None


def test_result_out_warnings_non_list():
    r = MagicMock()
    r.id = uuid4()
    r.resume_file_id = uuid4()
    r.is_hh_resume = False
    r.hh_confidence_score = 0.1
    r.warnings_json = {"a": 1}
    r.parsed_json = {"rawSectionsDetected": ["skills"]}
    out = ri._result_out(r)
    assert len(out.warnings) == 1


def test_result_out_parsed_not_dict():
    r = MagicMock()
    r.id = uuid4()
    r.resume_file_id = uuid4()
    r.is_hh_resume = False
    r.hh_confidence_score = 0.0
    r.warnings_json = []
    r.parsed_json = "broken"
    out = ri._result_out(r)
    assert out.parsed is None


def test_file_job_draft_out_roundtrip():
    rf = MagicMock()
    rf.id = uuid4()
    rf.user_id = uuid4()
    rf.original_name = "a.pdf"
    rf.mime_type = "application/pdf"
    rf.extension = ".pdf"
    rf.size = 3
    rf.sha256 = "0" * 64
    rf.source_type = "hh_resume"
    rf.uploaded_at = datetime.utcnow()
    f_out = ri._file_out(rf)
    assert f_out.original_name == "a.pdf"
