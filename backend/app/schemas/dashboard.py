"""Pydantic schemas for Dashboard endpoint."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class SeriesPoint(BaseModel):
    date: str
    actual: Optional[float] = None
    predicted: Optional[float] = None


class CategoryPerf(BaseModel):
    category: str
    sales: float
    target: float


class DashboardResponse(BaseModel):
    totalSales: float
    predictedSales: float
    growth: float
    alerts: int
    series: list[SeriesPoint]
    categories: list[CategoryPerf]
