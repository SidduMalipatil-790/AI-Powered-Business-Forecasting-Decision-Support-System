"""POST /api/forecast — ARIMA forecast with confidence intervals."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.core.forecaster import forecast as run_forecast
from app.core.explainer import get_explanation
from app.core.data_loader import resolve_product_id
from app.schemas.forecast import ForecastRequest, ForecastResponse, ForecastPoint, ForecastSummary

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_HORIZON = 180
MIN_HORIZON = 1


@router.post("/forecast", response_model=ForecastResponse)
def post_forecast(body: ForecastRequest) -> ForecastResponse:
    """
    Generate a forecast for the requested product and horizon.

    Input:
      - horizon: int (days ahead, 1–180)
      - product: str (display name, e.g. "Wireless Earbuds Pro")

    Output:
      - ForecastResponse with points[], summary, and explanation
    """
    horizon = int(body.horizon)
    if not (MIN_HORIZON <= horizon <= MAX_HORIZON):
        raise HTTPException(
            status_code=422,
            detail=f"horizon must be between {MIN_HORIZON} and {MAX_HORIZON}",
        )

    product_name = body.product.strip() or "All Products"

    try:
        result = run_forecast(product_name, horizon)
        product_id = resolve_product_id(product_name)
        shap_explanation = get_explanation(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Forecast failed for product=%s horizon=%d", product_name, horizon)
        raise HTTPException(status_code=500, detail="Forecast engine error. Please try again.")

    points = [
        ForecastPoint(
            date=p["date"],
            forecast=p["forecast"],
            lower=p["lower"],
            upper=p["upper"],
            actual=p.get("actual"),
        )
        for p in result["points"]
    ]

    summary = ForecastSummary(
        mean=result["summary"]["mean"],
        min=result["summary"]["min"],
        max=result["summary"]["max"],
        mape=result["summary"]["mape"],
    )

    return ForecastResponse(
        horizon=result["horizon"],
        product=result["product"],
        points=points,
        summary=summary,
        explanation=shap_explanation,
    )
