import asyncio
import logging
import skinport
from skinport_bot.database import MarketDatabase
from skinport_bot.api_manager import SkinportAPIManager
from skinport_bot.evaluator import OpportunityEvaluator
from skinport_bot.trading_bot import SkinportTradingBot
from skinport_bot.config import DB_CONFIG, BOT_CONFIG, EVALUATOR_CONFIG

async def main():
    """Funcția principală pentru rularea bot-ului."""
    # Configurare logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(BOT_CONFIG.get('log_file', "skinport_bot.log")),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Inițializare componente
        logging.info("Initializing components...")
        
        # Baza de date
        db = MarketDatabase(DB_CONFIG)
        logging.info("Database initialized")
        
        # Client Skinport
        client = skinport.Client()
        logging.info("Skinport client created")
        
        # Manager API
        api_manager = SkinportAPIManager(client, db)
        logging.info("API manager initialized")
        
        # Evaluator de oportunități
        evaluator = OpportunityEvaluator(db, EVALUATOR_CONFIG)
        logging.info("Opportunity evaluator initialized")
        
        # Bot de trading
        bot = SkinportTradingBot(client, db, api_manager, evaluator, BOT_CONFIG)
        logging.info("Trading bot initialized")
        
        # Pornește bot-ul
        logging.info("Starting bot...")
        await bot.start()
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 