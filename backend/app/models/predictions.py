"""ORM model for stored ML predictions."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func

from app.database import Base


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    product_id = Column(String(64), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False)
    forecast_value = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    model_name = Column(String(64), nullable=False, default="ARIMA")
    mape = Column(Float, nullable=True)
