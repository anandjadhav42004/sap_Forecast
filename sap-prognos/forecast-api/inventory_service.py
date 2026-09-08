import sqlite3
import os

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_inventory(store: int, item: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE store = ? AND item = ?', (store, item))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_reorder_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all inventory to categorize
    cursor.execute('SELECT * FROM inventory')
    rows = cursor.fetchall()
    conn.close()
    
    alerts = []
    for row in rows:
        inv = dict(row)
        current_stock = inv['current_stock']
        avg_demand = inv['avg_daily_demand']
        lead_time = inv['lead_time_days']
        reorder_point = inv['reorder_point']
        target_stock = inv['target_stock']
        safety_stock = inv['safety_stock']
        incoming = inv['incoming_stock']
        
        # Calculate risk levels
        projected_demand_during_lt = avg_demand * lead_time
        available_stock = current_stock + incoming
        
        days_of_cover = round(available_stock / avg_demand, 1) if avg_demand > 0 else 999
        
        if available_stock <= projected_demand_during_lt:
            risk = "CRITICAL" # Stockout likely within lead time
            risk_score = 4
        elif available_stock <= reorder_point:
            risk = "HIGH" # Below reorder point
            risk_score = 3
        elif available_stock <= (reorder_point * 1.2):
            risk = "MEDIUM" # Approaching reorder point
            risk_score = 2
        else:
            continue # NORMAL - we don't alert
            
        recommended_order = max(0, target_stock - available_stock)
            
        inv['risk'] = risk
        inv['risk_score'] = risk_score
        inv['days_of_cover'] = days_of_cover
        inv['recommended_order'] = recommended_order
        alerts.append(inv)
        
    # Sort critical first, then by days of cover (lowest first)
    alerts.sort(key=lambda x: (-x['risk_score'], x['days_of_cover']))
    
    return alerts
