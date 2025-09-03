import pymysql
import logging
from skinport_bot.config import DB_CONFIG

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_db_connection():
    """Testează conexiunea la baza de date."""
    try:
        # Afișare configurație (fără parolă)
        safe_config = {k: v for k, v in DB_CONFIG.items() if k != 'password'}
        logging.info(f"Încercăm conectarea cu configurația: {safe_config}")
        
        # Încercăm să ne conectăm
        conn = pymysql.connect(**DB_CONFIG)
        
        logging.info("Conexiune reușită la baza de date!")
        
        # Testăm execuția unei interogări simple
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            logging.info(f"Tabele existente în baza de date: {tables}")
        
        # Închidem conexiunea
        conn.close()
        logging.info("Conexiune închisă cu succes")
        return True
        
    except Exception as e:
        logging.error(f"Eroare la conectarea la baza de date: {e}")
        return False

if __name__ == "__main__":
    test_db_connection() 