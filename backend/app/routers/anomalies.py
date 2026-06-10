"""GET /api/anomalies — Isolation Forest anomaly detection results."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.core.anomaly_detector import detect_all_anomalies
from app.schemas.anomaly import AnomalySchema

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/anomalies", response_model=list[AnomalySchema])
def get_anomalies(
    lookback_days: int = Query(default=30, ge=7, le=365, description="Days of history to scan"),
) -> list[AnomalySchema]:
    """
    Return detected anomalies across all products within the lookback window.

    Each anomaly includes:
      - id, date, metric, severity (low/medium/high)
      - delta: % deviation from 7-day rolling mean
      - description: human-readable explanation
      - anomaly_score: raw Isolation Forest decision function score
    """
    try:
        anomalies = detect_all_anomalies(lookback_days=lookback_days)
        return [
            AnomalySchema(
                id=a["id"],
                date=a["date"],
                metric=a["metric"],
                severity=a["severity"],
                delta=a["delta"],
                description=a["description"],
                anomaly_score=a["anomaly_score"],
            )
            for a in anomalies
        ]
    except Exception as exc:
        logger.exception("Anomaly detection failed: %s", exc)
        raise HTTPException(status_code=500, detail="Anomaly detection engine error.")
