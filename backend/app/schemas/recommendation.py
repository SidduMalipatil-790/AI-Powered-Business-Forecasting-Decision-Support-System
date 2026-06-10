"""Pydantic schemas for Recommendations endpoint."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel


class RecommendationSchema(BaseModel):
    id: str
    type: Literal["inventory", "pricing", "risk"]
    title: str
    confidence: float        # 0–100
    explanation: str
    impact: str
    priority: str = "medium"
