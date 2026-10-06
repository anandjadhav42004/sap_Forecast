import pytest
from fastapi.testclient import TestClient
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
import main
import inventory_service

client = TestClient(main.app)

def test_single_day_forecast():
    payload = {
        "store": 2,
        "item": 10,
        "date": "2018-01-01",
        "sales_lag_1": 45.0,
        "sales_lag_7": 40.0,
        "sales_roll_mean_7": 42.5,
        "horizon_days": 1
    }
    response = client.post("/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["store"] == 2
    assert data["item"] == 10
    assert data["forecast_date"] == "2018-01-01"
    assert data["predicted_demand"] > 0
    assert data["lower_bound"] <= data["predicted_demand"] <= data["upper_bound"]
    assert data["confidence_level"] == 0.85
    assert len(data["explainability"]) > 0
    assert "explainability_disclaimer" in data

def test_recursive_multi_day_horizon():
    horizon = 7
    payload = {
        "store": 2,
        "item": 10,
        "date": "2018-01-01",
        "sales_lag_1": 45.0,
        "sales_lag_7": 40.0,
        "sales_roll_mean_7": 42.5,
        "horizon_days": horizon
    }
    response = client.post("/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["horizon_days"] == horizon
    assert len(data["horizon_forecast"]) == horizon
    assert data["total_horizon_demand"] > 0
    assert data["avg_daily_demand"] > 0
    
    # Verify chronological sequence
    dates = [p["date"] for p in data["horizon_forecast"]]
    expected_dates = ["2018-01-01", "2018-01-02", "2018-01-03", "2018-01-04", "2018-01-05", "2018-01-06", "2018-01-07"]
    assert dates == expected_dates

def test_data_leakage_checks():
    """Verify that lag features are strictly backward-looking and exclude target day."""
    feat = inventory_service.get_latest_features(2, 10)
    history = feat["history"]
    assert len(history) >= 7
    
    # 1. Next forecast date must be strictly after the latest historical actual date
    latest_hist_date = datetime.strptime(history[-1]["date"], "%Y-%m-%d")
    forecast_date = datetime.strptime(feat["next_date"], "%Y-%m-%d")
    assert forecast_date > latest_hist_date
    
    # 2. sales_lag_1 must equal the sales of the day immediately prior
    assert feat["sales_lag_1"] == history[-1]["sales"]
    
    # 3. sales_roll_mean_7 must equal average of past 7 days excluding forecast day
    last_7 = [h["sales"] for h in history[-7:]]
    expected_roll = round(sum(last_7) / 7.0, 2)
    assert abs(feat["sales_roll_mean_7"] - expected_roll) < 0.05
