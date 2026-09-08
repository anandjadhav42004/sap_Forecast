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
        lead_time_days INTEGER,
        reorder_point INTEGER,
        target_stock INTEGER,
        incoming_stock INTEGER,
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
            lead_time_days = random.randint(1, 5) # 1 to 5 days lead time
            
            # Safety stock is typically (Max Demand * Max Lead Time) - (Avg Demand * Avg Lead Time)
            # We'll use a simpler heuristic for the prototype: pad average lead time demand by 50%
            safety_stock = int(avg_daily_demand * lead_time_days * 0.5)
            
            # Reorder Point = Demand during lead time + Safety Stock
            reorder_point = int((avg_daily_demand * lead_time_days) + safety_stock)
            
            # Target Stock = Reorder Point + Reorder Quantity (let's assume roughly 14 days of supply)
            target_stock = int(reorder_point + (avg_daily_demand * 14))
            
            # Most items have plenty of stock, but ~10-15% will fall below threshold
            if random.random() < 0.15:
                # Force low/critical stock (below reorder point)
                current_stock = random.randint(0, reorder_point - 1)
                incoming_stock = 0 if random.random() < 0.5 else random.randint(10, 50)
            else:
                # Healthy stock
                current_stock = random.randint(reorder_point + 1, target_stock)
                incoming_stock = 0
                
            last_updated = datetime.now()
            
            rows.append((store, item, current_stock, safety_stock, avg_daily_demand, lead_time_days, reorder_point, target_stock, incoming_stock, last_updated))
            
    cursor.executemany('''
    INSERT INTO inventory (store, item, current_stock, safety_stock, avg_daily_demand, lead_time_days, reorder_point, target_stock, incoming_stock, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', rows)
    
    conn.commit()
    conn.close()
    
    print(f"Successfully seeded {len(rows)} rows into {db_path}")

if __name__ == '__main__':
    setup_database()
