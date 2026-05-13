"""Unit-тесты на рекомендательную модель v3 (`hybrid_ahp_v3`).

Запуск:
    cd services/ml-service && pytest app/test_scoring_v3.py -q

Тесты сгруппированы по разделам спецификации
``docs/recommendation_model_v3.md``:
    §3 — профильный скор P(u, v) и проверка AHP-весов;
    §4 — поведенческий скор B(u, v);
    §5 — адаптивное смешивание τ(N);
    §6 — мультипликатор M(u, v);
    §7 — прямой override.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from .config import settings
from .scoring import (
    behavior_score,
    category_score,
    run_scoring,
    salary_score,
    seniority_score,
    skill_score,
    specialization_score,
    _trust,
)
from .schemas import BehaviorInput, ScoreRequest, UserProfileInput, VacancyInput


# ── Фикстуры ─────────────────────────────────────────────────────────────────

def _profile(**overrides) -> UserProfileInput:
    base = dict(
        user_id=uuid4(),
        skills=["python", "sql"],
        preferred_locations=["Москва"],
        work_formats=["remote"],
        salary_from=200_000,
        salary_to=300_000,
        seniority="middle",
        target_industry="IT",
        preferred_categories=["analytics"],
        preferred_specializations=["data_analyst"],
    )
    base.update(overrides)
    return UserProfileInput(**base)


def _vacancy(**overrides) -> VacancyInput:
    base = dict(
        vacancy_id=uuid4(),
        title="Аналитик данных",
        company="ACME",
        location="Москва",
        salary_from=220_000,
        salary_to=280_000,
        seniority="middle",
        skills=["python", "sql", "tableau"],
        employment_type="full_time",
        description="Поиск аналитика данных для отдела BI.",
        published_at=None,
        profession_area="analytics",
        specialization="data_analyst",
        work_format=["remote"],
    )
    base.update(overrides)
    return VacancyInput(**base)


# ── §3.2 AHP-веса: проверка нормировки и согласованности ─────────────────────

def test_ahp_weights_sum_to_one():
    total = (
        settings.weight_category
        + settings.weight_specialization
        + settings.weight_skills
        + settings.weight_salary
        + settings.weight_seniority
        + settings.weight_format
        + settings.weight_location
    )
    assert total == pytest.approx(1.0, abs=1e-3)


def test_skills_and_specialization_dominate_weights():
    """После упрощения профиля навыки и специализация — самые сильные признаки."""
    weights = {
        "skills": settings.weight_skills,
        "specialization": settings.weight_specialization,
        "category": settings.weight_category,
        "salary": settings.weight_salary,
        "seniority": settings.weight_seniority,
        "format": settings.weight_format,
        "location": settings.weight_location,
    }
    top_two = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:2]
    assert {k for k, _ in top_two} == {"skills", "specialization"}


# ── §3.1 sub-scores ───────────────────────────────────────────────────────────

def test_category_match_returns_one():
    assert category_score(_profile(), _vacancy()) == 1.0


def test_category_family_returns_smoothed_score():
    p = _profile(preferred_categories=["it"])
    v = _vacancy(profession_area="analytics")
    assert category_score(p, v) == pytest.approx(settings.category_family_score)


def test_category_mismatch_returns_zero():
    p = _profile(preferred_categories=["medicine"], target_industry=None)
    assert category_score(p, _vacancy()) == 0.0


def test_category_unknown_returns_neutral_half():
    p = _profile(preferred_categories=[])
    assert category_score(p, _vacancy(profession_area=None)) == 0.5


def test_specialization_neighbor_returns_smoothed_score():
    p = _profile(preferred_specializations=["business_analyst"])
    v = _vacancy(specialization="data_analyst")
    assert specialization_score(p, v) == pytest.approx(settings.spec_neighbor_score)


def test_skill_score_full_coverage():
    sk, matched, missing = skill_score({"python", "sql"}, {"python", "sql"})
    assert sk == 1.0
    assert matched == ["python", "sql"]
    assert missing == []


def test_skill_score_empty_vacancy_returns_neutral():
    sk, _, _ = skill_score({"python"}, set())
    assert sk == 0.30


def test_seniority_one_step_promotion_gets_higher_score():
    p = _profile(seniority="middle")
    assert seniority_score(p, "senior") == 0.70


def test_salary_overlap_full_returns_one():
    assert salary_score(_profile(salary_from=200_000, salary_to=300_000), 220_000, 280_000) == pytest.approx(0.6, abs=0.05)


# ── §3 интеграционный тест: категория важнее навыков ──────────────────────────

def test_category_match_dominates_pure_skill_match():
    """Вакансия в категории пользователя со средними навыками побеждает
    вакансию в чужой категории даже при идеальном покрытии навыков."""
    profile = _profile(preferred_categories=["analytics"], preferred_specializations=["data_analyst"])
    vac_correct = _vacancy(profession_area="analytics", specialization="data_analyst", skills=["python"])
    vac_wrong = _vacancy(profession_area="medicine", specialization=None, skills=["python", "sql"])

    request = ScoreRequest(profile=profile, vacancies=[vac_correct, vac_wrong])
    response = run_scoring(request)

    by_id = {str(r.vacancy_id): r for r in response.results}
    s_correct = by_id[str(vac_correct.vacancy_id)].score
    s_wrong = by_id[str(vac_wrong.vacancy_id)].score
    assert s_correct > s_wrong


# ── §4 поведенческий скор ────────────────────────────────────────────────────

def test_behavior_score_neutral_when_no_history():
    bh = BehaviorInput()
    score, components = behavior_score(bh, _vacancy(), {"python"})
    assert score == pytest.approx(0.5)
    assert components["beta_category"] == 0.0


def test_behavior_score_pushes_up_for_loved_category():
    bh = BehaviorInput(
        total_signals=5,
        category_pref={"analytics": 0.8},
        specialization_pref={"data_analyst": 0.7},
        skill_pref={"python": 0.5},
        title_token_pref={"аналитик": 0.6},
    )
    score, _ = behavior_score(bh, _vacancy(), {"python"})
    assert score > 0.5


def test_behavior_score_pushes_down_for_disliked_category():
    bh = BehaviorInput(
        total_signals=5,
        category_pref={"analytics": -0.8},
        specialization_pref={"data_analyst": -0.7},
    )
    score, _ = behavior_score(bh, _vacancy(), {"python"})
    assert score < 0.5


# ── §5 адаптивное смешивание ─────────────────────────────────────────────────

def test_trust_at_zero_is_zero():
    assert _trust(0) == 0.0


def test_trust_at_n0_is_half():
    assert _trust(int(settings.behavior_trust_n0)) == pytest.approx(0.5)


def test_trust_grows_monotonically():
    values = [_trust(n) for n in (0, 1, 2, 5, 10, 50, 200)]
    assert all(b >= a for a, b in zip(values, values[1:]))


def test_zero_signals_gives_pure_profile_score():
    """При N=0 должно выполняться S = P · M = P · 1 = P."""
    profile = _profile()
    vac = _vacancy()
    request = ScoreRequest(profile=profile, vacancies=[vac])
    response = run_scoring(request)
    r = response.results[0]
    assert r.tau == 0.0
    assert r.multiplier == 1.0
    assert r.score == pytest.approx(r.base_score, abs=1e-3)


def test_many_signals_gives_high_trust():
    bh = BehaviorInput(total_signals=50)
    request = ScoreRequest(profile=_profile(), vacancies=[_vacancy()], behavior=bh)
    response = run_scoring(request)
    assert response.results[0].tau >= 0.9


# ── §7 прямой override ───────────────────────────────────────────────────────

def test_direct_positive_override_floors_score():
    vac = _vacancy(profession_area="medicine", specialization=None, skills=["bash"])
    bh = BehaviorInput(total_signals=10, positive_vacancy_ids=[str(vac.vacancy_id)])
    request = ScoreRequest(profile=_profile(), vacancies=[vac], behavior=bh)
    r = run_scoring(request).results[0]
    assert r.direct_signal == 1.0
    assert r.score >= settings.direct_positive_floor


def test_direct_negative_override_caps_score():
    vac = _vacancy()
    bh = BehaviorInput(total_signals=10, negative_vacancy_ids=[str(vac.vacancy_id)])
    request = ScoreRequest(profile=_profile(), vacancies=[vac], behavior=bh)
    r = run_scoring(request).results[0]
    assert r.direct_signal == -1.0
    assert r.score <= settings.direct_negative_ceiling * settings.direct_negative_multiplier + 1e-4


# ── §6 мультипликатор M(u, v) ────────────────────────────────────────────────

def test_multiplier_disabled_at_zero_trust():
    bh = BehaviorInput(total_signals=0, skill_pref={"python": 0.5})
    request = ScoreRequest(profile=_profile(), vacancies=[_vacancy()], behavior=bh)
    r = run_scoring(request).results[0]
    assert r.multiplier == 1.0


def test_negative_skill_penalty_reduces_score():
    """Если все навыки вакансии — «холодные» (есть отрицательные сигналы),
    мультипликатор < 1 и итоговый скор просаживается."""
    vac = _vacancy(skills=["kubernetes", "rust"])
    bh = BehaviorInput(
        total_signals=10,
        skill_pref={"kubernetes": -0.6, "rust": -0.7},
    )
    request = ScoreRequest(profile=_profile(), vacancies=[vac], behavior=bh)
    r = run_scoring(request).results[0]
    assert r.multiplier < 1.0
    assert r.score < r.base_score


def test_positive_skill_reward_increases_score_modestly():
    vac = _vacancy(skills=["python", "sql"])
    bh = BehaviorInput(
        total_signals=10,
        skill_pref={"python": 0.6, "sql": 0.7},
        category_pref={"analytics": 0.6},
        specialization_pref={"data_analyst": 0.6},
    )
    request = ScoreRequest(profile=_profile(), vacancies=[vac], behavior=bh)
    r = run_scoring(request).results[0]
    assert r.multiplier > 1.0
    assert r.behavior_score > 0.5


# ── Интеграция всех компонентов ──────────────────────────────────────────────

def test_full_pipeline_orders_correctly():
    """Лайкнутая вакансия → жёсткий топ (≥0.95);
    «не подходит» → жёсткое дно (≤0.02);
    «обычная» аналитика — где-то между, но всегда выше disliked."""
    profile = _profile()
    vac_loved = _vacancy(title="Senior Data Analyst")
    vac_neutral = _vacancy(
        title="Системный администратор",
        company="Other Co",
        profession_area="it",
        specialization=None,
        skills=["bash"],
    )
    vac_hated = _vacancy(
        title="Backend Engineer",
        profession_area="it",
        specialization="backend_developer",
        skills=["go", "kubernetes"],
    )

    bh = BehaviorInput(
        total_signals=8,
        category_pref={"analytics": 0.7, "it": -0.3},
        specialization_pref={"data_analyst": 0.7, "backend_developer": -0.5},
        skill_pref={"sql": 0.5, "kubernetes": -0.5},
        title_token_pref={"аналитик": 0.5, "backend": -0.5},
        positive_vacancy_ids=[str(vac_loved.vacancy_id)],
        negative_vacancy_ids=[str(vac_hated.vacancy_id)],
    )

    request = ScoreRequest(
        profile=profile, vacancies=[vac_loved, vac_neutral, vac_hated], behavior=bh
    )
    response = run_scoring(request)
    by_id = {str(r.vacancy_id): r for r in response.results}

    s_loved = by_id[str(vac_loved.vacancy_id)].score
    s_neutral = by_id[str(vac_neutral.vacancy_id)].score
    s_hated = by_id[str(vac_hated.vacancy_id)].score

    assert s_loved >= 0.95
    assert s_hated <= 0.02
    assert s_neutral > s_hated
