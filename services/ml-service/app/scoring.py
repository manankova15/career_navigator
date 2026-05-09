"""
Content-based scoring engine.

Score = w_skills   * S_skills
      + w_role     * S_role
      + w_seniority* S_seniority
      + w_salary   * S_salary
      + w_location * S_location
      + w_format   * S_format

All six sub-scores are normalised to [0, 1]. The weight vector is fixed
and derived analytically from the Analytic Hierarchy Process (see
`config.py` for the pairwise matrix and CR < 0.10 validation). The
engine is stateless, deterministic and does not depend on any external
training data or pretrained model.
"""

from __future__ import annotations

import re
from typing import Iterable

from .config import settings
from .schemas import (
    ScoreRequest,
    ScoreResponse,
    ScoredVacancy,
    UserProfileInput,
    VacancyInput,
)

SENIORITY_LEVELS = ["intern", "junior", "middle", "senior", "lead"]

_TOKEN_RE = re.compile(r"[a-zа-яё0-9+#\.]+", re.I)
_STOPWORDS = {
    "и", "в", "на", "с", "для", "of", "the", "a", "an", "to", "in", "at",
    "по", "от", "или", "or", "and", "for", "into", "из",
}


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    toks = {m.group(0).lower() for m in _TOKEN_RE.finditer(text)}
    return {t for t in toks if len(t) > 1 and t not in _STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def _norm_skills(skills: Iterable[str]) -> set[str]:
    return {s.strip().lower() for s in (skills or []) if s and s.strip()}


# ── Sub-scores ───────────────────────────────────────────────────────────────

def skill_score(
    user_skills: set[str], vacancy_skills: set[str]
) -> tuple[float, list[str], list[str]]:
    """Asymmetric coverage score — how much of the vacancy's requirement set
    the user already covers. If vacancy lists no skills, we fall back to a
    neutral 0.30 so that it still competes with badly-described postings.
    """
    if not vacancy_skills:
        return 0.30, [], []
    matched = user_skills & vacancy_skills
    missing = vacancy_skills - user_skills
    coverage = len(matched) / len(vacancy_skills)
    jaccard = len(matched) / len(user_skills | vacancy_skills)
    blended = 0.8 * coverage + 0.2 * jaccard
    return round(min(1.0, blended), 4), sorted(matched), sorted(missing)


def role_score(profile: UserProfileInput, vacancy: VacancyInput) -> float:
    """Semantic match between user's role/headline/summary and vacancy title.

    Uses simple token Jaccard on the lowercased alphabetic+numeric tokens.
    Target roles contribute strongly, headline — moderately, summary — lightly.
    """
    roles_blob = " ".join([*(profile.target_roles or []), profile.headline or ""])
    summary_blob = profile.summary or ""
    title_toks = _tokens(vacancy.title)
    desc_toks = _tokens(vacancy.description)

    role_toks = _tokens(roles_blob)
    summary_toks = _tokens(summary_blob)

    if not title_toks:
        return 0.5

    j_role_title = _jaccard(role_toks, title_toks)
    j_role_desc = _jaccard(role_toks, desc_toks) if desc_toks else 0.0
    j_summary_title = _jaccard(summary_toks, title_toks) if summary_toks else 0.0

    raw = 0.70 * j_role_title + 0.20 * j_role_desc + 0.10 * j_summary_title
    # Jaccard values for natural text are typically small (<0.3); stretch them.
    stretched = min(1.0, raw * 3.0)
    return round(stretched, 4)


def location_score(profile: UserProfileInput, vacancy_location: str | None) -> float:
    if not vacancy_location:
        return 0.5
    vac = vacancy_location.lower()
    if any(kw in vac for kw in ("remote", "удалённ", "удален", "дистанц", "hybrid", "гибрид")):
        return 0.90
    if not profile.preferred_locations:
        return 0.5
    for pref in profile.preferred_locations:
        p = pref.lower().strip()
        if not p:
            continue
        if p in vac or vac in p:
            return 1.0
    return 0.1


def salary_score(profile: UserProfileInput, vac_from: int | None, vac_to: int | None) -> float:
    """Overlap-ratio of vacancy salary range with user's expected range."""
    if profile.salary_from is None and profile.salary_to is None:
        return 0.5
    if vac_from is None and vac_to is None:
        return 0.5

    u_from = profile.salary_from or 0
    u_to = profile.salary_to or 10_000_000
    v_from = vac_from or 0
    v_to = vac_to or 10_000_000

    overlap = max(0, min(u_to, v_to) - max(u_from, v_from))
    if overlap > 0:
        denom = max(1, u_to - u_from)
        return min(1.0, round(overlap / denom, 4))

    gap = max(u_from - v_to, v_from - u_to)
    ref = max(1, u_to - u_from)
    if gap <= 0.1 * ref:
        return 0.4
    if gap <= 0.25 * ref:
        return 0.25
    return 0.1


def seniority_score(profile: UserProfileInput, vacancy_seniority: str | None) -> float:
    if not vacancy_seniority or not profile.seniority:
        return 0.5
    u = profile.seniority.lower()
    v = vacancy_seniority.lower()
    if u == v:
        return 1.0
    try:
        ui = SENIORITY_LEVELS.index(u)
        vi = SENIORITY_LEVELS.index(v)
    except ValueError:
        return 0.35
    diff = abs(ui - vi)
    if diff == 1:
        return 0.70 if vi > ui else 0.65  # slight nudge toward promotion
    if diff == 2:
        return 0.30
    return 0.1


def format_score(profile: UserProfileInput, vacancy: VacancyInput) -> float:
    """Match preferred work format against vacancy location / employment type."""
    prefs = {f.lower().strip() for f in (profile.work_formats or []) if f}
    if not prefs:
        return 0.5

    loc = (vacancy.location or "").lower()
    et = (vacancy.employment_type or "").lower()
    haystack = f"{loc} {et}"

    for p in prefs:
        if p == "remote" and any(k in haystack for k in ("remote", "удалённ", "удален", "дистанц")):
            return 1.0
        if p == "hybrid" and any(k in haystack for k in ("hybrid", "гибрид")):
            return 1.0
        if p == "office" and "remote" not in haystack and "удалён" not in haystack:
            return 0.9
    return 0.3


# ── Aggregation ──────────────────────────────────────────────────────────────

def _build_reasons(
    matched: list[str],
    loc: float,
    sal: float,
    sen: float,
    rol: float,
    vacancy: VacancyInput,
) -> list[str]:
    reasons: list[str] = []
    if matched:
        preview = ", ".join(matched[:4])
        suffix = f" +{len(matched) - 4} ещё" if len(matched) > 4 else ""
        reasons.append(f"Совпадение по навыкам: {preview}{suffix}")
    if rol >= 0.6:
        reasons.append("Роль соответствует вашим целям")
    if loc >= 0.9:
        reasons.append(f"Локация подходит: {vacancy.location or 'удалённо'}")
    if sal >= 0.8:
        reasons.append("Зарплата в пределах ожиданий")
    if sen >= 0.9:
        reasons.append(f"Уровень совпадает: {vacancy.seniority}")
    return reasons


def run_scoring(request: ScoreRequest) -> ScoreResponse:
    profile = request.profile
    user_skills = _norm_skills(profile.skills)

    w = settings
    results: list[ScoredVacancy] = []

    for vac in request.vacancies[: w.max_candidates]:
        vac_skills = _norm_skills(vac.skills)

        sk, matched, missing = skill_score(user_skills, vac_skills)
        rol = role_score(profile, vac)
        sen = seniority_score(profile, vac.seniority)
        sal = salary_score(profile, vac.salary_from, vac.salary_to)
        loc = location_score(profile, vac.location)
        fmt = format_score(profile, vac)

        total = (
            w.weight_skills * sk
            + w.weight_role * rol
            + w.weight_seniority * sen
            + w.weight_salary * sal
            + w.weight_location * loc
            + w.weight_format * fmt
        )

        features = {
            "skill_score": sk,
            "role_score": rol,
            "seniority_score": sen,
            "salary_score": sal,
            "location_score": loc,
            "format_score": fmt,
            "vacancy_skills": sorted(vac_skills),
            "vacancy_title": vac.title or "",
            "vacancy_seniority": vac.seniority,
        }

        results.append(
            ScoredVacancy(
                vacancy_id=vac.vacancy_id,
                score=round(min(1.0, total), 4),
                skill_score=sk,
                role_score=rol,
                location_score=loc,
                salary_score=sal,
                seniority_score=sen,
                format_score=fmt,
                matched_skills=matched,
                missing_skills=missing,
                reasons=_build_reasons(matched, loc, sal, sen, rol, vac),
                features=features,
            )
        )

    results.sort(key=lambda x: x.score, reverse=True)

    return ScoreResponse(
        user_id=profile.user_id,
        algorithm="content_ahp_v2",
        total_scored=len(results),
        results=results[: w.top_n],
    )


# ── Back-compat helpers used elsewhere ───────────────────────────────────────

def _skill_score(user_skills: set[str], vacancy_skills: set[str]):
    return skill_score(user_skills, vacancy_skills)


def _location_score(profile, vacancy_location):
    return location_score(profile, vacancy_location)


def _salary_score(profile, vac_from, vac_to):
    return salary_score(profile, vac_from, vac_to)
