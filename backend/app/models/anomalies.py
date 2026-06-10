"""ORM model for detected anomaly events."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func

from app.database import Base


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    anomaly_date = Column(Date, nullable=False, index=True)
    product_id = Column(String(64), nullable=False)
    metric = Column(String(128), nullable=False)
    anomaly_score = Column(Float, nullable=False)   # Isolation Forest raw score
    severity = Column(String(16), nullable=False)   # low / medium / high
    delta_pct = Column(Float, nullable=False)        # % deviation from baseline
    description = Column(String(512), nullable=False)
