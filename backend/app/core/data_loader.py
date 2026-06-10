"""
Data Loader — reads CSV, handles missing values, and engineers features.

Feature set produced per product:
  - lag_7, lag_14, lag_21       : sales n days ago
  - rolling_7_mean, rolling_7_std
  - rolling_30_mean, rolling_30_std
  - day_of_week (0=Mon … 6=Sun)
  - month (1-12)
  - week_of_year (1-53)
  - is_weekend (0/1)
  - quarter (1-4)
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from app.config import DATA_CSV_PATH

logger = logging.getLogger(__name__)

# Canonical product name → short ID mapping
PRODUCT_MAP: dict[str, str] = {
    "All Products":       "ALL",
    "Wireless Earbuds Pro": "P001",
    "Smart Watch X":      "P002",
    "Coffee Beans 1kg":   "P003",
    "Winter Coat":        "P004",
    "Yoga Mat":           "P005",
}

# Reverse map
ID_TO_NAME: dict[str, str] = {v: k for k, v in PRODUCT_MAP.items()}

# Category groups for category performance chart
CATEGORY_MAP: dict[str, str] = {
    "P001": "Electronics",
    "P002": "Electronics",
    "P003": "Food & Drink",
    "P004": "Apparel",
    "P005": "Sports",
    "ALL":  "All",
}

# Singleton cache
_df_cache: dict[str, pd.DataFrame] = {}


def load_raw(csv_path: str = DATA_CSV_PATH) -> pd.DataFrame:
    """Load the raw CSV and parse dates."""
    if "raw" in _df_cache:
        return _df_cache["raw"]

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Basic type coercion
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0).astype(int)
    df["inventory_level"] = pd.to_numeric(df["inventory_level"], errors="coerce").fillna(0).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Forward-fill then back-fill any remaining NaN in numeric cols
    numeric_cols = ["sales", "price"]
    df[numeric_cols] = df[numeric_cols].ffill().bfill()

    _df_cache["raw"] = df
    logger.info("Loaded %d rows from %s", len(df), csv_path)
    return df


def get_product_df(product_id: str) -> pd.DataFrame:
    """Return feature-engineered DataFrame for a single product (or ALL)."""
    cache_key = f"feat_{product_id}"
    if cache_key in _df_cache:
        return _df_cache[cache_key]

    raw = load_raw()

    if product_id == "ALL":
        # Aggregate across all products per day
        df = (
            raw.groupby("date")
            .agg({"sales": "sum", "units_sold": "sum", "inventory_level": "sum", "price": "mean"})
            .reset_index()
        )
        df["product_id"] = "ALL"
        df["product_name"] = "All Products"
        df["category"] = "All"
    else:
        df = raw[raw["product_id"] == product_id].copy()
        if df.empty:
            raise ValueError(f"No data found for product_id={product_id}")

    df = df.sort_values("date").reset_index(drop=True)
    df = _engineer_features(df)

    _df_cache[cache_key] = df
    return df


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time and lag features in-place."""
    df = df.copy()
    s = df["sales"]

    # Lag features
    df["lag_7"] = s.shift(7)
    df["lag_14"] = s.shift(14)
    df["lag_21"] = s.shift(21)

    # Rolling statistics
    df["rolling_7_mean"] = s.shift(1).rolling(7).mean()
    df["rolling_7_std"] = s.shift(1).rolling(7).std()
    df["rolling_30_mean"] = s.shift(1).rolling(30).mean()
    df["rolling_30_std"] = s.shift(1).rolling(30).std()

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["quarter"] = df["date"].dt.quarter

    # Fill NaN introduced by rolling (median fill)
    lag_cols = ["lag_7", "lag_14", "lag_21", "rolling_7_mean", "rolling_7_std",
                "rolling_30_mean", "rolling_30_std"]
    for col in lag_cols:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val if not np.isnan(median_val) else 0)

    return df


def resolve_product_id(product_name: str) -> str:
    """Map frontend display name → internal product_id."""
    return PRODUCT_MAP.get(product_name, "ALL")


def invalidate_cache() -> None:
    """Clear the in-memory DataFrame cache (e.g., after DB seed)."""
    _df_cache.clear()
