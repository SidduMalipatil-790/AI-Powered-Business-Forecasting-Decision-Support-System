"""Pydantic schemas for Anomaly endpoint."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel


class AnomalySchema(BaseModel):
    id: str
    date: str
    metric: str
    severity: Literal["low", "medium", "high"]
    delta: float          # % deviation (positive = spike, negative = drop)
    description: str
    anomaly_score: float  # raw Isolation Forest score
