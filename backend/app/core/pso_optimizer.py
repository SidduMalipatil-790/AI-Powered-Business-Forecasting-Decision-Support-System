"""
Particle Swarm Optimization (PSO) for ARIMA/XGBoost hyperparameter tuning.

Pure NumPy implementation — no external PSO library required.

Optimized parameters:
  - For ARIMA: (p, d, q) order  ← discrete, mapped from continuous positions
  - For XGBoost: n_estimators, max_depth, learning_rate, subsample

The PSO minimises MAPE on a held-out validation slice (last 20% of data).
Results are cached to disk as JSON so subsequent starts are instant.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable

import numpy as np

from app.config import PSO_PARTICLES, PSO_ITERATIONS, PSO_CACHE_PATH

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Generic PSO engine
# ---------------------------------------------------------------------------

def pso_minimize(
    objective: Callable[[np.ndarray], float],
    bounds: list[tuple[float, float]],
    n_particles: int = PSO_PARTICLES,
    n_iterations: int = PSO_ITERATIONS,
    w: float = 0.7,    # inertia weight
    c1: float = 1.5,   # cognitive coefficient
    c2: float = 1.5,   # social coefficient
    seed: int = 42,
) -> tuple[np.ndarray, float]:
    """
    Minimise `objective(x)` where x ∈ R^dim subject to `bounds`.

    Returns (best_position, best_score).
    """
    rng = np.random.default_rng(seed)
    dim = len(bounds)
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])

    # Initialise particles
    pos = rng.uniform(lo, hi, size=(n_particles, dim))
    vel = rng.uniform(-(hi - lo), hi - lo, size=(n_particles, dim))

    personal_best_pos = pos.copy()
    personal_best_score = np.full(n_particles, np.inf)
    global_best_pos = pos[0].copy()
    global_best_score = np.inf

    for iteration in range(n_iterations):
        for i in range(n_particles):
            score = objective(pos[i])
            if score < personal_best_score[i]:
                personal_best_score[i] = score
                personal_best_pos[i] = pos[i].copy()
            if score < global_best_score:
                global_best_score = score
                global_best_pos = pos[i].copy()

        # Update velocities and positions
        r1 = rng.random((n_particles, dim))
        r2 = rng.random((n_particles, dim))
        vel = (
            w * vel
            + c1 * r1 * (personal_best_pos - pos)
            + c2 * r2 * (global_best_pos - pos)
        )
        pos = np.clip(pos + vel, lo, hi)

        logger.debug("PSO iter %d/%d — best score: %.4f", iteration + 1, n_iterations, global_best_score)

    return global_best_pos, global_best_score


# ---------------------------------------------------------------------------
# ARIMA-specific PSO
# ---------------------------------------------------------------------------

def tune_arima(series: "np.ndarray", product_id: str) -> dict:
    """
    Use PSO to find best ARIMA (p, d, q) order.
    Returns dict with keys: p, d, q, mape.
    Caches results to disk.
    """
    cache = _load_cache()
    cache_key = f"arima_{product_id}"
    if cache_key in cache:
        logger.info("PSO cache hit for %s", product_id)
        return cache[cache_key]

    logger.info("Running PSO for ARIMA tuning on %s (%d observations)…", product_id, len(series))
    t0 = time.time()

    # Split: last 20% as validation
    split = int(len(series) * 0.8)
    train, val = series[:split], series[split:]
    n_val = len(val)

    def objective(x: np.ndarray) -> float:
        p = max(0, int(round(x[0])))
        d = max(0, int(round(x[1])))
        q = max(0, int(round(x[2])))
        try:
            import warnings
            from statsmodels.tsa.arima.model import ARIMA
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ARIMA(train, order=(p, d, q))
                fit = model.fit()
                forecast = fit.forecast(steps=n_val)
            # MAPE
            actual = val
            mape = float(np.mean(np.abs((actual - forecast) / (np.abs(actual) + 1e-8)))) * 100
            return mape
        except Exception:
            return 999.0

    # Search space: p ∈ [0,3], d ∈ [0,2], q ∈ [0,3]
    bounds = [(0.0, 3.0), (0.0, 2.0), (0.0, 3.0)]
    best_pos, best_score = pso_minimize(objective, bounds)

    result = {
        "p": max(0, int(round(best_pos[0]))),
        "d": max(0, int(round(best_pos[1]))),
        "q": max(0, int(round(best_pos[2]))),
        "mape": round(best_score, 3),
    }

    elapsed = time.time() - t0
    logger.info("PSO done for %s in %.1fs — best order=(%d,%d,%d) MAPE=%.2f%%",
                product_id, elapsed, result["p"], result["d"], result["q"], result["mape"])

    cache[cache_key] = result
    _save_cache(cache)
    return result


# ---------------------------------------------------------------------------
# XGBoost-specific PSO (for surrogate SHAP model)
# ---------------------------------------------------------------------------

def tune_xgboost(X_train: "np.ndarray", y_train: "np.ndarray", product_id: str) -> dict:
    """
    PSO to tune XGBoost hyperparameters.
    Returns dict with xgb_params.
    """
    cache = _load_cache()
    cache_key = f"xgb_{product_id}"
    if cache_key in cache:
        logger.info("XGB PSO cache hit for %s", product_id)
        return cache[cache_key]

    logger.info("Running PSO for XGBoost tuning on %s…", product_id)

    split = int(len(X_train) * 0.8)
    Xtr, Xval = X_train[:split], X_train[split:]
    ytr, yval = y_train[:split], y_train[split:]

    def objective(x: np.ndarray) -> float:
        try:
            import xgboost as xgb
            params = {
                "n_estimators": max(10, int(round(x[0]))),
                "max_depth": max(1, int(round(x[1]))),
                "learning_rate": float(np.clip(x[2], 0.01, 0.5)),
                "subsample": float(np.clip(x[3], 0.5, 1.0)),
                "verbosity": 0,
            }
            m = xgb.XGBRegressor(**params)
            m.fit(Xtr, ytr)
            pred = m.predict(Xval)
            mape = float(np.mean(np.abs((yval - pred) / (np.abs(yval) + 1e-8)))) * 100
            return mape
        except Exception:
            return 999.0

    bounds = [
        (50.0, 300.0),   # n_estimators
        (2.0, 8.0),      # max_depth
        (0.01, 0.3),     # learning_rate
        (0.6, 1.0),      # subsample
    ]
    best_pos, best_score = pso_minimize(objective, bounds)

    result = {
        "n_estimators": max(10, int(round(best_pos[0]))),
        "max_depth": max(1, int(round(best_pos[1]))),
        "learning_rate": round(float(np.clip(best_pos[2], 0.01, 0.5)), 4),
        "subsample": round(float(np.clip(best_pos[3], 0.6, 1.0)), 4),
        "mape": round(best_score, 3),
    }

    logger.info("XGB PSO done for %s — params=%s MAPE=%.2f%%", product_id, result, result["mape"])
    cache[cache_key] = result
    _save_cache(cache)
    return result


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    path = Path(PSO_CACHE_PATH)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(data: dict) -> None:
    path = Path(PSO_CACHE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
