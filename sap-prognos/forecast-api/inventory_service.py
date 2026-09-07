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
    # The condition for reorder: if forecasted_demand (avg_daily_demand) > (current_stock - safety_stock)
    cursor.execute('''
        SELECT * FROM inventory 
        WHERE avg_daily_demand > (current_stock - safety_stock)
        ORDER BY (current_stock - safety_stock - avg_daily_demand) ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
