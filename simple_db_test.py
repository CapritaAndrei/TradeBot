import logging
import sqlite3

# Configurare logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sqlite_connection():
    """Testează conexiunea la baza de date SQLite"""
    try:
        # Creăm o bază de date temporară în memorie pentru test
        logger.info("Încercăm conectarea la SQLite...")
        conn = sqlite3.connect('skinport_bot.db')
        cursor = conn.cursor()
        
        # Creăm un tabel simplu de test
        logger.info("Creăm un tabel de test...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL
        )
        ''')
        
        # Inserăm date de test
        logger.info("Inserăm date de test...")
        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", 
                      ('test_item', 10.5))
        conn.commit()
        
        # Verificăm că datele au fost inserate
        logger.info("Verificăm datele...")
        cursor.execute("SELECT * FROM test_table")
        results = cursor.fetchall()
        logger.info(f"Rezultate: {results}")
        
        # Încheierea testului
        conn.close()
        logger.info("Test SQLite completat cu succes!")
        return True
        
    except Exception as e:
        logger.error(f"Eroare la testarea bazei de date SQLite: {e}")
        return False

if __name__ == "__main__":
    test_sqlite_connection() 