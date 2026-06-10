"""Pydantic schemas for Forecast endpoint."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ForecastRequest(BaseModel):
    horizon: int = 30
    product: str = "All Products"


class ForecastPoint(BaseModel):
    date: str
    forecast: float
    lower: float
    upper: float
    actual: Optional[float] = None


class ForecastSummary(BaseModel):
    mean: float
    min: float
    max: float
    mape: float


class ForecastResponse(BaseModel):
    horizon: int
    product: str
    points: list[ForecastPoint]
    summary: ForecastSummary
    explanation: str = ""
