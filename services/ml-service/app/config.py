from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    """Настройки скоринг-сервиса.

    Алгоритм: ``hybrid_ahp_v3`` — см. ``docs/recommendation_model_v3.md`` для
    математического обоснования всех весов и параметров.

    Профильный скор P(u, v) — взвешенная сумма 7 признаков (навыки,
    специализация, категория, seniority, зарплата, локация, формат).
    После упрощения профиля (структурированные поля вместо свободного текста)
    признак role_score удалён, а его вес перераспределён между остальными.
    Веса получены методом анализа иерархий (AHP, Saaty 1980); сумма = 1.0.
    """

    service_name: str = "ml-service"
    version: str = "0.4.0"
    algorithm_name: str = "hybrid_ahp_v3"

    # ── AHP-веса 7 признаков (сумма = 1.0) ────────────────────────────────
    weight_skills: float = 0.50
    weight_specialization: float = 0.26
    weight_category: float = 0.10
    weight_seniority: float = 0.07
    weight_salary: float = 0.04
    weight_location: float = 0.02
    weight_format: float = 0.01

    # ── Поведенческая компонента B(u, v) ─────────────────────────────────
    # Веса 4 поведенческих осей (см. §4.4 модели). Сумма = 1.0.
    behavior_alpha_category: float = 0.32
    behavior_alpha_specialization: float = 0.32
    behavior_alpha_skills: float = 0.22
    behavior_alpha_title: float = 0.14

    # ── Адаптивное смешивание профиля и поведения ────────────────────────
    # τ(N) = N / (N + N0). N0 — «вес априора» в Beta-Binomial credibility.
    # При N0 = 5: τ(5) = 0.5, τ(15) = 0.75, τ(45) = 0.9.
    behavior_trust_n0: float = 5.0

    # ── Мультипликатор M(u, v) — мягкий буст/штраф по навыкам и тайтлу ───
    multiplier_min: float = 0.20
    multiplier_max: float = 1.50
    multiplier_skill_reward: float = 0.35
    multiplier_title_reward: float = 0.25
    multiplier_skill_penalty: float = 0.80
    multiplier_title_penalty: float = 0.55
    # Порог, выше/ниже которого навык считается «горячим» / «холодным».
    multiplier_pos_skill_threshold: float = 0.20
    multiplier_neg_skill_threshold: float = -0.20

    # ── Прямой override ───────────────────────────────────────────────────
    direct_positive_floor: float = 0.95
    direct_negative_ceiling: float = 0.15
    direct_negative_multiplier: float = 0.10

    # ── Полу-период затухания / шринкеджи (используется на стороне
    # recommendation-service при сборке поведенческого payload, дублируется
    # здесь для документации).
    time_decay_half_life_days: float = 90.0
    shrinkage_lambda_category: float = 1.0
    shrinkage_lambda_specialization: float = 1.0
    shrinkage_lambda_skill: float = 2.0
    shrinkage_lambda_title: float = 3.0

    # ── Бонусы «соседних» категорий и специализаций ──────────────────────
    category_family_score: float = 0.6
    spec_neighbor_score: float = 0.7

    # ── Лимиты и пагинация ───────────────────────────────────────────────
    max_candidates: int = 1000
    # top_n должен быть ≥ top_n_store на стороне recommendation-service,
    # иначе пользователь увидит укороченную ленту.
    top_n: int = 200
    skill_gap_top_n: int = 20

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = MLSettings()
