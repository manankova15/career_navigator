"""HTTP tests for /profiles with dependency overrides and patched CRUD."""

from datetime import datetime
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


def _profile_mock(uid, **kwargs):
    p = MagicMock()
    p.id = uuid4()
    p.user_id = uid
    p.full_name = kwargs.get("full_name", "FN")
    p.first_name = kwargs.get("first_name", "F")
    p.last_name = kwargs.get("last_name", "L")
    p.patronymic = kwargs.get("patronymic")
    p.bio = kwargs.get("bio")
    p.location = kwargs.get("location")
    p.target_role = kwargs.get("target_role")
    p.target_industry = kwargs.get("target_industry")
    p.headline = kwargs.get("headline")
    p.summary = kwargs.get("summary")
    p.created_at = datetime(2020, 1, 1)
    p.updated_at = datetime(2020, 1, 2)
    return p


def test_get_me(api_client, user_id):
    prof = _profile_mock(user_id)
    with patch("app.routers.profiles.get_or_create_profile", return_value=prof):
        r = api_client.get("/profiles/me", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert r.json()["user_id"] == str(user_id)


def test_put_me(api_client, user_id):
    prof = _profile_mock(user_id, full_name="New")
    with patch("app.routers.profiles.upsert_profile", return_value=prof):
        r = api_client.put(
            "/profiles/me",
            headers={"Authorization": "Bearer x"},
            json={"full_name": "New"},
        )
    assert r.status_code == 200


def test_preferences_get_and_put(api_client, user_id):
    prof = _profile_mock(user_id)
    prefs = MagicMock()
    prefs.id = uuid4()
    prefs.preferred_locations = []
    prefs.work_formats = []
    prefs.target_roles = []
    prefs.salary_from = None
    prefs.salary_to = None
    prefs.seniority = None
    prof.preferences = prefs

    with patch("app.routers.profiles.get_or_create_profile", return_value=prof):
        r = api_client.get("/profiles/me/preferences", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200

    out_prefs = MagicMock()
    out_prefs.id = uuid4()
    out_prefs.preferred_locations = ["СПб"]
    out_prefs.work_formats = []
    out_prefs.target_roles = []
    out_prefs.salary_from = 1
    out_prefs.salary_to = 2
    out_prefs.seniority = "middle"
    with patch("app.routers.profiles.upsert_preferences", return_value=out_prefs):
        r = api_client.put(
            "/profiles/me/preferences",
            headers={"Authorization": "Bearer x"},
            json={"preferred_locations": ["СПб"], "salary_from": 1, "salary_to": 2, "seniority": "middle"},
        )
    assert r.status_code == 200


def test_skills_crud(api_client, user_id):
    skill = MagicMock()
    skill.id = uuid4()
    skill.name = "Go"
    ps = MagicMock()
    ps.id = uuid4()
    ps.skill_id = skill.id
    ps.skill = skill
    ps.self_assessed_level = 3
    ps.confirmed = False
    ps.years_of_experience = 2

    with patch("app.routers.profiles.list_profile_skills", return_value=[ps]):
        r = api_client.get("/profiles/me/skills", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert r.json()[0]["skill_name"] == "Go"

    with patch("app.routers.profiles.add_profile_skill", return_value=ps):
        r = api_client.post(
            "/profiles/me/skills",
            headers={"Authorization": "Bearer x"},
            json={"skill_name": "Go", "self_assessed_level": 3, "years_of_experience": 2},
        )
    assert r.status_code == 201

    with patch("app.routers.profiles.delete_profile_skill", return_value=True):
        r = api_client.delete(
            f"/profiles/me/skills/{ps.id}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 204

    with patch("app.routers.profiles.delete_profile_skill", return_value=False):
        r = api_client.delete(
            f"/profiles/me/skills/{uuid4()}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 404


def test_experience_crud(api_client, user_id):
    we = MagicMock()
    we.id = uuid4()
    we.profile_id = uuid4()
    we.company = "C"
    we.title = "T"
    we.start_date = None
    we.end_date = None
    we.is_current = False
    we.description = None
    we.created_at = datetime(2020, 1, 1)

    with patch("app.routers.profiles.list_work_experiences", return_value=[we]):
        r = api_client.get("/profiles/me/experience", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200

    with patch("app.routers.profiles.add_work_experience", return_value=we):
        r = api_client.post(
            "/profiles/me/experience",
            headers={"Authorization": "Bearer x"},
            json={"company": "C", "title": "T"},
        )
    assert r.status_code == 201

    with patch("app.routers.profiles.update_work_experience", return_value=we):
        r = api_client.put(
            f"/profiles/me/experience/{we.id}",
            headers={"Authorization": "Bearer x"},
            json={"company": "C", "title": "T2"},
        )
    assert r.status_code == 200

    with patch("app.routers.profiles.update_work_experience", return_value=None):
        r = api_client.put(
            f"/profiles/me/experience/{uuid4()}",
            headers={"Authorization": "Bearer x"},
            json={"company": "C", "title": "T"},
        )
    assert r.status_code == 404

    with patch("app.routers.profiles.delete_work_experience", return_value=True):
        r = api_client.delete(
            f"/profiles/me/experience/{we.id}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 204

    with patch("app.routers.profiles.delete_work_experience", return_value=False):
        r = api_client.delete(
            f"/profiles/me/experience/{uuid4()}",
            headers={"Authorization": "Bearer x"},
        )
    assert r.status_code == 404


def test_education_post(api_client, user_id):
    ed = MagicMock()
    ed.id = uuid4()
    ed.profile_id = uuid4()
    ed.institution = "Вуз"
    ed.degree = None
    ed.field = None
    ed.start_year = None
    ed.end_year = 2020
    ed.created_at = datetime(2020, 1, 1)

    with patch("app.routers.profiles.list_educations", return_value=[ed]):
        r = api_client.get("/profiles/me/education", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200

    with patch("app.routers.profiles.add_education", return_value=ed):
        r = api_client.post(
            "/profiles/me/education",
            headers={"Authorization": "Bearer x"},
            json={"institution": "Вуз", "end_year": 2020},
        )
    assert r.status_code == 201


def test_preferences_none_profile(api_client, user_id):
    prof = _profile_mock(user_id)
    prof.preferences = None
    with patch("app.routers.profiles.get_or_create_profile", return_value=prof):
        r = api_client.get("/profiles/me/preferences", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert r.json() is None
