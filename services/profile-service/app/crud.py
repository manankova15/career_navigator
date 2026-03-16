from uuid import UUID

from sqlalchemy.orm import Session

from .models import Education, Profile, ProfilePreference, ProfileSkill, Skill, WorkExperience
from .schemas import EducationIn, ProfileIn, ProfilePreferenceIn, ProfileSkillIn, WorkExperienceIn


def get_profile_by_user_id(db: Session, user_id: UUID) -> Profile | None:
    return db.query(Profile).filter(Profile.user_id == user_id).first()


def get_or_create_profile(db: Session, user_id: UUID) -> Profile:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def upsert_profile(db: Session, user_id: UUID, data: ProfileIn) -> Profile:
    profile = get_or_create_profile(db, user_id)
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def upsert_preferences(db: Session, user_id: UUID, data: ProfilePreferenceIn) -> ProfilePreference:
    profile = get_or_create_profile(db, user_id)
    prefs = (
        db.query(ProfilePreference).filter(ProfilePreference.profile_id == profile.id).first()
    )
    if not prefs:
        prefs = ProfilePreference(profile_id=profile.id, **data.model_dump())
        db.add(prefs)
    else:
        for key, value in data.model_dump().items():
            setattr(prefs, key, value)
    db.commit()
    db.refresh(prefs)
    return prefs


def _get_or_create_skill(db: Session, skill_name: str) -> Skill:
    normalized = skill_name.strip().lower()
    skill = db.query(Skill).filter(Skill.normalized_name == normalized).first()
    if not skill:
        skill = Skill(name=skill_name.strip(), normalized_name=normalized)
        db.add(skill)
        db.flush()
    return skill


def list_profile_skills(db: Session, user_id: UUID) -> list[ProfileSkill]:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return []
    return (
        db.query(ProfileSkill)
        .filter(ProfileSkill.profile_id == profile.id)
        .join(Skill)
        .all()
    )


def add_profile_skill(db: Session, user_id: UUID, data: ProfileSkillIn) -> ProfileSkill:
    profile = get_or_create_profile(db, user_id)
    skill = _get_or_create_skill(db, data.skill_name)
    existing = (
        db.query(ProfileSkill)
        .filter(ProfileSkill.profile_id == profile.id, ProfileSkill.skill_id == skill.id)
        .first()
    )
    if existing:
        existing.self_assessed_level = data.self_assessed_level
        if data.years_of_experience is not None:
            existing.years_of_experience = data.years_of_experience
        db.commit()
        db.refresh(existing)
        return existing
    ps = ProfileSkill(
        profile_id=profile.id,
        skill_id=skill.id,
        self_assessed_level=data.self_assessed_level,
        years_of_experience=data.years_of_experience,
    )
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return ps


def delete_profile_skill(db: Session, user_id: UUID, skill_id: UUID) -> bool:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return False
    ps = (
        db.query(ProfileSkill)
        .filter(ProfileSkill.profile_id == profile.id, ProfileSkill.id == skill_id)
        .first()
    )
    if not ps:
        return False
    db.delete(ps)
    db.commit()
    return True


def list_work_experiences(db: Session, user_id: UUID) -> list[WorkExperience]:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return []
    return db.query(WorkExperience).filter(WorkExperience.profile_id == profile.id).all()


def add_work_experience(db: Session, user_id: UUID, data: WorkExperienceIn) -> WorkExperience:
    profile = get_or_create_profile(db, user_id)
    exp = WorkExperience(profile_id=profile.id, **data.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


def update_work_experience(
    db: Session, user_id: UUID, exp_id: UUID, data: WorkExperienceIn
) -> WorkExperience | None:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return None
    exp = (
        db.query(WorkExperience)
        .filter(WorkExperience.profile_id == profile.id, WorkExperience.id == exp_id)
        .first()
    )
    if not exp:
        return None
    for key, value in data.model_dump().items():
        setattr(exp, key, value)
    db.commit()
    db.refresh(exp)
    return exp


def delete_work_experience(db: Session, user_id: UUID, exp_id: UUID) -> bool:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return False
    exp = (
        db.query(WorkExperience)
        .filter(WorkExperience.profile_id == profile.id, WorkExperience.id == exp_id)
        .first()
    )
    if not exp:
        return False
    db.delete(exp)
    db.commit()
    return True


def list_educations(db: Session, user_id: UUID) -> list[Education]:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return []
    return db.query(Education).filter(Education.profile_id == profile.id).all()


def add_education(db: Session, user_id: UUID, data: EducationIn) -> Education:
    profile = get_or_create_profile(db, user_id)
    edu = Education(profile_id=profile.id, **data.model_dump())
    db.add(edu)
    db.commit()
    db.refresh(edu)
    return edu
