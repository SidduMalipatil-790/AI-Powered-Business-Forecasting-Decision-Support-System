"""
SHAP Explainability module.

Trains a lightweight XGBoost surrogate model on the same engineered features
as the ARIMA forecaster, then uses SHAP TreeExplainer to generate
feature importance explanations returned in API responses.
"""
from __future__ import annotations

import logging
from typing import TypedDict

import numpy as np
import pandas as pd

from app.core.data_loader import get_product_df, PRODUCT_MAP
from app.core.pso_optimizer import tune_xgboost

logger = logging.getLogger(__name__)

# Cached XGBoost models and their SHAP explainers
_xgb_cache: dict[str, object] = {}
_explainer_cache: dict[str, object] = {}

FEATURE_COLS = [
    "price", "lag_7", "lag_14", "lag_21",
    "rolling_7_mean", "rolling_7_std",
    "rolling_30_mean", "rolling_30_std",
    "day_of_week", "month", "week_of_year",
    "is_weekend", "quarter",
]

FEATURE_DISPLAY_NAMES = {
    "price": "Price",
    "lag_7": "Last-week sales",
    "lag_14": "2-week-ago sales",
    "lag_21": "3-week-ago sales",
    "rolling_7_mean": "7-day avg",
    "rolling_7_std": "7-day volatility",
    "rolling_30_mean": "30-day avg",
    "rolling_30_std": "30-day volatility",
    "day_of_week": "Day of week",
    "month": "Month",
    "week_of_year": "Week of year",
    "is_weekend": "Weekend effect",
    "quarter": "Quarter",
}


class FeatureImportance(TypedDict):
    feature: str
    importance_pct: float


def get_explanation(product_id: str, top_n: int = 3) -> str:
    """
    Return a human-readable explanation string for the given product's forecast.
    Falls back gracefully if XGBoost/SHAP not available.
    """
    try:
        importances = _get_feature_importances(product_id)
        top = importances[:top_n]
        parts = [f"{f['feature']} ({f['importance_pct']:.0f}%)" for f in top]
        return f"Top forecast drivers: {', '.join(parts)}."
    except Exception as exc:
        logger.warning("Explainer failed for %s: %s", product_id, exc)
        return "Explanation unavailable — model trained with engineered temporal features."


def _get_feature_importances(product_id: str) -> list[FeatureImportance]:
    """Train or retrieve XGBoost model, compute SHAP values, return sorted importances."""
    if product_id not in _xgb_cache:
        _train_surrogate(product_id)

    xgb_model = _xgb_cache[product_id]

    try:
        import shap
        explainer = _explainer_cache.get(product_id)
        if explainer is None:
            explainer = shap.TreeExplainer(xgb_model)
            _explainer_cache[product_id] = explainer

        df = get_product_df(product_id).dropna(subset=FEATURE_COLS)
        X = df[FEATURE_COLS].values
        shap_values = explainer.shap_values(X)

        # Mean |SHAP| per feature
        mean_abs = np.mean(np.abs(shap_values), axis=0)
        total = mean_abs.sum() + 1e-10
        importances = [
            {
                "feature": FEATURE_DISPLAY_NAMES.get(col, col),
                "importance_pct": round(float(mean_abs[i] / total) * 100, 1),
            }
            for i, col in enumerate(FEATURE_COLS)
        ]

    except ImportError:
        # Fallback: XGBoost native feature importance
        imp = xgb_model.feature_importances_
        total = imp.sum() + 1e-10
        importances = [
            {
                "feature": FEATURE_DISPLAY_NAMES.get(FEATURE_COLS[i], FEATURE_COLS[i]),
                "importance_pct": round(float(imp[i] / total) * 100, 1),
            }
            for i in range(len(FEATURE_COLS))
        ]

    importances.sort(key=lambda x: x["importance_pct"], reverse=True)
    return importances


def _train_surrogate(product_id: str) -> None:
    """Train XGBoost surrogate for SHAP explainability."""
    import xgboost as xgb

    df = get_product_df(product_id).dropna(subset=FEATURE_COLS + ["sales"])
    X = df[FEATURE_COLS].values
    y = df["sales"].values

    # PSO-tune the surrogate
    params = tune_xgboost(X, y, product_id)

    model = xgb.XGBRegressor(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        learning_rate=params["learning_rate"],
        subsample=params["subsample"],
        verbosity=0,
        random_state=42,
    )
    model.fit(X, y)
    _xgb_cache[product_id] = model
    logger.info("XGBoost surrogate trained for %s", product_id)


def warm_up_explainers() -> None:
    """Pre-train surrogate models for all products."""
    for pid in PRODUCT_MAP.values():
        try:
            _train_surrogate(pid)
        except Exception as exc:
            logger.warning("Explainer warm-up failed for %s: %s", pid, exc)
