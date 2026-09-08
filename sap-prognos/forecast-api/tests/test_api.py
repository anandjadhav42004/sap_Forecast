from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "model_loaded" in data
    assert "database_connected" in data

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "SAP Prognos API" in response.json()["name"]

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "XGBoost (Full Global)" in data["metrics"]

def test_reorder_alerts():
    response = client.get("/reorder-alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "alerts" in data
    if len(data["alerts"]) > 0:
        assert "risk" in data["alerts"][0]
        assert "store" in data["alerts"][0]

def test_forecast_endpoint():
    payload = {
        "store": 1,
        "item": 1,
        "date": "2023-01-01",
        "sales_lag_1": 10.0,
        "sales_lag_7": 15.0,
        "sales_roll_mean_7": 12.0
    }
    response = client.post("/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_demand" in data
    assert "explainability" in data
    
def test_simulate_endpoint():
    payload = {
        "store": 1,
        "item": 1,
        "date": "2023-01-01",
        "sales_lag_1": 10.0,
        "sales_lag_7": 15.0,
        "sales_roll_mean_7": 12.0,
        "demand_adjustment_pct": 10.0,
        "is_promotion": True,
        "high_seasonality": False
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "adjusted_forecast" in data
    assert "base_forecast" in data
    assert data["adjusted_forecast"] > data["base_forecast"]
