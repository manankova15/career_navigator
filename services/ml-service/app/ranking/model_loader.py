"""Load LightGBM booster from disk."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import lightgbm as lgb

from .feature_extractor import FEATURE_ORDER

logger = logging.getLogger(__name__)


def load_ranker(model_dir: str | Path) -> lgb.Booster | None:
    root = Path(model_dir)
    model_path = root / "lightgbm_ranker.txt"
    meta_path = root / "feature_order.json"
    if not model_path.is_file():
        logger.info("No ranker model at %s", model_path)
        return None
    if meta_path.is_file():
        try:
            saved = json.loads(meta_path.read_text(encoding="utf-8"))
            if saved.get("feature_order") != FEATURE_ORDER:
                logger.warning("feature_order.json does not match code; retrain recommended")
        except json.JSONDecodeError:
            logger.warning("Invalid feature_order.json")
    try:
        return lgb.Booster(model_file=str(model_path))
    except Exception as exc:
        logger.error("Failed to load LightGBM model: %s", exc)
        return None
