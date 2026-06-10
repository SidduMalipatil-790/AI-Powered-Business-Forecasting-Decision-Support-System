"""
Anomaly Detection Engine using Isolation Forest.

Detects statistical outliers in the sales time series over a rolling window.
For each detected anomaly, computes:
  - anomaly_score   : raw Isolation Forest decision function score
  - delta_pct       : % deviation from 7-day rolling mean
  - severity        : high / medium / low based on score thresholds
  - description     : human-readable explanation
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, timedelta
from typing import TypedDict

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.core.data_loader import get_product_df, PRODUCT_MAP

logger = logging.getLogger(__name__)

# Cache: product_id → (fitted model, scaler, dataframe)
_detector_cache: dict[str, tuple] = {}

# Feature columns fed into Isolation Forest
FEATURE_COLS = [
    "sales",
    "lag_7",
    "rolling_7_mean",
    "rolling_7_std",
    "day_of_week",
    "is_weekend",
]


class AnomalyDict(TypedDict):
    id: str
    date: str
    metric: str
    severity: str
    delta: float
    description: str
    anomaly_score: float


def detect_anomalies(
    product_id: str = "ALL",
    lookback_days: int = 30,
    contamination: float = 0.1,
) -> list[AnomalyDict]:
    """
    Detect anomalies in the last `lookback_days` for `product_id`.
    Returns a list of AnomalyDict sorted by severity desc, date desc.
    """
    df = get_product_df(product_id)
    df = df.dropna(subset=FEATURE_COLS)

    if len(df) < 30:
        logger.warning("Not enough data for anomaly detection on %s", product_id)
        return []

    # Train Isolation Forest on all available data
    model, scaler = _get_or_train_detector(product_id, df, contamination)

    # Score the full dataset
    X = df[FEATURE_COLS].values
    X_scaled = scaler.transform(X)
    scores = model.decision_function(X_scaled)  # higher = more normal
    predictions = model.predict(X_scaled)       # -1 = anomaly, 1 = normal

    df = df.copy()
    df["if_score"] = scores
    df["is_anomaly"] = predictions == -1

    # Filter to lookback window
    cutoff = df["date"].max() - pd.Timedelta(days=lookback_days)
    recent = df[df["date"] >= cutoff].copy()
    anomalies_df = recent[recent["is_anomaly"]].copy()

    if anomalies_df.empty:
        # Return the most extreme points even if no hard anomaly
        anomalies_df = recent.nsmallest(3, "if_score")

    results: list[AnomalyDict] = []
    for _, row in anomalies_df.iterrows():
        score = float(row["if_score"])
        sales = float(row["sales"])
        baseline = float(row["rolling_7_mean"]) if row["rolling_7_mean"] > 0 else sales
        delta_pct = round(((sales - baseline) / (abs(baseline) + 1e-8)) * 100, 1)

        severity = _score_to_severity(score)
        description = _build_description(row, delta_pct, severity, product_id)

        anomaly_id = hashlib.md5(
            f"{product_id}{row['date']}{score}".encode()
        ).hexdigest()[:8]

        results.append({
            "id": f"a_{anomaly_id}",
            "date": row["date"].strftime("%Y-%m-%d"),
            "metric": f"Sales — {_product_metric_name(product_id)}",
            "severity": severity,
            "delta": delta_pct,
            "description": description,
            "anomaly_score": round(score, 4),
        })

    # Sort: high severity first, then by date desc
    severity_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda x: (severity_order[x["severity"]], x["date"]), reverse=False)
    results.sort(key=lambda x: severity_order[x["severity"]])

    return results


def detect_all_anomalies(lookback_days: int = 30) -> list[AnomalyDict]:
    """Detect anomalies across all products and merge."""
    all_anomalies: list[AnomalyDict] = []
    seen_ids: set[str] = set()

    for product_id in PRODUCT_MAP.values():
        try:
            anomalies = detect_anomalies(product_id, lookback_days)
            for a in anomalies:
                if a["id"] not in seen_ids:
                    seen_ids.add(a["id"])
                    all_anomalies.append(a)
        except Exception as exc:
            logger.warning("Anomaly detection failed for %s: %s", product_id, exc)

    # De-duplicate and sort globally
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_anomalies.sort(key=lambda x: (severity_order[x["severity"]], x["date"]))

    # Cap at 15 most important
    return all_anomalies[:15]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_train_detector(product_id: str, df: pd.DataFrame, contamination: float):
    """Return or train (IsolationForest, StandardScaler) pair."""
    if product_id in _detector_cache:
        return _detector_cache[product_id]

    X = df[FEATURE_COLS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    _detector_cache[product_id] = (model, scaler)
    logger.info("Isolation Forest trained for %s (%d rows)", product_id, len(df))
    return model, scaler


def _score_to_severity(score: float) -> str:
    """Map Isolation Forest score to severity label."""
    if score < -0.15:
        return "high"
    elif score < 0.0:
        return "medium"
    else:
        return "low"


def _build_description(row: pd.Series, delta_pct: float, severity: str, product_id: str) -> str:
    direction = "spike" if delta_pct > 0 else "drop"
    abs_delta = abs(delta_pct)
    product_label = _product_metric_name(product_id)
    day = row["date"].strftime("%A")

    if severity == "high":
        prefix = f"Significant {direction} of {abs_delta:.1f}%"
        suffix = "Immediate review recommended."
    elif severity == "medium":
        prefix = f"Notable {direction} of {abs_delta:.1f}%"
        suffix = "Monitor closely over next 3 days."
    else:
        prefix = f"Minor {direction} of {abs_delta:.1f}%"
        suffix = "Within tolerable range but worth tracking."

    return (
        f"{prefix} in {product_label} sales on {day} vs 7-day rolling average. {suffix}"
    )


def _product_metric_name(product_id: str) -> str:
    from app.core.data_loader import ID_TO_NAME
    return ID_TO_NAME.get(product_id, product_id)


def invalidate_detector_cache() -> None:
    _detector_cache.clear()
