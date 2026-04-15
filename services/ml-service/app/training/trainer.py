"""
Bootstrap training: synthetic user–vacancy pairs labeled with Phase-1 content scores.
Enough to validate the pipeline; replace with real LambdaRank data later.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from uuid import uuid4

import lightgbm as lgb
import numpy as np

from ..ranking.feature_extractor import FEATURE_ORDER, FeatureExtractor
from ..schemas import ScoreRequest, UserProfileInput, VacancyInput
from ..scoring import run_scoring

logger = logging.getLogger(__name__)

SKILL_POOL = [
    "python",
    "sql",
    "aws",
    "docker",
    "kubernetes",
    "react",
    "typescript",
    "java",
    "go",
    "cpp",
    "machine learning",
    "pandas",
    "spark",
    "kafka",
    "redis",
    "postgresql",
    "mongodb",
    "git",
    "linux",
    "django",
    "fastapi",
]

TITLES = [
    "Backend Engineer",
    "Data Engineer",
    "ML Engineer",
    "Fullstack Developer",
    "DevOps Engineer",
    "QA Automation",
    "Product Analyst",
]

LOCATIONS = [
    "Moscow",
    "Saint Petersburg",
    "Remote",
    "Казань",
    "hybrid Moscow",
]


def _random_profile() -> UserProfileInput:
    return UserProfileInput(
        user_id=uuid4(),
        skills=random.sample(SKILL_POOL, k=random.randint(2, 9)),
        preferred_locations=random.sample(LOCATIONS, k=random.randint(1, 2)),
        work_formats=random.sample(["remote", "office", "hybrid"], k=1),
        target_roles=random.sample(TITLES, k=random.randint(1, 2)),
        salary_from=random.randint(80_000, 200_000),
        salary_to=random.randint(200_000, 450_000),
        seniority=random.choice(["intern", "junior", "middle", "senior", "lead"]),
    )


def _make_vacancy_pool(n: int = 70) -> list[VacancyInput]:
    pool: list[VacancyInput] = []
    for _ in range(n):
        sf = random.randint(100_000, 180_000)
        st = sf + random.randint(20_000, 200_000)
        pool.append(
            VacancyInput(
                vacancy_id=uuid4(),
                title=random.choice(TITLES),
                company=f"Company-{random.randint(1, 500)}",
                location=random.choice(LOCATIONS),
                salary_from=sf,
                salary_to=st,
                seniority=random.choice(["junior", "middle", "senior", "lead"]),
                skills=random.sample(SKILL_POOL, k=random.randint(2, 10)),
                employment_type=random.choice(["full_time", "part_time", "contract"]),
                description=random.choice(
                    [
                        "Build APIs and microservices",
                        "Data pipelines and ETL",
                        "React dashboard and Node backend",
                        "Kubernetes and cloud infrastructure",
                    ]
                ),
            )
        )
    return pool


def train_and_save(model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    extractor = FeatureExtractor()
    vac_pool = _make_vacancy_pool(72)
    rng = random.Random(42)

    X_rows: list[np.ndarray] = []
    y_vals: list[float] = []

    n_users = 50
    vacs_per_user = 32
    for _ in range(n_users):
        profile = _random_profile()
        subset = rng.sample(vac_pool, k=min(vacs_per_user, len(vac_pool)))
        req = ScoreRequest(profile=profile, vacancies=subset)
        resp = run_scoring(req)
        scores_by_id = {str(r.vacancy_id): float(r.score) for r in resp.results}
        pd = profile.model_dump(mode="json")
        for vac in subset:
            vd = vac.model_dump(mode="json")
            cid = str(vac.vacancy_id)
            label = scores_by_id.get(cid, 0.0) + random.gauss(0, 0.015)
            label = max(0.0, min(1.0, label))
            cb = scores_by_id.get(cid, 0.0)
            row = extractor.extract_row(pd, vd, {}, {}, cb)
            X_rows.append(row)
            y_vals.append(label)

    X = np.vstack(X_rows)
    y = np.array(y_vals, dtype=np.float64)
    train_data = lgb.Dataset(X, label=y, feature_name=FEATURE_ORDER)

    params = {
        "objective": "regression",
        "metric": "l2",
        "verbosity": -1,
        "num_leaves": 31,
        "learning_rate": 0.06,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.85,
        "bagging_freq": 3,
        "max_depth": 6,
        "min_data_in_leaf": 8,
    }
    booster = lgb.train(params, train_data, num_boost_round=120)
    model_path = model_dir / "lightgbm_ranker.txt"
    booster.save_model(str(model_path))
    meta_path = model_dir / "feature_order.json"
    meta_path.write_text(json.dumps({"feature_order": FEATURE_ORDER}, indent=2), encoding="utf-8")
    logger.info("Trained default LightGBM ranker: %s samples → %s", len(y_vals), model_path)


def ensure_trained_model(model_dir: str | Path) -> None:
    root = Path(model_dir)
    model_path = root / "lightgbm_ranker.txt"
    meta_path = root / "feature_order.json"
    stale = True
    if model_path.is_file() and meta_path.is_file():
        try:
            saved = json.loads(meta_path.read_text(encoding="utf-8"))
            stale = saved.get("feature_order") != FEATURE_ORDER
        except (json.JSONDecodeError, OSError):
            stale = True
    if not stale:
        return
    if model_path.is_file():
        model_path.unlink(missing_ok=True)
    if meta_path.is_file():
        meta_path.unlink(missing_ok=True)
    logger.info("Training synthetic ranker (missing model or feature set changed)…")
    train_and_save(root)
