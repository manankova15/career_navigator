"""
Load the same profile bundle as GET /profiles/me (+ skills + preferences) from the shared Postgres DB.
Used by the hourly refresh job (no end-user JWT).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def load_profile_bundle(db: Session, user_id: UUID) -> dict[str, Any] | None:
    """Профиль v2: канонические коды без текстового classifier в этом пути"""
    uid = str(user_id)
    meta = db.execute(
        text(
            """
            SELECT p.location, p.specialization, p.target_industry
            FROM profiles p
            WHERE p.user_id = CAST(:uid AS uuid)
            """
        ),
        {"uid": uid},
    ).mappings().first()
    if not meta:
        return None

    pref = db.execute(
        text(
            """
            SELECT pp.work_formats, pp.salary_from, pp.salary_to, pp.seniority
            FROM profile_preferences pp
            JOIN profiles p ON p.id = pp.profile_id
            WHERE p.user_id = CAST(:uid AS uuid)
            """
        ),
        {"uid": uid},
    ).mappings().first()

    skill_rows = db.execute(
        text(
            """
            SELECT s.name
            FROM skills s
            JOIN profile_skills ps ON ps.skill_id = s.id
            JOIN profiles p ON p.id = ps.profile_id
            WHERE p.user_id = CAST(:uid AS uuid)
            """
        ),
        {"uid": uid},
    ).fetchall()
    skills = [r[0] for r in skill_rows]

    prefs: dict[str, Any] = {}
    if pref:
        prefs = {
            "work_formats": list(pref["work_formats"] or []),
            "salary_from": pref["salary_from"],
            "salary_to": pref["salary_to"],
            "seniority": pref["seniority"],
        }

    return {
        "skills": skills,
        "preferences": prefs,
        "location": meta.get("location"),
        "specialization": meta.get("specialization"),
        "target_industry": meta.get("target_industry"),
    }
