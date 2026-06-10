"""GET /api/recommendations — AI-generated business recommendations."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.core.decision_engine import generate_recommendations
from app.schemas.recommendation import RecommendationSchema

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/recommendations", response_model=list[RecommendationSchema])
def get_recommendations() -> list[RecommendationSchema]:
    """
    Return a ranked list of AI-generated business recommendations.

    Combines:
      - Forecast trend analysis
      - Inventory level signals
      - Anomaly detection outputs
      - Price elasticity rules
    """
    try:
        recs = generate_recommendations()
        return [
            RecommendationSchema(
                id=r["id"],
                type=r["type"],
                title=r["title"],
                confidence=r["confidence"],
                explanation=r["explanation"],
                impact=r["impact"],
                priority=r.get("priority", "medium"),
            )
            for r in recs
        ]
    except Exception as exc:
        logger.exception("Recommendations failed: %s", exc)
        raise HTTPException(status_code=500, detail="Decision engine error.")
