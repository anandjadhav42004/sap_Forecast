import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
import main
import inventory_service

client = TestClient(main.app)

def test_inventory_math_and_risk_levels():
    """Verify mathematical definitions of LTD, Available Stock, ROP, Risk."""
    # Test case 1: Stockout condition (available <= LTD) -> CRITICAL
    dummy_inv_critical = {
        "store": 99,
        "item": 99,
        "current_stock": 20,
        "incoming_stock": 10,
        "avg_daily_demand": 30,
        "lead_time_days": 3,
        "safety_stock": 45,
        "reorder_point": 135,
        "target_stock": 500
    }
    # Available = 30, LTD = 30 * 3 = 90 -> available (30) <= LTD (90) -> CRITICAL
    result = inventory_service.calculate_inventory_metrics(dummy_inv_critical)
    assert result["available_stock"] == 30
    assert result["lead_time_demand"] == 90
    assert result["risk"] == "CRITICAL"
    assert result["risk_score"] == 4
    assert "CRITICAL" in result["risk_reason"]
    assert result["recommended_order"] == 470 # target (500) - available (30)

    # Test case 2: Below Reorder Point (LTD < available <= ROP) -> HIGH
    dummy_inv_high = {
        "store": 99,
        "item": 99,
        "current_stock": 100,
        "incoming_stock": 0,
        "avg_daily_demand": 30,
        "lead_time_days": 3,
        "safety_stock": 45,
        "reorder_point": 135,
        "target_stock": 500
    }
    # Available = 100 > LTD (90), but <= ROP (135) -> HIGH
    result_high = inventory_service.calculate_inventory_metrics(dummy_inv_high)
    assert result_high["risk"] == "HIGH"
    assert result_high["risk_score"] == 3

    # Test case 3: Healthy stock (available > ROP * 1.2) -> LOW
    dummy_inv_low = {
        "store": 99,
        "item": 99,
        "current_stock": 350,
        "incoming_stock": 50,
        "avg_daily_demand": 20,
        "lead_time_days": 2,
        "safety_stock": 20,
        "reorder_point": 60,
        "target_stock": 400
    }
    # Available = 400 > ROP * 1.2 (72) -> LOW
    result_low = inventory_service.calculate_inventory_metrics(dummy_inv_low)
    assert result_low["risk"] == "LOW"
    assert result_low["risk_score"] == 1

def test_purchase_order_persistence_and_stock_increment():
    """Verify placing a PO creates an order record and increments incoming_stock."""
    initial_inv = inventory_service.get_inventory(1, 1)
    initial_incoming = initial_inv["incoming_stock"]
    
    order_qty = 85
    po_res = client.post(
        "/purchase-order",
        json={"store": 1, "item": 1, "quantity": order_qty},
        headers={"X-User-Role": "admin"}
    )
    assert po_res.status_code == 200
    po_data = po_res.json()["order"]
    
    # 1. PO ID format
    assert po_data["order_id"].startswith("PO-")
    assert po_data["quantity"] == order_qty
    
    # 2. Incoming stock incremented in DB
    updated_inv = inventory_service.get_inventory(1, 1)
    assert updated_inv["incoming_stock"] == initial_incoming + order_qty
    
    # 3. Order is discoverable via /orders
    orders_res = client.get("/orders?store=1&item=1")
    orders = orders_res.json()["orders"]
    matching = [o for o in orders if o["order_id"] == po_data["order_id"]]
    assert len(matching) == 1

def test_all_inventory_catalog_count():
    """Verify that full inventory endpoint returns 500 store-item combinations."""
    response = client.get("/inventory")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 500
    assert len(data["inventory"]) == 500
