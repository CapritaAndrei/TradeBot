import sqlite3
import os
import time

# Verifică dacă fișierul bazei de date există
db_path = 'skinport_bot.db'
if os.path.exists(db_path):
    print(f"Fișierul bazei de date există: {os.path.abspath(db_path)}")
    # Obține dimensiunea
    size = os.path.getsize(db_path)
    print(f"Dimensiune: {size} bytes")
else:
    print(f"Fișierul bazei de date NU există!")

# Încercăm o inserare directă pentru test
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificăm dacă tabelele există
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"\nTabele existente: {len(tables)}")
for table in tables:
    print(f"- {table[0]}")
    # Verifică dacă tabelul are date
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"  Rânduri: {count}")

# Inserăm direct date de test dacă nu există
if 'item_categories' in [t[0] for t in tables]:
    # Verifică dacă avem date
    cursor.execute("SELECT COUNT(*) FROM item_categories")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("\nInserăm date de test în baza de date...")
        # Inserăm un test direct
        cursor.execute(
            "INSERT INTO item_categories (market_hash_name, name, updated_at) VALUES (?, ?, ?)",
            ("TEST ITEM", "TEST ITEM", int(time.time()))
        )
        
        # Obținem ID-ul
        cursor.execute("SELECT id FROM item_categories WHERE market_hash_name = ?", ("TEST ITEM",))
        cat_id = cursor.fetchone()[0]
        
        # Inserăm vânzări de test
        cursor.execute(
            "INSERT INTO item_sales (item_id, price, float_value, timestamp) VALUES (?, ?, ?, ?)",
            (cat_id, 100.0, 0.15, int(time.time()))
        )
        
        # Inserăm statistici de test
        cursor.execute(
            "INSERT INTO item_category_stats (category_id, float_min, float_max, avg_price, sales_count) VALUES (?, ?, ?, ?, ?)",
            (cat_id, 0.1, 0.2, 100.0, 1)
        )
        
        conn.commit()
        print("Date de test inserate cu succes!")
    else:
        print(f"\nExistă deja {count} rânduri în item_categories.")

conn.close() 