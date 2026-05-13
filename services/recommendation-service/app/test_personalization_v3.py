"""Unit-тесты на личностную (поведенческую) надстройку модели v3.

Тестируются:
  • временное затухание (T_½ = 90 дней) — ``_decay_weight``;
  • байесовское сглаживание ``_Aggregator.shrink(λ)``;
  • сборка AffinityProfile из БД (UserLikedVacancy + UserVacancySignal);
  • live-скоринг ``score_with_personalization``;
  • прямой override (положительный/отрицательный).

Запуск:
    cd services/recommendation-service && pytest app/test_personalization_v3.py -q
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from .personalization import (
    AffinityProfile,
    BEHAVIOR_TRUST_N0,
    DIRECT_NEGATIVE_CEILING,
    DIRECT_NEGATIVE_MULTIPLIER,
    DIRECT_POSITIVE_FLOOR,
    SHRINKAGE_CATEGORY,
    SHRINKAGE_SKILL,
    _Aggregator,
    _decay_weight,
    _tokens,
    behavior_score_live,
    multiplier_live,
    score_with_personalization,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


class _FakeLike:
    def __init__(self, *, vacancy_id, liked_at, category, specialization, skills, title):
        self.vacancy_id = vacancy_id
        self.liked_at = liked_at
        self.unliked_at = None
        self.vacancy_category = category
        self.vacancy_specialization = specialization
        self.vacancy_skills = skills
        self.vacancy_title = title


class _FakeSignal:
    def __init__(self, *, vacancy_id, sentiment, updated_at, category, specialization, skills, title):
        self.vacancy_id = vacancy_id
        self.sentiment = sentiment
        self.kind = "interested" if sentiment > 0 else "not_interested"
        self.updated_at = updated_at
        self.created_at = updated_at
        self.vacancy_category = category
        self.vacancy_specialization = specialization
        self.vacancy_skills = skills
        self.vacancy_title = title


class _FakeQuery:
    def __init__(self, items):
        self._items = items

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._items)


class _FakeDB:
    def __init__(self, likes=None, signals=None, feedbacks=None):
        self._likes = list(likes or [])
        self._signals = list(signals or [])
        self._feedbacks = list(feedbacks or [])

    def query(self, model):
        from .models import UserLikedVacancy, UserVacancySignal, VacancyRecommendation
        if model is UserLikedVacancy:
            return _FakeQuery(self._likes)
        if model is UserVacancySignal:
            return _FakeQuery(self._signals)
        if model is VacancyRecommendation:
            return _FakeQuery(self._feedbacks)
        return _FakeQuery([])

    def rollback(self):  # noqa: D401
        pass


# ── §4.2 — затухание ω(Δt) = 2^(−Δt/T_½) ────────────────────────────────────

def test_decay_weight_zero_age_is_one():
    now = datetime(2026, 5, 1)
    assert _decay_weight(now, now) == pytest.approx(1.0)


def test_decay_weight_half_life_is_half():
    now = datetime(2026, 5, 1)
    earlier = now - timedelta(days=90)
    assert _decay_weight(earlier, now) == pytest.approx(0.5)


def test_decay_weight_decreases_monotonically():
    now = datetime(2026, 5, 1)
    weights = [
        _decay_weight(now - timedelta(days=d), now) for d in (0, 30, 60, 90, 180, 365)
    ]
    assert all(b < a for a, b in zip(weights, weights[1:]))


def test_decay_missing_time_treated_as_fresh():
    assert _decay_weight(None, datetime.utcnow()) == 1.0


# ── §4.3 — байесовское сглаживание ───────────────────────────────────────────

def test_shrinkage_single_signal_does_not_reach_one():
    agg = _Aggregator()
    agg.add("python", 1.0, weight=1.0)
    pref = agg.shrink(SHRINKAGE_SKILL)
    assert pref["python"] == pytest.approx(1.0 / (1.0 + SHRINKAGE_SKILL))


def test_shrinkage_many_signals_converges_to_empirical_mean():
    agg = _Aggregator()
    for _ in range(50):
        agg.add("python", 1.0, weight=1.0)
    pref = agg.shrink(SHRINKAGE_SKILL)
    assert pref["python"] == pytest.approx(50.0 / (50.0 + SHRINKAGE_SKILL), abs=1e-6)
    assert pref["python"] > 0.95


def test_shrinkage_clipped_to_unit_range():
    agg = _Aggregator()
    agg.add("python", -1.0, weight=100.0)
    pref = agg.shrink(SHRINKAGE_SKILL)
    assert pref["python"] >= -1.0
    assert pref["python"] < 0.0


# ── Сборка AffinityProfile из «БД» ───────────────────────────────────────────

def test_build_affinity_aggregates_categories_and_specializations():
    from .personalization import build_affinity

    now = datetime(2026, 5, 1)
    likes = [
        _FakeLike(
            vacancy_id=uuid4(),
            liked_at=now - timedelta(days=10),
            category="analytics",
            specialization="data_analyst",
            skills=["sql", "python"],
            title="Аналитик данных",
        ),
        _FakeLike(
            vacancy_id=uuid4(),
            liked_at=now - timedelta(days=5),
            category="analytics",
            specialization="data_analyst",
            skills=["python", "tableau"],
            title="Data Analyst",
        ),
    ]
    signals = [
        _FakeSignal(
            vacancy_id=uuid4(),
            sentiment=-1.0,
            updated_at=now - timedelta(days=1),
            category="it",
            specialization="backend_developer",
            skills=["go"],
            title="Backend Engineer",
        )
    ]

    db = _FakeDB(likes=likes, signals=signals)
    aff = build_affinity(db, user_id=uuid4(), now=now)

    assert aff.total_signals == 3
    assert aff.category_pref["analytics"] > 0
    assert aff.category_pref["it"] < 0
    assert aff.specialization_pref["data_analyst"] > 0
    assert aff.specialization_pref["backend_developer"] < 0
    assert "python" in aff.skill_pref


def test_build_affinity_records_direct_overrides():
    from .personalization import build_affinity

    pos_id = uuid4()
    neg_id = uuid4()
    now = datetime.utcnow()
    likes = [
        _FakeLike(
            vacancy_id=pos_id,
            liked_at=now,
            category="analytics",
            specialization="data_analyst",
            skills=["sql"],
            title="Loved",
        )
    ]
    signals = [
        _FakeSignal(
            vacancy_id=neg_id,
            sentiment=-1.0,
            updated_at=now,
            category="it",
            specialization=None,
            skills=[],
            title="Hated",
        )
    ]
    aff = build_affinity(_FakeDB(likes=likes, signals=signals), user_id=uuid4(), now=now)
    assert str(pos_id) in aff.positive_vacancy_ids
    assert str(neg_id) in aff.negative_vacancy_ids


# ── Адаптивное доверие τ(N) ──────────────────────────────────────────────────

def test_trust_at_zero_signals_is_zero():
    aff = AffinityProfile(total_signals=0)
    assert aff.trust == 0.0


def test_trust_at_n0_signals_is_half():
    aff = AffinityProfile(total_signals=int(BEHAVIOR_TRUST_N0))
    assert aff.trust == pytest.approx(0.5)


# ── Live-скор ────────────────────────────────────────────────────────────────

def test_score_with_zero_signals_returns_base():
    aff = AffinityProfile(total_signals=0)
    final, boost, direct = score_with_personalization(
        aff,
        base_score=0.7,
        vacancy_id=uuid4(),
        vacancy_skills=["python"],
        vacancy_title="Backend",
        vacancy_category="it",
        vacancy_specialization="backend_developer",
    )
    assert final == pytest.approx(0.7, abs=1e-3)
    assert direct is None


def test_score_pushes_up_for_aligned_vacancy_when_warm():
    aff = AffinityProfile(
        total_signals=10,
        category_pref={"analytics": 0.7},
        specialization_pref={"data_analyst": 0.7},
        skill_pref={"sql": 0.6, "python": 0.5},
        title_token_pref={"аналитик": 0.5},
    )
    final, _, direct = score_with_personalization(
        aff,
        base_score=0.5,
        vacancy_id=uuid4(),
        vacancy_skills=["sql", "python"],
        vacancy_title="Аналитик данных",
        vacancy_category="analytics",
        vacancy_specialization="data_analyst",
    )
    assert final > 0.5
    assert direct is None


def test_score_pushes_down_for_disliked_vacancy():
    aff = AffinityProfile(
        total_signals=10,
        category_pref={"it": -0.7},
        specialization_pref={"backend_developer": -0.7},
        skill_pref={"kubernetes": -0.7, "go": -0.6},
        title_token_pref={"backend": -0.6},
    )
    final, _, _ = score_with_personalization(
        aff,
        base_score=0.5,
        vacancy_id=uuid4(),
        vacancy_skills=["kubernetes", "go"],
        vacancy_title="Backend Engineer",
        vacancy_category="it",
        vacancy_specialization="backend_developer",
    )
    assert final < 0.5


def test_direct_positive_override_floors_at_095():
    vid = uuid4()
    aff = AffinityProfile(total_signals=5, positive_vacancy_ids={str(vid)})
    final, _, direct = score_with_personalization(
        aff,
        base_score=0.10,
        vacancy_id=vid,
        vacancy_skills=[],
        vacancy_title="",
        vacancy_category=None,
        vacancy_specialization=None,
    )
    assert direct == 1.0
    assert final >= DIRECT_POSITIVE_FLOOR


def test_direct_negative_override_caps_score_low():
    vid = uuid4()
    aff = AffinityProfile(total_signals=5, negative_vacancy_ids={str(vid)})
    final, _, direct = score_with_personalization(
        aff,
        base_score=0.95,
        vacancy_id=vid,
        vacancy_skills=[],
        vacancy_title="",
        vacancy_category=None,
        vacancy_specialization=None,
    )
    assert direct == -1.0
    assert final <= DIRECT_NEGATIVE_CEILING * DIRECT_NEGATIVE_MULTIPLIER + 1e-4


def test_behavior_payload_round_trip():
    aff = AffinityProfile(
        total_signals=3,
        category_pref={"analytics": 0.5},
        specialization_pref={"data_analyst": 0.4},
        skill_pref={"python": 0.3},
        title_token_pref={"аналитик": 0.2},
        positive_vacancy_ids={"a", "b"},
        negative_vacancy_ids={"c"},
    )
    payload = aff.to_behavior_payload()
    assert payload["total_signals"] == 3
    assert payload["category_pref"]["analytics"] == 0.5
    assert sorted(payload["positive_vacancy_ids"]) == ["a", "b"]
    assert payload["negative_vacancy_ids"] == ["c"]


# ── Multiplier поведения ─────────────────────────────────────────────────────

def test_multiplier_neutral_when_no_signals():
    aff = AffinityProfile(total_signals=0)
    assert multiplier_live(aff, ["python"], "backend") == 1.0


def test_multiplier_penalizes_disliked_skills():
    aff = AffinityProfile(
        total_signals=10,
        skill_pref={"kubernetes": -0.7, "rust": -0.6},
    )
    m = multiplier_live(aff, ["kubernetes", "rust"], "Backend")
    assert m < 1.0


def test_multiplier_rewards_liked_skills():
    aff = AffinityProfile(
        total_signals=10,
        skill_pref={"sql": 0.6, "python": 0.5},
        title_token_pref={"аналитик": 0.5},
    )
    m = multiplier_live(aff, ["sql", "python"], "Аналитик данных")
    assert m > 1.0


# ── B(u, v) ──────────────────────────────────────────────────────────────────

def test_behavior_score_neutral_at_no_signals():
    aff = AffinityProfile(total_signals=0)
    assert behavior_score_live(aff, "analytics", "data_analyst", ["python"], "Аналитик") == 0.5


def test_behavior_score_in_unit_range():
    aff = AffinityProfile(
        total_signals=20,
        category_pref={"analytics": 1.0},
        specialization_pref={"data_analyst": 1.0},
        skill_pref={"sql": 1.0, "python": 1.0},
        title_token_pref={"аналитик": 1.0},
    )
    s = behavior_score_live(aff, "analytics", "data_analyst", ["sql", "python"], "Аналитик данных")
    assert 0.0 <= s <= 1.0
    assert s == pytest.approx(1.0, abs=1e-6)


def test_tokenizer_strips_stopwords_and_short_words():
    toks = _tokens("Python и SQL для data analyst в bi")
    assert "python" in toks
    assert "sql" in toks
    assert "и" not in toks
    assert "в" not in toks
