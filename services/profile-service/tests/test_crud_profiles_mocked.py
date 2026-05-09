"""Unit-style tests for app.crud with a mocked SQLAlchemy session."""

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app import crud
from app.schemas import (
    EducationIn,
    ProfileIn,
    ProfilePreferenceIn,
    ProfileSkillIn,
    WorkExperienceIn,
)


def _query_chain(first_result=None, all_result=None):
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    if all_result is not None:
        q.all.return_value = all_result
    q.first.return_value = first_result
    return q


@pytest.fixture
def db():
    session = MagicMock()
    session.query.return_value = _query_chain()
    return session


def test_get_profile_by_user_id(db):
    uid = uuid4()
    prof = MagicMock()
    db.query.return_value = _query_chain(first_result=prof)
    assert crud.get_profile_by_user_id(db, uid) is prof


def test_get_or_create_creates(db):
    uid = uuid4()
    new_prof = MagicMock()
    new_prof.id = uuid4()

    db.query.return_value = _query_chain(first_result=None)

    def add_side_effect(obj):
        if hasattr(obj, "user_id"):
            obj.id = new_prof.id

    db.add.side_effect = add_side_effect
    out = crud.get_or_create_profile(db, uid)
    db.add.assert_called()
    db.commit.assert_called()


def test_get_or_create_returns_existing(db):
    uid = uuid4()
    prof = MagicMock()
    db.query.return_value = _query_chain(first_result=prof)
    assert crud.get_or_create_profile(db, uid) is prof


def test_upsert_profile(db):
    uid = uuid4()
    prof = MagicMock()
    db.query.return_value = _query_chain(first_result=prof)
    data = ProfileIn(full_name="N")
    crud.upsert_profile(db, uid, data)
    assert prof.full_name == "N"


def test_upsert_preferences_create_and_update(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    prefs = MagicMock()
    prefs.profile_id = prof.id

    def q_create(model):
        if model.__name__ == "Profile":
            return _query_chain(first_result=prof)
        return _query_chain(first_result=None)

    db.query.side_effect = q_create
    crud.upsert_preferences(db, uid, ProfilePreferenceIn(salary_from=10))

    def q_update(model):
        if model.__name__ == "Profile":
            return _query_chain(first_result=prof)
        return _query_chain(first_result=prefs)

    db.query.side_effect = q_update
    crud.upsert_preferences(db, uid, ProfilePreferenceIn(salary_from=20))


def test_list_profile_skills_empty_without_profile(db):
    db.query.return_value = _query_chain(first_result=None)
    assert crud.list_profile_skills(db, uuid4()) == []


def test_list_profile_skills_with_rows(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    ps = MagicMock()
    db.query.return_value = _query_chain(first_result=prof)
    db.query.side_effect = None
    q2 = _query_chain(all_result=[ps])
    db.query.return_value = q2
    # list_profile_skills: get_profile then query ProfileSkill
    def query_side_effect(model):
        if model.__name__ == "Profile":
            q = _query_chain(first_result=prof)
            return q
        return _query_chain(all_result=[ps])

    db.query.side_effect = query_side_effect
    out = crud.list_profile_skills(db, uid)
    assert out == [ps]


def test_add_profile_skill_creates_new_skill(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    new_ps = MagicMock()

    def query_side_effect(model):
        if model.__name__ == "Profile":
            return _query_chain(first_result=prof)
        if model.__name__ == "Skill":
            return _query_chain(first_result=None)
        if model.__name__ == "ProfileSkill":
            return _query_chain(first_result=None)

    db.query.side_effect = query_side_effect

    def add_capture(obj):
        if hasattr(obj, "skill_id"):
            new_ps.id = uuid4()
            obj.id = new_ps.id

    db.add.side_effect = add_capture
    out = crud.add_profile_skill(db, uid, ProfileSkillIn(skill_name="NewSkill", self_assessed_level=2))
    assert out is not None


def test_add_profile_skill_new_and_update_existing(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    skill = MagicMock()
    skill.id = uuid4()
    existing = MagicMock()

    def query_side_effect(model):
        if model.__name__ == "Profile":
            return _query_chain(first_result=prof)
        if model.__name__ == "Skill":
            return _query_chain(first_result=skill)
        if model.__name__ == "ProfileSkill":
            return _query_chain(first_result=existing)

    db.query.side_effect = query_side_effect
    crud.add_profile_skill(db, uid, ProfileSkillIn(skill_name="Py", self_assessed_level=2))
    db.query.side_effect = query_side_effect
    crud.add_profile_skill(
        db, uid, ProfileSkillIn(skill_name="Py", self_assessed_level=4, years_of_experience=5)
    )


def test_delete_profile_skill_paths(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    ps = MagicMock()

    db.query.side_effect = [
        _query_chain(first_result=None),
        _query_chain(first_result=prof),
        _query_chain(first_result=None),
        _query_chain(first_result=prof),
        _query_chain(first_result=ps),
    ]
    assert crud.delete_profile_skill(db, uid, uuid4()) is False
    assert crud.delete_profile_skill(db, uuid4(), uuid4()) is False
    assert crud.delete_profile_skill(db, uid, ps.id) is True


def test_list_work_experiences_empty_without_profile(db):
    db.query.return_value = _query_chain(first_result=None)
    assert crud.list_work_experiences(db, uuid4()) == []


def test_list_work_experiences_returns_rows(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    we = MagicMock()

    def q(model):
        if model.__name__ == "Profile":
            return _query_chain(first_result=prof)
        return _query_chain(all_result=[we])

    db.query.side_effect = q
    assert crud.list_work_experiences(db, uid) == [we]


def test_update_work_experience_no_profile(db):
    db.query.return_value = _query_chain(first_result=None)
    assert (
        crud.update_work_experience(
            db, uuid4(), uuid4(), WorkExperienceIn(company="A", title="B")
        )
        is None
    )


def test_delete_work_experience_no_profile(db):
    db.query.return_value = _query_chain(first_result=None)
    assert crud.delete_work_experience(db, uuid4(), uuid4()) is False


def test_list_educations_with_profile(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    ed = MagicMock()

    def q(model):
        if model.__name__ == "Profile":
            return _query_chain(first_result=prof)
        return _query_chain(all_result=[ed])

    db.query.side_effect = q
    assert crud.list_educations(db, uid) == [ed]


def test_add_and_update_delete_work_experience(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    we = MagicMock()
    we.id = uuid4()
    missing = uuid4()

    db.query.side_effect = [
        _query_chain(first_result=prof),
        _query_chain(first_result=prof),
        _query_chain(first_result=we),
        _query_chain(first_result=prof),
        _query_chain(first_result=None),
        _query_chain(first_result=prof),
        _query_chain(first_result=None),
        _query_chain(first_result=prof),
        _query_chain(first_result=we),
    ]
    crud.add_work_experience(
        db, uid, WorkExperienceIn(company="A", title="B", start_date=date(2020, 1, 1))
    )
    crud.update_work_experience(
        db, uid, we.id, WorkExperienceIn(company="A", title="C", start_date=date(2020, 1, 1))
    )
    assert crud.update_work_experience(db, uid, missing, WorkExperienceIn(company="A", title="C")) is None
    assert crud.delete_work_experience(db, uid, missing) is False
    assert crud.delete_work_experience(db, uid, we.id) is True


def test_education_list_and_add(db):
    uid = uuid4()
    prof = MagicMock()
    prof.id = uuid4()
    ed = MagicMock()
    db.query.side_effect = [
        _query_chain(first_result=None),
        _query_chain(first_result=prof),
    ]
    assert crud.list_educations(db, uid) == []
    crud.add_education(db, uid, EducationIn(institution="Вуз"))
