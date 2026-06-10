"""GET /api/dashboard — KPIs and summary stats."""
from __future__ import annotations

import logging
from datetime import timedelta

import numpy as np
import pandas as pd
from fastapi import APIRouter

from app.core.data_loader import get_product_df, PRODUCT_MAP
from app.core.anomaly_detector import detect_all_anomalies
from app.core.forecaster import forecast
from app.schemas.dashboard import DashboardResponse, SeriesPoint, CategoryPerf

router = APIRouter()
logger = logging.getLogger(__name__)

# Category sales target ratios (vs actual last-30d)
TARGET_RATIOS = {
    "Electronics": 0.92,
    "Apparel": 1.05,
    "Food & Drink": 0.97,
    "Sports": 1.08,
    "All": 1.0,
}

CATEGORY_LABELS = {
    "P001": "Electronics",
    "P002": "Electronics",
    "P003": "Food & Drink",
    "P004": "Apparel",
    "P005": "Sports",
}


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    """Return KPIs and time-series data for the dashboard."""
    # ── Aggregate historical sales (ALL products)
    all_df = get_product_df("ALL")
    last_30 = all_df.tail(30).copy()

    total_sales = float(last_30["sales"].sum())

    # ── 7-day forecast for "predicted sales" KPI
    fc_result = forecast("All Products", horizon=7)
    predicted_sales = fc_result["summary"]["mean"] * 7

    # ── Growth: compare last 30 days vs prior 30 days
    prev_30 = all_df.iloc[-60:-30]["sales"].sum() if len(all_df) >= 60 else all_df.iloc[:-30]["sales"].sum()
    growth = round(((total_sales - float(prev_30)) / (abs(float(prev_30)) + 1e-8)) * 100, 1)

    # ── Active alerts (high-severity anomalies in last 7 days)
    anomalies = detect_all_anomalies(lookback_days=7)
    alerts = sum(1 for a in anomalies if a["severity"] == "high")

    # ── Time series: last 37 days actual + 7 days predicted (matches frontend split)
    series_df = all_df.tail(37).copy()
    series: list[SeriesPoint] = [
        SeriesPoint(
            date=row["date"].strftime("%Y-%m-%d"),
            actual=round(float(row["sales"]), 2),
            predicted=None,
        )
        for _, row in series_df.iterrows()
    ]
    # Append predicted points
    for pt in fc_result["points"]:
        series.append(SeriesPoint(date=pt["date"], actual=None, predicted=round(pt["forecast"], 2)))

    # ── Category performance
    categories: list[CategoryPerf] = _build_category_perf()

    return DashboardResponse(
        totalSales=round(total_sales, 2),
        predictedSales=round(predicted_sales, 2),
        growth=growth,
        alerts=alerts,
        series=series,
        categories=categories,
    )


def _build_category_perf() -> list[CategoryPerf]:
    """Compute last-30d sales by category with synthetic targets."""
    cat_sales: dict[str, float] = {}

    for pid, label in CATEGORY_LABELS.items():
        try:
            df = get_product_df(pid)
            sales_30 = float(df.tail(30)["sales"].sum())
            cat_sales[label] = cat_sales.get(label, 0.0) + sales_30
        except Exception:
            pass

    result = []
    for cat, sales in cat_sales.items():
        ratio = TARGET_RATIOS.get(cat, 1.0)
        target = round(sales * ratio, 2)
        result.append(CategoryPerf(category=cat, sales=round(sales, 2), target=target))

    # Sort by sales desc
    result.sort(key=lambda x: x.sales, reverse=True)
    return result
