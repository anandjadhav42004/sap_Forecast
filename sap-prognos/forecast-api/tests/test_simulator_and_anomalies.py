import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
import main

client = TestClient(main.app)

def test_simulator_base_vs_simulated_comparison():
    payload = {
        "store": 2,
        "item": 10,
        "date": "2018-01-01",
        "sales_lag_1": 45.0,
        "sales_lag_7": 40.0,
        "sales_roll_mean_7": 42.5,
        "demand_adjustment_pct": 20.0,
        "is_promotion": True,
        "high_seasonality": False
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # 1. Base case and simulated case structures
    assert "base_case" in data
    assert "simulated_case" in data
    base_demand = data["base_case"]["daily_demand"]
    sim_demand = data["simulated_case"]["daily_demand"]
    
    # 2. Demand increases by (1 + 0.20) * 1.15 = 1.38x
    assert sim_demand > base_demand
    expected_approx = base_demand * 1.20 * 1.15
    assert abs(sim_demand - expected_approx) < 0.1
    
    # 3. Scenario narrative explanation exists
    assert "scenario_explanation" in data
    assert len(data["scenario_explanation"]) > 20

def test_anomaly_detection_z_score():
    # 20 steady baseline points (~50) so std is tight enough (~20)
    # allowing both 180 (spike, Z > +3.0) and 2 (dip, Z < -2.0) to qualify as outliers
    historical_sales = [{"date": f"2017-11-{i:02d}", "sales": 50.0} for i in range(1, 21)]
    # Add outlier spike
    historical_sales.append({"date": "2017-11-21", "sales": 180.0})
    # Add outlier dip
    historical_sales.append({"date": "2017-11-22", "sales": 2.0})
    
    payload = {
        "store": 2,
        "item": 10,
        "historical_sales": historical_sales
    }
    response = client.post("/anomalies", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["anomalies_detected"] >= 2
    anomalies = data["anomalies"]
    
    # Check spike
    spikes = [a for a in anomalies if a["is_spike"]]
    assert len(spikes) >= 1
    assert spikes[0]["anomaly_type"] == "Demand Spike"
    assert spikes[0]["actual_sales"] == 180.0
    assert spikes[0]["z_score"] > 2.0
    
    # Check dip
    dips = [a for a in anomalies if not a["is_spike"]]
    assert len(dips) >= 1
    assert dips[0]["anomaly_type"] == "Demand Drop"
    assert dips[0]["actual_sales"] == 2.0
    assert dips[0]["z_score"] < -2.0
    
    # Methodology & explanation
    assert "methodology" in data
    assert "Two-tailed Z-score" in data["methodology"]
    assert "explanation" in data
