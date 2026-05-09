"""Security, deps, FastAPI meta, and Pydantic schemas."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from jose import jwt
from pydantic import ValidationError

import app.security as sec
from app.config import ProfileSettings
from app.deps import get_current_user_id
from app.main import app
from app.schemas import (
    EducationIn,
    ProfileIn,
    ProfilePreferenceIn,
    ProfileSkillIn,
    WorkExperienceIn,
)
from app.schemas_resume import ApplyResumeDraftIn, ResumeFileOut
from app.security import decode_access_token


@pytest.fixture
def jwt_secret(monkeypatch) -> str:
    secret = "unit-test-secret-at-least-32-chars-long!!"
    monkeypatch.setattr(sec.settings, "jwt_secret", secret)
    monkeypatch.setattr(sec.settings, "jwt_algorithm", "HS256")
    return secret


def test_profile_settings_model():
    s = ProfileSettings(service_name="x", version="1.0.0")
    assert s.service_name == "x"


def test_decode_access_token_ok(jwt_secret):
    token = jwt.encode(
        {"sub": str(uuid4()), "type": "access"},
        jwt_secret,
        algorithm="HS256",
    )
    payload = decode_access_token(token)
    assert payload["type"] == "access"


def test_decode_access_token_wrong_type(jwt_secret):
    token = jwt.encode(
        {"sub": str(uuid4()), "type": "refresh"},
        jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as ei:
        decode_access_token(token)
    assert ei.value.status_code == 401


def test_decode_access_token_invalid(jwt_secret):
    with pytest.raises(HTTPException):
        decode_access_token("not-a-jwt")


def test_get_current_user_id_invalid_sub(jwt_secret):
    token = jwt.encode(
        {"sub": "not-a-uuid", "type": "access"},
        jwt_secret,
        algorithm="HS256",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as ei:
        get_current_user_id(creds)
    assert ei.value.status_code == 401


def test_health_and_ready(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path / "rs"))
    with TestClient(app) as client:
        h = client.get("/health")
        assert h.status_code == 200
        assert h.json()["status"] == "ok"
        r = client.get("/ready")
        assert r.status_code == 200


def test_schemas_build():
    p = ProfileIn(full_name="Иван Иванов", location="Москва")
    assert p.full_name == "Иван Иванов"
    pref = ProfilePreferenceIn(preferred_locations=["Москва"], salary_from=100000)
    assert pref.salary_from == 100000
    skill = ProfileSkillIn(skill_name="Python", self_assessed_level=4)
    assert skill.self_assessed_level == 4
    we = WorkExperienceIn(company="ACME", title="Dev", is_current=True)
    assert we.is_current is True
    ed = EducationIn(institution="МГУ", end_year=2020)
    assert ed.end_year == 2020


def test_apply_resume_draft_in_defaults():
    body = ApplyResumeDraftIn()
    assert body.skills_mode == "append"
    assert body.work_experience_mode == "append"


def test_resume_file_out_rejects_incomplete():
    with pytest.raises(ValidationError):
        ResumeFileOut.model_validate({"id": uuid4()})
