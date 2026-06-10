"""
DB Seeder — seeds the SQLite database from the CSV file.
Run once at startup if the DB is empty.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from app.config import DATA_CSV_PATH
from app.database import SessionLocal
from app.models.sales import SalesRecord

logger = logging.getLogger(__name__)


def seed_database() -> None:
    """Seed sales_records from CSV if table is empty."""
    db = SessionLocal()
    try:
        existing = db.query(SalesRecord).count()
        if existing > 0:
            logger.info("Database already has %d sales records — skipping seed.", existing)
            return

        csv_path = Path(DATA_CSV_PATH)
        if not csv_path.exists():
            logger.warning("CSV not found at %s — skipping seed.", DATA_CSV_PATH)
            return

        df = pd.read_csv(csv_path, parse_dates=["date"])
        records = []
        for _, row in df.iterrows():
            records.append(
                SalesRecord(
                    date=row["date"].date(),
                    product_id=str(row["product_id"]),
                    product_name=str(row["product_name"]),
                    category=str(row["category"]),
                    sales=float(row["sales"]),
                    units_sold=int(row["units_sold"]),
                    inventory_level=int(row["inventory_level"]),
                    price=float(row["price"]),
                )
            )

        db.bulk_save_objects(records)
        db.commit()
        logger.info("Seeded %d sales records into the database.", len(records))
    except Exception as exc:
        db.rollback()
        logger.error("Database seed failed: %s", exc)
    finally:
        db.close()
