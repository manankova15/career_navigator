"""
Skill-gap analyser (Phase 1).

For each skill required in the target vacancies but absent from the user's
profile, compute an importance score = frequency / total_vacancies.
Returns the top-N gaps sorted by importance.
"""

from __future__ import annotations

from collections import defaultdict

from .config import settings
from .schemas import SkillGapItem, SkillGapRequest, SkillGapResponse

# Lightweight resource suggestions per skill keyword
_RESOURCE_HINTS: dict[str, list[str]] = {
    "python": ["Python docs (docs.python.org)", "Real Python (realpython.com)"],
    "fastapi": ["FastAPI docs (fastapi.tiangolo.com)"],
    "postgresql": ["PostgreSQL Tutorial (postgresqltutorial.com)"],
    "docker": ["Play with Docker (labs.play-with-docker.com)"],
    "kubernetes": ["Kubernetes docs (kubernetes.io/docs)"],
    "sql": ["SQLZoo (sqlzoo.net)", "Mode SQL Tutorial (mode.com/sql-tutorial)"],
    "git": ["Pro Git book (git-scm.com/book)"],
    "redis": ["Redis University (university.redis.com)"],
    "celery": ["Celery docs (docs.celeryq.dev)"],
    "react": ["React docs (react.dev)"],
    "typescript": ["TypeScript handbook (typescriptlang.org/docs)"],
    "machine learning": ["Fast.ai (fast.ai)", "Scikit-learn docs"],
    "tensorflow": ["TensorFlow tutorials (tensorflow.org)"],
    "pytorch": ["PyTorch tutorials (pytorch.org)"],
    "kafka": ["Confluent Kafka tutorials"],
    "rabbitmq": ["RabbitMQ tutorials (rabbitmq.com/tutorials)"],
    "linux": ["Linux Journey (linuxjourney.com)"],
    "golang": ["A Tour of Go (tour.golang.org)"],
    "java": ["Baeldung Java (baeldung.com)"],
}


def _suggest_resources(skill_name: str) -> list[str]:
    key = skill_name.lower()
    for keyword, resources in _RESOURCE_HINTS.items():
        if keyword in key:
            return resources
    return []


def compute_skill_gap(request: SkillGapRequest) -> SkillGapResponse:
    user_skills = {s.strip().lower() for s in request.profile.skills}
    target_vacancies = request.target_vacancies

    # Count how many vacancies require each missing skill
    skill_freq: dict[str, int] = defaultdict(int)
    skill_display: dict[str, str] = {}   # lower → original casing

    for vac in target_vacancies:
        seen_in_this_vac: set[str] = set()
        for skill in vac.skills:
            lower = skill.strip().lower()
            if lower in user_skills:
                continue
            if lower not in seen_in_this_vac:
                skill_freq[lower] += 1
                skill_display[lower] = skill.strip()
                seen_in_this_vac.add(lower)

    total = len(target_vacancies)

    gaps: list[SkillGapItem] = [
        SkillGapItem(
            skill_name=skill_display[lower],
            importance_score=round(count / total, 4) if total > 0 else 0.0,
            frequency=count,
            recommended_resources=_suggest_resources(lower),
        )
        for lower, count in sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)
    ]

    return SkillGapResponse(
        user_id=request.profile.user_id,
        total_target_vacancies=total,
        gaps=gaps[: settings.skill_gap_top_n],
    )
