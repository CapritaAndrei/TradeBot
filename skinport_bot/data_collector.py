import asyncio
import logging
import skinport
import sys
from .database import MarketDatabase
from .api_manager import SkinportAPIManager
from .config import DB_CONFIG, POPULAR_ITEMS

async def collect_initial_data(client, db):
    """Colectează date inițiale pentru itemele populare."""
    api_manager = SkinportAPIManager(client, db)
    
    logging.info("Starting initial data collection for popular items")
    
    # Verificăm dacă baza de date are structură validă
    logging.info(f"Fisier baza de date: {db.db_path}")
    
    # Arată itemele din listă
    logging.info(f"Iteme populare configurate: {len(POPULAR_ITEMS)}")
    for item in POPULAR_ITEMS:
        logging.info(f"- {item}")
    
    # Împărțim itemele în seturi de maxim 8 (limita API)
    chunks = [POPULAR_ITEMS[i:i+8] for i in range(0, len(POPULAR_ITEMS), 8)]
    
    for chunk in chunks:
        logging.info(f"Collecting data for {len(chunk)} items: {', '.join(chunk)}")
        success = await api_manager.update_sales_history(chunk)
        
        if success:
            logging.info("Successfully collected data")
            # Verificăm câte înregistrări avem acum
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM item_sales")
            count = cursor.fetchone()[0]
            logging.info(f"Numar total de vanzari in baza de date: {count}")
            conn.close()
        else:
            logging.error("Failed to collect data for this chunk")
        
        # Așteptăm 5 minute între chunk-uri pentru a respecta limita API
        if len(chunks) > 1:
            logging.info("Waiting 5 minutes before processing next chunk...")
            await asyncio.sleep(300)
    
    logging.info("Initial data collection completed")
    
    return api_manager

async def main():
    """Script principal pentru colectarea datelor."""
    # Configurare logging cu encoding UTF-8 pentru fișier
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("data_collector.log", encoding="utf-8"),
        ]
    )
    
    # Adăugăm un handler separat pentru consolă care evită caracterele problematice
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger('').addHandler(console)
    
    try:
        # Inițializare
        db = MarketDatabase(DB_CONFIG)
        client = skinport.Client()
        
        # Opțional: Setează autentificarea (doar dacă ai credențiale)
        # client.set_auth(client_id="YOUR_ID", client_secret="YOUR_SECRET")
        
        # Colectează date inițiale
        api_manager = await collect_initial_data(client, db)
        
        # Menține o buclă de actualizare
        logging.info("Starting background update loop")
        await api_manager.background_update_loop()
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 