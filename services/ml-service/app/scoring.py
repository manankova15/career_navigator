"""
Hybrid recommendation scoring — algorithm ``hybrid_ahp_v3``.

Финальный скор для пары (пользователь u, вакансия v):

    S(u, v) =
        ⎧ max(P(u,v), 0.95)                             если v ∈ V⁺
        ⎨ min(P(u,v), 0.15) · 0.10                       если v ∈ V⁻
        ⎩ clip( [(1−τ) P(u,v) + τ B(u,v)] · M(u,v), 0,1) иначе

где
    P(u, v) — профильный AHP-скор по 7 признакам
              (skills, specialization, category, seniority, salary,
               location, format), веса см. ``config.py``;
    B(u, v) — поведенческий скор по сглаженной по Байесу истории лайков
              и кнопок «интересно»/«не подходит»;
    τ(N)   = N / (N + N₀) — доверие к поведению, растущее с числом сигналов;
    M(u, v) — мягкая мультипликативная коррекция по «горячим/холодным» паттернам.

Полное математическое обоснование и проверка согласованности матрицы AHP
(CR ≈ 0.007) — в ``docs/recommendation_model_v3.md``.
"""

from __future__ import annotations

import math
import re
from typing import Iterable

from .config import settings
from .schemas import (
    BehaviorInput,
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

# «Семьи» категорий — близкие, но не идентичные. При промахе по точной
# категории присваиваем смягчённый скор (см. §3.3 модели v3).
_CATEGORY_FAMILIES: list[set[str]] = [
    {"it", "analytics"},
    {"analytics", "finance"},
    {"finance", "accounting"},
    {"marketing", "sales"},
    {"marketing", "product"},
    {"product", "project_management"},
    {"design", "marketing"},
    {"hr", "administration"},
    {"customer_support", "operations"},
    {"engineering", "it"},
]

# «Соседние» специализации внутри одной категории.
_SPEC_NEIGHBORS: list[set[str]] = [
    {"backend_developer", "fullstack_developer"},
    {"frontend_developer", "fullstack_developer"},
    {"backend_developer", "frontend_developer"},
    {"qa_engineer", "devops_engineer"},
    {"data_analyst", "business_analyst"},
    {"business_analyst", "system_analyst"},
    {"data_analyst", "financial_analyst"},
    {"product_manager", "project_manager"},
    {"sales_manager", "account_manager"},
    {"internet_marketer", "performance_marketer"},
]


# ── Helpers ──────────────────────────────────────────────────────────────────

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


def _norm_label(value: str | None) -> str | None:
    if not value:
        return None
    s = str(value).strip().lower()
    return s or None


# ── Sub-scores ───────────────────────────────────────────────────────────────

def category_score(profile: UserProfileInput, vacancy: VacancyInput) -> float:
    """1 если профиль и вакансия одной категории, 0.6 — «семья», 0 — промах,
    0.5 — нет данных хотя бы у одной из сторон."""
    vac_cat = _norm_label(vacancy.profession_area)
    profile_cats = {
        c for c in (
            _norm_label(c) for c in (profile.preferred_categories or [])
        ) if c
    }
    if profile.target_industry:
        v = _norm_label(profile.target_industry)
        if v:
            profile_cats.add(v)

    if not vac_cat or not profile_cats:
        return 0.5

    if vac_cat in profile_cats:
        return 1.0

    for fam in _CATEGORY_FAMILIES:
        if vac_cat in fam and profile_cats & fam:
            return float(settings.category_family_score)
    return 0.0


def specialization_score(profile: UserProfileInput, vacancy: VacancyInput) -> float:
    """1 если совпала, ``spec_neighbor_score`` для «соседней», 0 иначе.
    Нейтральное 0.5 при отсутствии разметки у одной из сторон."""
    vac_spec = _norm_label(vacancy.specialization)
    profile_specs = {
        s for s in (
            _norm_label(s) for s in (profile.preferred_specializations or [])
        ) if s
    }

    if not vac_spec or not profile_specs:
        return 0.5

    if vac_spec in profile_specs:
        return 1.0

    for neigh in _SPEC_NEIGHBORS:
        if vac_spec in neigh and profile_specs & neigh:
            return float(settings.spec_neighbor_score)
    return 0.0


def skill_score(
    user_skills: set[str], vacancy_skills: set[str]
) -> tuple[float, list[str], list[str]]:
    """Асимметричное «покрытие» — сколько требований вакансии есть у юзера.
    При пустом списке навыков у вакансии ставим нейтральные 0.30, чтобы плохо
    описанная вакансия всё ещё могла конкурировать."""
    if not vacancy_skills:
        return 0.30, [], []
    matched = user_skills & vacancy_skills
    missing = vacancy_skills - user_skills
    coverage = len(matched) / len(vacancy_skills)
    jaccard = len(matched) / len(user_skills | vacancy_skills)
    blended = 0.7 * coverage + 0.3 * jaccard
    return round(min(1.0, blended), 4), sorted(matched), sorted(missing)


def location_score(profile: UserProfileInput, vacancy: VacancyInput) -> float:
    loc = vacancy.location or ""
    if not loc:
        return 0.5
    vac = loc.lower()
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
    """Overlap-ratio диапазона вакансии с диапазоном пользователя (всё в RUB
    эквиваленте — конвертация выполняется в recommendation-service)."""
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
        return 0.70 if vi > ui else 0.65
    if diff == 2:
        return 0.30
    return 0.1


def format_score(profile: UserProfileInput, vacancy: VacancyInput) -> float:
    """Совпадение предпочитаемого формата работы с разметкой вакансии."""
    prefs = {f.lower().strip() for f in (profile.work_formats or []) if f}
    if not prefs:
        return 0.5

    haystack_tokens: set[str] = set()
    for w in (vacancy.work_format or []):
        if w:
            haystack_tokens.add(w.lower().strip())
    loc = (vacancy.location or "").lower()
    et = (vacancy.employment_type or "").lower()
    haystack = f"{loc} {et}"

    for p in prefs:
        if p == "remote" and (
            "remote" in haystack_tokens
            or any(k in haystack for k in ("remote", "удалённ", "удален", "дистанц"))
        ):
            return 1.0
        if p == "hybrid" and (
            "hybrid" in haystack_tokens
            or any(k in haystack for k in ("hybrid", "гибрид"))
        ):
            return 1.0
        if p == "office" and (
            "office" in haystack_tokens
            or ("remote" not in haystack and "удалён" not in haystack and "remote" not in haystack_tokens)
        ):
            return 0.9
    return 0.3


# ── Behavior score B(u, v) ───────────────────────────────────────────────────

def _avg_pref(keys: Iterable[str], pref_map: dict[str, float]) -> float:
    """Средняя байес-сглаженная склонность по множеству ключей. Возвращает 0
    если ключей нет или ни один не встречается в карте."""
    vals = [pref_map[k] for k in keys if k in pref_map]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def behavior_score(
    behavior: BehaviorInput,
    vacancy: VacancyInput,
    vacancy_skills: set[str],
) -> tuple[float, dict[str, float]]:
    """Вычисляет B(u, v) ∈ [0, 1] и возвращает компоненты для интерпретации."""
    cat = _norm_label(vacancy.profession_area)
    spec = _norm_label(vacancy.specialization)
    title_tokens = _tokens(vacancy.title)

    beta_c = behavior.category_pref.get(cat, 0.0) if cat else 0.0
    beta_s = behavior.specialization_pref.get(spec, 0.0) if spec else 0.0
    beta_sk = _avg_pref(vacancy_skills, behavior.skill_pref)
    beta_t = _avg_pref(title_tokens, behavior.title_token_pref)

    s = (
        settings.behavior_alpha_category * beta_c
        + settings.behavior_alpha_specialization * beta_s
        + settings.behavior_alpha_skills * beta_sk
        + settings.behavior_alpha_title * beta_t
    )

    raw = 0.5 + 0.5 * s
    score = max(0.0, min(1.0, raw))
    return score, {
        "beta_category": round(beta_c, 4),
        "beta_specialization": round(beta_s, 4),
        "beta_skills": round(beta_sk, 4),
        "beta_title": round(beta_t, 4),
    }


# ── Multiplier M(u, v) ───────────────────────────────────────────────────────

def _multiplier(
    behavior: BehaviorInput,
    vacancy: VacancyInput,
    vacancy_skills: set[str],
    tau: float,
) -> tuple[float, dict[str, float]]:
    if tau <= 0.0:
        return 1.0, {
            "neg_skill_ratio": 0.0,
            "pos_skill_ratio": 0.0,
            "neg_title_ratio": 0.0,
            "pos_title_ratio": 0.0,
        }

    if vacancy_skills:
        skill_prefs = [behavior.skill_pref.get(s, 0.0) for s in vacancy_skills]
        n = len(skill_prefs)
        neg_skill = sum(
            1 for v in skill_prefs if v <= settings.multiplier_neg_skill_threshold
        ) / n
        pos_skill = sum(
            1 for v in skill_prefs if v >= settings.multiplier_pos_skill_threshold
        ) / n
    else:
        neg_skill = pos_skill = 0.0

    title_tokens = _tokens(vacancy.title)
    if title_tokens:
        title_prefs = [behavior.title_token_pref.get(t, 0.0) for t in title_tokens]
        n = len(title_prefs)
        neg_title = sum(
            1 for v in title_prefs if v <= settings.multiplier_neg_skill_threshold
        ) / n
        pos_title = sum(
            1 for v in title_prefs if v >= settings.multiplier_pos_skill_threshold
        ) / n
    else:
        neg_title = pos_title = 0.0

    reward = (
        settings.multiplier_skill_reward * pos_skill
        + settings.multiplier_title_reward * pos_title
    )
    penalty = (
        settings.multiplier_skill_penalty * neg_skill
        + settings.multiplier_title_penalty * neg_title
    )
    mult = 1.0 + tau * (reward - penalty)
    mult = max(settings.multiplier_min, min(settings.multiplier_max, mult))
    return mult, {
        "neg_skill_ratio": round(neg_skill, 4),
        "pos_skill_ratio": round(pos_skill, 4),
        "neg_title_ratio": round(neg_title, 4),
        "pos_title_ratio": round(pos_title, 4),
    }


# ── Aggregation ──────────────────────────────────────────────────────────────

def _trust(total_signals: int) -> float:
    n = max(0, int(total_signals))
    return n / (n + settings.behavior_trust_n0) if (n + settings.behavior_trust_n0) > 0 else 0.0


def _build_reasons(
    matched: list[str],
    cat: float,
    spec: float,
    sk: float,
    sal: float,
    sen: float,
    loc: float,
    vacancy: VacancyInput,
) -> list[str]:
    reasons: list[str] = []
    if cat >= 0.99 and vacancy.profession_area:
        reasons.append(f"Категория совпадает: {vacancy.profession_area}")
    elif cat >= 0.5 and vacancy.profession_area:
        reasons.append(f"Близкая категория: {vacancy.profession_area}")
    if spec >= 0.99 and vacancy.specialization:
        reasons.append(f"Специализация совпадает: {vacancy.specialization}")
    elif spec >= 0.69 and vacancy.specialization:
        reasons.append(f"Соседняя специализация: {vacancy.specialization}")
    if matched:
        preview = ", ".join(matched[:4])
        suffix = f" +{len(matched) - 4} ещё" if len(matched) > 4 else ""
        reasons.append(f"Совпадение по навыкам: {preview}{suffix}")
    if loc >= 0.9:
        reasons.append(f"Локация подходит: {vacancy.location or 'удалённо'}")
    if sal >= 0.8:
        reasons.append("Зарплата в пределах ожиданий")
    if sen >= 0.9 and vacancy.seniority:
        reasons.append(f"Уровень совпадает: {vacancy.seniority}")
    return reasons


def run_scoring(request: ScoreRequest) -> ScoreResponse:
    profile = request.profile
    behavior = request.behavior or BehaviorInput()
    user_skills = _norm_skills(profile.skills)

    tau = _trust(behavior.total_signals)
    positive_ids = {str(x) for x in (behavior.positive_vacancy_ids or [])}
    negative_ids = {str(x) for x in (behavior.negative_vacancy_ids or [])}

    w = settings
    results: list[ScoredVacancy] = []

    for vac in request.vacancies[: w.max_candidates]:
        vac_skills = _norm_skills(vac.skills)

        cat = category_score(profile, vac)
        spec = specialization_score(profile, vac)
        sk, matched, missing = skill_score(user_skills, vac_skills)
        sen = seniority_score(profile, vac.seniority)
        sal = salary_score(profile, vac.salary_from, vac.salary_to)
        loc = location_score(profile, vac)
        fmt = format_score(profile, vac)

        profile_score = (
            w.weight_category * cat
            + w.weight_specialization * spec
            + w.weight_skills * sk
            + w.weight_salary * sal
            + w.weight_seniority * sen
            + w.weight_format * fmt
            + w.weight_location * loc
        )
        profile_score = max(0.0, min(1.0, profile_score))

        beh_score, beh_components = behavior_score(behavior, vac, vac_skills)
        mult, mult_components = _multiplier(behavior, vac, vac_skills, tau)

        blended = (1.0 - tau) * profile_score + tau * beh_score
        # ── Anti-saturation ──────────────────────────────────────────────
        # Если у пользователя много лайков, B(u, v) → 1 для всех подобных
        # вакансий, M(u, v) → 1.5, и `blended * mult` упирается в hard-cap
        # 1.0 у десятков карточек — UI показывает 100% match повсюду и
        # ранжирование «плывёт». Чтобы сохранить дисперсию, мягко сжимаем
        # хвост через гладкую логистическую функцию: значения <0.80 проходят
        # почти без изменений, а 0.80→1.0 утрамбовывается в 0.80→0.97.
        raw = max(0.0, blended * mult)
        if raw <= 0.80:
            final = raw
        else:
            over = raw - 0.80                       # ∈ [0, 0.70]
            squashed = 0.17 * math.tanh(over / 0.17)  # ∈ [0, ~0.17)
            final = 0.80 + squashed
        final = max(0.0, min(0.99, final))

        direct: float | None = None
        vac_id = str(vac.vacancy_id)
        if vac_id in positive_ids:
            direct = 1.0
            # Liked-vacancy floor применяется к финалу ПОСЛЕ anti-saturation:
            # floor=0.95 + cap=0.99 → лайкнутые карточки получают 95–99%,
            # неоценённые — 0–80%. Это сохраняет дисперсию и одновременно
            # явно отмечает прямое «нравится».
            final = max(final, settings.direct_positive_floor)
            final = min(final, 0.99)
        elif vac_id in negative_ids:
            direct = -1.0
            capped = min(profile_score, settings.direct_negative_ceiling)
            final = round(capped * settings.direct_negative_multiplier, 4)

        features = {
            "category_score": cat,
            "specialization_score": spec,
            "skill_score": sk,
            "seniority_score": sen,
            "salary_score": sal,
            "location_score": loc,
            "format_score": fmt,
            "profile_score": round(profile_score, 4),
            "behavior_score": round(beh_score, 4),
            "tau": round(tau, 4),
            "multiplier": round(mult, 4),
            "behavior_components": beh_components,
            "multiplier_components": mult_components,
            "direct_signal": direct,
            "vacancy_skills": sorted(vac_skills),
            "vacancy_title": vac.title or "",
            "vacancy_seniority": vac.seniority,
            "vacancy_category": vac.profession_area,
            "vacancy_specialization": vac.specialization,
        }

        results.append(
            ScoredVacancy(
                vacancy_id=vac.vacancy_id,
                score=round(min(1.0, final), 4),
                base_score=round(profile_score, 4),
                behavior_score=round(beh_score, 4),
                tau=round(tau, 4),
                multiplier=round(mult, 4),
                direct_signal=direct,
                category_score=cat,
                specialization_score=spec,
                skill_score=sk,
                location_score=loc,
                salary_score=sal,
                seniority_score=sen,
                format_score=fmt,
                matched_skills=matched,
                missing_skills=missing,
                reasons=_build_reasons(matched, cat, spec, sk, sal, sen, loc, vac),
                features=features,
            )
        )

    results.sort(key=lambda x: x.score, reverse=True)

    return ScoreResponse(
        user_id=profile.user_id,
        algorithm=settings.algorithm_name,
        total_scored=len(results),
        results=results[: w.top_n],
    )


# ── Back-compat helpers used elsewhere ───────────────────────────────────────

def _skill_score(user_skills: set[str], vacancy_skills: set[str]):
    return skill_score(user_skills, vacancy_skills)


def _location_score(profile, vacancy):
    if hasattr(vacancy, "location"):
        return location_score(profile, vacancy)
    fake = VacancyInput(vacancy_id=__placeholder_uuid(), title="", company="", location=vacancy)
    return location_score(profile, fake)


def _salary_score(profile, vac_from, vac_to):
    return salary_score(profile, vac_from, vac_to)


def __placeholder_uuid():
    from uuid import uuid4
    return uuid4()
