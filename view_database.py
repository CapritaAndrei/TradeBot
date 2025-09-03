import sqlite3
import os
import pandas as pd

def view_database():
    # Verifică dacă fișierul bazei de date există
    db_path = 'skinport_bot.db'
    if not os.path.exists(db_path):
        print(f"Baza de date {db_path} nu există!")
        return
    
    print(f"Analiza bazei de date: {db_path}")
    
    # Conectare la baza de date
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obține lista de tabele
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\nTabele găsite: {len(tables)}")
    for i, table in enumerate(tables):
        table_name = table[0]
        print(f"{i+1}. {table_name}")
        
        # Obține structura tabelului
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("   Structură:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Număr de rânduri
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"   Rânduri: {row_count}")
        
        # Afișează primele 5 rânduri pentru tabelele cu date
        if row_count > 0:
            print(f"   Primele 5 rânduri:")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            # Extrage numele coloanelor
            column_names = [col[1] for col in columns]
            # Creează un DataFrame pentru afișare mai frumoasă
            df = pd.DataFrame(rows, columns=column_names)
            print(df)
        
        print()
    
    conn.close()

if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        print("Instalare pandas pentru afișare tabelară...")
        import subprocess
        subprocess.check_call(["pip", "install", "pandas"])
        import pandas as pd
    
    view_database() 