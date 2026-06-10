"""ORM model for historical sales records."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, Date, Index

from app.database import Base


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    product_id = Column(String(64), nullable=False, index=True)
    product_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    sales = Column(Float, nullable=False)          # revenue in $
    units_sold = Column(Integer, nullable=False)
    inventory_level = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_sales_date_product", "date", "product_id"),
    )
