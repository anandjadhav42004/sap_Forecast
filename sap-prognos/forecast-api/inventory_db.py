import sqlite3
import random
import os
from datetime import datetime

def setup_database():
    db_path = os.path.join(os.path.dirname(__file__), 'inventory.db')
    
    # Remove existing DB if we want a fresh seed
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        store INTEGER,
        item INTEGER,
        current_stock INTEGER,
        safety_stock INTEGER,
        avg_daily_demand INTEGER,
        last_updated TIMESTAMP,
        PRIMARY KEY (store, item)
    )
    ''')
    
    print("Seeding inventory database (10 stores x 50 items = 500 rows)...")
    
    rows = []
    # 10 stores, 50 items
    for store in range(1, 11):
        for item in range(1, 51):
            # Realistic randoms
            avg_daily_demand = random.randint(15, 90)
            # Safety stock is roughly 1.5x daily demand (e.g. lead time padding)
            safety_stock = int(avg_daily_demand * 1.5)
            
            # Most items have plenty of stock, but ~10-15% will fall below threshold
            # Threshold for alert is: avg_daily_demand > (current_stock - safety_stock)
            # which means current_stock < avg_daily_demand + safety_stock
            
            if random.random() < 0.15:
                # Force low stock
                current_stock = random.randint(0, safety_stock + avg_daily_demand - 1)
            else:
                # Healthy stock
                current_stock = random.randint(safety_stock + avg_daily_demand, avg_daily_demand * 10)
                
            last_updated = datetime.now()
            
            rows.append((store, item, current_stock, safety_stock, avg_daily_demand, last_updated))
            
    cursor.executemany('''
    INSERT INTO inventory (store, item, current_stock, safety_stock, avg_daily_demand, last_updated)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', rows)
    
    conn.commit()
    conn.close()
    
    print(f"Successfully seeded {len(rows)} rows into {db_path}")

if __name__ == '__main__':
    setup_database()
