import sqlite3
import os
import random
from datetime import datetime, timedelta

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_inventory_metrics(inv: dict) -> dict:
    """Calculates supply chain indicators (LTD, Available Stock, Days of Cover, Risk, Reason)."""
    current_stock = inv['current_stock']
    avg_demand = inv['avg_daily_demand']
    lead_time = inv['lead_time_days']
    reorder_point = inv['reorder_point']
    target_stock = inv['target_stock']
    incoming = inv['incoming_stock']
    
    projected_demand_during_lt = avg_demand * lead_time
    available_stock = current_stock + incoming
    days_of_cover = round(available_stock / avg_demand, 1) if avg_demand > 0 else 999
    
    if available_stock <= projected_demand_during_lt:
        risk = "CRITICAL"
        risk_score = 4
        risk_reason = (
            f"CRITICAL: Available stock ({available_stock}) is less than or equal to lead-time demand "
            f"({int(projected_demand_during_lt)}). Imminent stockout within {lead_time} days!"
        )
    elif available_stock <= reorder_point:
        risk = "HIGH"
        risk_score = 3
        risk_reason = (
            f"HIGH: Available stock ({available_stock}) has breached Reorder Point ({reorder_point}). "
            f"Safety stock buffer ({inv['safety_stock']} units) is currently being consumed."
        )
    elif available_stock <= (reorder_point * 1.2):
        risk = "MEDIUM"
        risk_score = 2
        risk_reason = (
            f"MEDIUM: Available stock ({available_stock}) is within 20% of Reorder Point ({reorder_point}). "
            f"Monitor replenishment pipeline."
        )
    else:
        risk = "LOW"
        risk_score = 1
        risk_reason = f"NORMAL / LOW: Stock levels are healthy with {days_of_cover} days of cover."
        
    recommended_order = max(0, target_stock - available_stock)
    
    inv_enriched = dict(inv)
    inv_enriched['available_stock'] = available_stock
    inv_enriched['lead_time_demand'] = projected_demand_during_lt
    inv_enriched['days_of_cover'] = days_of_cover
    inv_enriched['risk'] = risk
    inv_enriched['risk_score'] = risk_score
    inv_enriched['risk_reason'] = risk_reason
    inv_enriched['recommended_order'] = recommended_order
    return inv_enriched

def get_inventory(store: int, item: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE store = ? AND item = ?', (store, item))
    row = cursor.fetchone()
    conn.close()
    if row:
        return calculate_inventory_metrics(dict(row))
    return None

def get_all_reorder_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    rows = cursor.fetchall()
    conn.close()
    
    alerts = []
    for row in rows:
        inv = calculate_inventory_metrics(dict(row))
        # Include all items that have risk CRITICAL, HIGH, or MEDIUM
        if inv['risk'] in ['CRITICAL', 'HIGH', 'MEDIUM']:
            alerts.append(inv)
        
    # Sort critical first, then lowest days of cover
    alerts.sort(key=lambda x: (-x['risk_score'], x['days_of_cover']))
    return alerts

def get_full_inventory():
    """Returns all 500 store-item records with calculated supply chain metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory ORDER BY store, item')
    rows = cursor.fetchall()
    conn.close()
    
    results = [calculate_inventory_metrics(dict(r)) for r in rows]
    # Sort with critical risk items first
    results.sort(key=lambda x: (-x['risk_score'], x['days_of_cover']))
    return results

def create_purchase_order(store: int, item: int, quantity: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM inventory WHERE store = ? AND item = ?', (store, item))
    inv_row = cursor.fetchone()
    if not inv_row:
        conn.close()
        return None
        
    inv = dict(inv_row)
    current_stock = inv['current_stock']
    target_stock = inv['target_stock']
    incoming = inv['incoming_stock']
    lead_time = inv['lead_time_days']
    available_stock = current_stock + incoming
    
    if not quantity or quantity <= 0:
        quantity = max(50, target_stock - available_stock)
        
    order_id = f"PO-{random.randint(10000, 99999)}"
    now = datetime.now()
    created_at = now.isoformat()
    expected_delivery = (now + timedelta(days=lead_time)).strftime('%Y-%m-%d')
    
    cursor.execute('''
    INSERT INTO orders (order_id, store, item, quantity, status, created_at, expected_delivery_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, store, item, quantity, 'CONFIRMED', created_at, expected_delivery))
    
    new_incoming = incoming + quantity
    cursor.execute('''
    UPDATE inventory 
    SET incoming_stock = ?, last_updated = ?
    WHERE store = ? AND item = ?
    ''', (new_incoming, created_at, store, item))
    
    conn.commit()
    
    cursor.execute('SELECT * FROM inventory WHERE store = ? AND item = ?', (store, item))
    updated_inv = calculate_inventory_metrics(dict(cursor.fetchone()))
    conn.close()
    
    return {
        "order_id": order_id,
        "store": store,
        "item": item,
        "quantity": quantity,
        "status": "CONFIRMED",
        "created_at": created_at,
        "expected_delivery_date": expected_delivery,
        "updated_inventory": updated_inv
    }

def get_orders(store: int = None, item: int = None, limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    if store is not None and item is not None:
        cursor.execute('SELECT * FROM orders WHERE store = ? AND item = ? ORDER BY created_at DESC LIMIT ?', (store, item, limit))
    elif store is not None:
        cursor.execute('SELECT * FROM orders WHERE store = ? ORDER BY created_at DESC LIMIT ?', (store, limit))
    else:
        cursor.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_sales_history(store: int, item: int, limit: int = 14):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT date, sales, sales_lag_1, sales_lag_7, sales_roll_mean_7
    FROM sales_history
    WHERE store = ? AND item = ?
    ORDER BY date DESC
    LIMIT ?
    ''', (store, item, limit))
    rows = cursor.fetchall()
    conn.close()
    
    result = [dict(r) for r in reversed(rows)]
    return result

def get_latest_features(store: int, item: int):
    history = get_sales_history(store, item, limit=14)
    if not history:
        return {
            "store": store,
            "item": item,
            "next_date": "2018-01-01",
            "sales_lag_1": 45.0,
            "sales_lag_7": 42.0,
            "sales_roll_mean_7": 44.5,
            "history": []
        }
        
    last_record = history[-1]
    last_date = datetime.strptime(last_record['date'], '%Y-%m-%d')
    next_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    sales_lag_1 = last_record['sales']
    sales_lag_7 = history[-7]['sales'] if len(history) >= 7 else history[0]['sales']
    
    last_7_sales = [h['sales'] for h in history[-7:]]
    sales_roll_mean_7 = round(sum(last_7_sales) / len(last_7_sales), 2)
    
    return {
        "store": store,
        "item": item,
        "next_date": next_date,
        "sales_lag_1": round(sales_lag_1, 1),
        "sales_lag_7": round(sales_lag_7, 1),
        "sales_roll_mean_7": sales_roll_mean_7,
        "history": history
    }
