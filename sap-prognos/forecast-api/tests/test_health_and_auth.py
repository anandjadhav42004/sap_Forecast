import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
import main

client = TestClient(main.app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["database_connected"] is True
    assert data["version"] == "1.0.0"

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "XGBoost (Full Global)" in data["metrics"]
    assert "Prophet (Sampled)" in data["metrics"]
    assert "Baseline (7-Day MA)" in data["metrics"]
    # Verify reported benchmark accuracy
    xgboost_mape = data["metrics"]["XGBoost (Full Global)"]["MAPE"]
    assert 12.0 < xgboost_mape < 14.0

def test_login_admin():
    response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert "token" in data

def test_login_viewer():
    response = client.post("/auth/login", json={"username": "user", "password": "user"})
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert "token" in data

def test_login_invalid():
    response = client.post("/auth/login", json={"username": "baduser", "password": "wrongpassword"})
    assert response.status_code == 401

def test_rbac_admin_guard():
    # Viewer attempt (no header or viewer header) should be rejected
    res_viewer = client.post(
        "/purchase-order",
        json={"store": 2, "item": 10, "quantity": 25},
        headers={"X-User-Role": "user"}
    )
    assert res_viewer.status_code == 403
    assert "Administrator privileges required" in res_viewer.json()["detail"]

    # Admin attempt should succeed
    res_admin = client.post(
        "/purchase-order",
        json={"store": 2, "item": 10, "quantity": 25},
        headers={"X-User-Role": "admin"}
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["message"] == "Purchase order successfully placed"
