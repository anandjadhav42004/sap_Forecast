import sqlite3
import random
import os
from datetime import datetime, timedelta
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.db')
DATA_PREP_CSV = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data-prep', 'split_test.csv'))

def init_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        store INTEGER,
        item INTEGER,
        current_stock INTEGER,
        safety_stock INTEGER,
        avg_daily_demand INTEGER,
        lead_time_days INTEGER,
        reorder_point INTEGER,
        target_stock INTEGER,
        incoming_stock INTEGER,
        last_updated TIMESTAMP,
        PRIMARY KEY (store, item)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        store INTEGER,
        item INTEGER,
        quantity INTEGER,
        status TEXT,
        created_at TIMESTAMP,
        expected_delivery_date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales_history (
        store INTEGER,
        item INTEGER,
        date TEXT,
        sales REAL,
        sales_lag_1 REAL,
        sales_lag_7 REAL,
        sales_roll_mean_7 REAL,
        PRIMARY KEY (store, item, date)
    )
    ''')
    conn.commit()

def seed_sales_history(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM sales_history")
    count = cursor.fetchone()[0]
    if count > 0:
        return count
        
    print("Populating sales_history table...")
    if os.path.exists(DATA_PREP_CSV):
        try:
            df = pd.read_csv(DATA_PREP_CSV)
            # Filter to the last 30 days of dataset (December 2017)
            recent_df = df[df['date'] >= '2017-12-01'][
                ['store', 'item', 'date', 'sales', 'sales_lag_1', 'sales_lag_7', 'sales_roll_mean_7']
            ]
            recent_df.to_sql('sales_history', conn, if_exists='replace', index=False)
            # Recreate primary key index
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_store_item_date ON sales_history (store, item, date)")
            conn.commit()
            print(f"Loaded {len(recent_df)} historical records from {DATA_PREP_CSV}")
            return len(recent_df)
        except Exception as e:
            print(f"Could not load split_test.csv: {e}. Generating fallback data.")
            
    # Fallback generation for 10 stores x 50 items x 14 days
    rows = []
    base_date = datetime(2017, 12, 18)
    for store in range(1, 11):
        for item in range(1, 51):
            base_sales = random.randint(20, 80)
            for d in range(14):
                cur_date = (base_date + timedelta(days=d)).strftime('%Y-%m-%d')
                is_weekend = (base_date + timedelta(days=d)).weekday() >= 5
                factor = 1.3 if is_weekend else 1.0
                sales = round(base_sales * factor + random.uniform(-5, 5), 1)
                rows.append((store, item, cur_date, sales, sales, sales, sales))
                
    cursor.executemany('''
    INSERT OR REPLACE INTO sales_history (store, item, date, sales, sales_lag_1, sales_lag_7, sales_roll_mean_7)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', rows)
    conn.commit()
    return len(rows)

def ensure_db_initialized():
    """Self-healing startup check to ensure all required tables and seeds exist."""
    conn = sqlite3.connect(DB_PATH)
    init_tables(conn)
    
    # Check inventory rows
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM inventory")
    inv_count = cursor.fetchone()[0]
    if inv_count == 0:
        seed_inventory(conn)
        
    seed_sales_history(conn)
    conn.close()

def seed_inventory(conn):
    print("Seeding inventory database (10 stores x 50 items = 500 rows)...")
    rows = []
    for store in range(1, 11):
        for item in range(1, 51):
            avg_daily_demand = random.randint(15, 90)
            lead_time_days = random.randint(1, 5)
            safety_stock = int(avg_daily_demand * lead_time_days * 0.5)
            reorder_point = int((avg_daily_demand * lead_time_days) + safety_stock)
            target_stock = int(reorder_point + (avg_daily_demand * 14))
            
            if random.random() < 0.15:
                current_stock = random.randint(0, reorder_point - 1)
                incoming_stock = 0 if random.random() < 0.5 else random.randint(10, 50)
            else:
                current_stock = random.randint(reorder_point + 1, target_stock)
                incoming_stock = 0
                
            last_updated = datetime.now().isoformat()
            rows.append((store, item, current_stock, safety_stock, avg_daily_demand, lead_time_days, reorder_point, target_stock, incoming_stock, last_updated))
            
    cursor = conn.cursor()
    cursor.executemany('''
    INSERT INTO inventory (store, item, current_stock, safety_stock, avg_daily_demand, lead_time_days, reorder_point, target_stock, incoming_stock, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', rows)
    conn.commit()

def setup_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    init_tables(conn)
    seed_inventory(conn)
    seed_sales_history(conn)
    conn.close()
    print(f"Database setup complete at {DB_PATH}")

if __name__ == '__main__':
    setup_database()
