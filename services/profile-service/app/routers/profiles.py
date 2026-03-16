from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crud import (
    add_education,
    add_profile_skill,
    add_work_experience,
    delete_profile_skill,
    delete_work_experience,
    get_or_create_profile,
    list_educations,
    list_profile_skills,
    list_work_experiences,
    update_work_experience,
    upsert_preferences,
    upsert_profile,
)
from ..database import get_db
from ..deps import get_current_user_id
from ..schemas import (
    EducationIn,
    EducationOut,
    ProfileIn,
    ProfileOut,
    ProfilePreferenceIn,
    ProfilePreferenceOut,
    ProfileSkillIn,
    ProfileSkillOut,
    WorkExperienceIn,
    WorkExperienceOut,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    return get_or_create_profile(db, user_id)


@router.put("/me", response_model=ProfileOut)
async def update_my_profile(
    data: ProfileIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return upsert_profile(db, user_id, data)


@router.get("/me/preferences", response_model=ProfilePreferenceOut | None)
async def get_preferences(
    user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    profile = get_or_create_profile(db, user_id)
    return profile.preferences


@router.put("/me/preferences", response_model=ProfilePreferenceOut)
async def update_preferences(
    data: ProfilePreferenceIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return upsert_preferences(db, user_id, data)


@router.get("/me/skills", response_model=list[ProfileSkillOut])
async def get_skills(
    user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    items = list_profile_skills(db, user_id)
    return [
        ProfileSkillOut(
            id=ps.id,
            skill_id=ps.skill_id,
            skill_name=ps.skill.name,
            self_assessed_level=ps.self_assessed_level,
            confirmed=ps.confirmed,
            years_of_experience=ps.years_of_experience,
        )
        for ps in items
    ]


@router.post("/me/skills", response_model=ProfileSkillOut, status_code=status.HTTP_201_CREATED)
async def add_skill(
    data: ProfileSkillIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    ps = add_profile_skill(db, user_id, data)
    return ProfileSkillOut(
        id=ps.id,
        skill_id=ps.skill_id,
        skill_name=ps.skill.name,
        self_assessed_level=ps.self_assessed_level,
        confirmed=ps.confirmed,
        years_of_experience=ps.years_of_experience,
    )


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill(
    skill_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not delete_profile_skill(db, user_id, skill_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")


@router.get("/me/experience", response_model=list[WorkExperienceOut])
async def get_experience(
    user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    return list_work_experiences(db, user_id)


@router.post(
    "/me/experience", response_model=WorkExperienceOut, status_code=status.HTTP_201_CREATED
)
async def add_experience(
    data: WorkExperienceIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return add_work_experience(db, user_id, data)


@router.put("/me/experience/{exp_id}", response_model=WorkExperienceOut)
async def update_experience(
    exp_id: UUID,
    data: WorkExperienceIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    result = update_work_experience(db, user_id, exp_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Work experience not found"
        )
    return result


@router.delete("/me/experience/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_experience(
    exp_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not delete_work_experience(db, user_id, exp_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Work experience not found"
        )


@router.get("/me/education", response_model=list[EducationOut])
async def get_education(
    user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    return list_educations(db, user_id)


@router.post(
    "/me/education", response_model=EducationOut, status_code=status.HTTP_201_CREATED
)
async def add_education_entry(
    data: EducationIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return add_education(db, user_id, data)
