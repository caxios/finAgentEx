import sqlite3
import json
import os

DB_PATH = os.path.join("backend", "cache.db")

def inspect_cache():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Checking TSLA Annual data in cache...")
    cursor.execute("""
        SELECT period, statement_type, data_json 
        FROM fundamentals_cache 
        WHERE ticker = 'TSLA' AND period_type = 'annual'
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        print("No TSLA data found in cache.")
    else:
        print(f"Found period: {row['period']}")
        data = json.loads(row['data_json'])
        print(f"Data keys (Labels): {list(data.keys())[:5]}")
        
        # Check if concept is stored inside the value objects
        sample_values = list(data.values())[:3]
        for idx, val in enumerate(sample_values):
             print(f"Item {idx} concept: {val.get('concept')}")

    conn.close()

if __name__ == "__main__":
    inspect_cache()
