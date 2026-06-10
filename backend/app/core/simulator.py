"""
What-If Scenario Simulator module.

Iteratively forecasts future sales using the XGBoost surrogate model,
allowing dynamic modification of the `price` feature.
"""
import datetime
from typing import TypedDict
import numpy as np
import pandas as pd

from app.core.data_loader import get_product_df
from app.core.explainer import FEATURE_COLS, _xgb_cache, _train_surrogate

class SimulatedPoint(TypedDict):
    date: str
    baseline: float
    scenario: float

def run_simulation(product_id: str, horizon: int, price_change_pct: float) -> list[SimulatedPoint]:
    """
    Run the XGBoost model iteratively to simulate baseline vs scenario.
    """
    if product_id not in _xgb_cache:
        _train_surrogate(product_id)
        
    model = _xgb_cache[product_id]
    
    # Get recent history for autoregressive feature generation
    df = get_product_df(product_id)
    history = df[["date", "sales", "price"]].tail(max(30, horizon)).copy()
    
    last_date = pd.to_datetime(history.iloc[-1]["date"])
    base_price = history.iloc[-1]["price"]
    scenario_price = base_price * (1 + price_change_pct / 100.0)
    
    # We maintain two separate histories: one for baseline, one for scenario
    baseline_history = list(history["sales"].values)
    scenario_history = list(history["sales"].values)
    
    points = []
    
    for i in range(1, horizon + 1):
        current_date = last_date + pd.Timedelta(days=i)
        
        # Helper to build features
        def build_features(hist, price):
            features = {}
            features["price"] = price
            features["lag_7"] = hist[-7]
            features["lag_14"] = hist[-14]
            features["lag_21"] = hist[-21]
            features["rolling_7_mean"] = np.mean(hist[-7:])
            features["rolling_7_std"] = np.std(hist[-7:]) or 0.0
            features["rolling_30_mean"] = np.mean(hist[-30:])
            features["rolling_30_std"] = np.std(hist[-30:]) or 0.0
            features["day_of_week"] = current_date.dayofweek
            features["month"] = current_date.month
            features["week_of_year"] = current_date.isocalendar()[1]
            features["is_weekend"] = 1 if current_date.dayofweek >= 5 else 0
            features["quarter"] = current_date.quarter
            return np.array([features[c] for c in FEATURE_COLS]).reshape(1, -1)

        X_base = build_features(baseline_history, base_price)
        X_scen = build_features(scenario_history, scenario_price)
        
        # Predict
        y_base = float(model.predict(X_base)[0])
        y_scen = float(model.predict(X_scen)[0])
        
        # Enforce non-negative
        y_base = max(0, y_base)
        y_scen = max(0, y_scen)
        
        # Update histories
        baseline_history.append(y_base)
        scenario_history.append(y_scen)
        
        points.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "baseline": round(y_base, 2),
            "scenario": round(y_scen, 2)
        })
        
    return points
