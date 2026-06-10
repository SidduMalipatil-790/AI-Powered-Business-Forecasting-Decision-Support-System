"""
Forecasting Engine — ARIMA (primary) with PSO-tuned hyperparameters.

Per-product models are trained once on startup and cached in memory.
The engine exposes a single `forecast(product_id, horizon)` function that
returns the ForecastResponse-compatible dict.

Confidence intervals are derived from the ARIMA model's built-in
prediction intervals (95% CI).
"""
from __future__ import annotations

import logging
import warnings
from datetime import date, timedelta
from typing import TypedDict

import numpy as np
import pandas as pd

from app.core.data_loader import get_product_df, resolve_product_id, PRODUCT_MAP
from app.core.pso_optimizer import tune_arima

logger = logging.getLogger(__name__)

# In-memory model cache: product_id → fitted ARIMA result
_model_cache: dict[str, object] = {}
_pso_params_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# TypedDict return shapes
# ---------------------------------------------------------------------------

class ForecastPointDict(TypedDict):
    date: str
    forecast: float
    lower: float
    upper: float
    actual: float | None


class ForecastResultDict(TypedDict):
    horizon: int
    product: str
    points: list[ForecastPointDict]
    summary: dict
    explanation: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def warm_up_models() -> None:
    """Pre-train models for all products on startup."""
    for name, pid in PRODUCT_MAP.items():
        try:
            _get_or_train(pid)
            logger.info("Model ready for %s (%s)", name, pid)
        except Exception as exc:
            logger.warning("Model warm-up failed for %s: %s", name, exc)


def forecast(product_name: str, horizon: int) -> ForecastResultDict:
    """
    Generate a `horizon`-day ahead forecast for `product_name`.
    Returns a dict matching ForecastResponse schema.
    """
    product_id = resolve_product_id(product_name)
    df = get_product_df(product_id)
    series = df["sales"].values.astype(float)

    fit, params = _get_or_train(product_id)
    p, d, q = params["p"], params["d"], params["q"]

    # Produce forecast with confidence intervals
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fc_result = fit.get_forecast(steps=horizon)
        fc_mean = fc_result.predicted_mean
        ci = fc_result.conf_int(alpha=0.05)  # 95% CI

    # Build date range starting tomorrow
    last_date = df["date"].max()
    if pd.isna(last_date):
        last_date = date.today()
    else:
        last_date = last_date.date() if hasattr(last_date, "date") else last_date

    future_dates = [last_date + timedelta(days=i + 1) for i in range(horizon)]

    points: list[ForecastPointDict] = []
    for i, d_date in enumerate(future_dates):
        mean_val = float(max(0, fc_mean.iloc[i] if hasattr(fc_mean, "iloc") else fc_mean[i]))
        lower_val = float(max(0, ci.iloc[i, 0] if hasattr(ci, "iloc") else ci[i][0]))
        upper_val = float(max(0, ci.iloc[i, 1] if hasattr(ci, "iloc") else ci[i][1]))
        points.append({
            "date": d_date.isoformat(),
            "forecast": round(mean_val, 2),
            "lower": round(lower_val, 2),
            "upper": round(upper_val, 2),
            "actual": None,
        })

    forecasts = [p["forecast"] for p in points]
    mean_fc = float(np.mean(forecasts))
    min_fc = float(np.min(forecasts))
    max_fc = float(np.max(forecasts))

    # MAPE on training holdout (last 20%)
    mape = _compute_holdout_mape(series, p, d, q)

    explanation = (
        f"ARIMA({p},{d},{q}) model trained on {len(series)} observations. "
        f"PSO-optimised order achieved {params.get('mape', mape):.2f}% MAPE on holdout. "
        f"95% confidence intervals widen over the {horizon}-day horizon as uncertainty compounds."
    )

    return {
        "horizon": horizon,
        "product": product_name,
        "points": points,
        "summary": {
            "mean": round(mean_fc, 2),
            "min": round(min_fc, 2),
            "max": round(max_fc, 2),
            "mape": round(mape, 2),
        },
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_train(product_id: str):
    """Return (fitted_model, pso_params), training if not cached."""
    if product_id in _model_cache:
        return _model_cache[product_id], _pso_params_cache[product_id]

    df = get_product_df(product_id)
    series = df["sales"].values.astype(float)

    # PSO-tune the ARIMA order
    params = tune_arima(series, product_id)
    p, d, q = params["p"], params["d"], params["q"]

    logger.info("Training ARIMA(%d,%d,%d) for product %s…", p, d, q, product_id)
    from statsmodels.tsa.arima.model import ARIMA

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ARIMA(series, order=(p, d, q))
        fit = model.fit()

    _model_cache[product_id] = fit
    _pso_params_cache[product_id] = params
    logger.info("ARIMA model cached for %s", product_id)
    return fit, params


def _compute_holdout_mape(series: np.ndarray, p: int, d: int, q: int) -> float:
    """Compute MAPE on the last 20% of data as a validation metric."""
    split = int(len(series) * 0.8)
    train, val = series[:split], series[split:]
    n_val = len(val)
    if n_val == 0:
        return 0.0
    try:
        from statsmodels.tsa.arima.model import ARIMA
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = ARIMA(train, order=(p, d, q)).fit()
            fc = m.forecast(steps=n_val)
        mape = float(np.mean(np.abs((val - fc) / (np.abs(val) + 1e-8)))) * 100
        return round(mape, 3)
    except Exception:
        return 0.0


def invalidate_model_cache() -> None:
    """Clear cached models (call after data updates)."""
    _model_cache.clear()
    _pso_params_cache.clear()
