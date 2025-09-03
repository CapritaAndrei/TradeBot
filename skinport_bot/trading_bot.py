import logging
import time
import asyncio
import json
import skinport

class SkinportTradingBot:
    """Bot pentru trading automat pe Skinport."""
    
    def __init__(self, skinport_client, db, api_manager, evaluator, config=None):
        self.client = skinport_client
        self.db = db
        self.api_manager = api_manager
        self.evaluator = evaluator
        self.config = config or {
            'max_budget_per_item': 100.0,  # Buget maxim per item
            'daily_budget': 500.0,         # Buget zilnic
            'min_profit_margin': 0.10,     # Profit minim 10%
            'simulation_mode': True,       # Mod de simulare (fara tranzactii reale)
            'log_file': 'skinport_bot.log' # Fisier pentru logging
        }
        self.spent_today = 0.0
        self.last_reset = time.time()
        self.purchased_items = []
        self.active_sales = []
        
        # Configurare logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configurează sistemul de logging."""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Handler pentru fișier
        file_handler = logging.FileHandler(self.config.get('log_file', 'skinport_bot.log'))
        file_handler.setLevel(logging.INFO)
        
        # Handler pentru consolă
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Adaugă handlere
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    async def start(self):
        """Pornește bot-ul."""
        logging.info("Starting Skinport Trading Bot")
        
        # Pornește procesul de actualizare în fundal
        asyncio.create_task(self.api_manager.background_update_loop())
        
        # Încarcă datele anterioare, dacă există
        self._load_state()
        
        # Setează handler-ul pentru WebSocket
        self.client.listen("saleFeed")(self.on_sale_feed)
        
        # Pornește clientul Skinport
        try:
            await self.client.connect()
        except Exception as e:
            logging.error(f"Failed to connect: {e}")
    
    async def on_sale_feed(self, data):
        """Handler pentru evenimentele saleFeed."""
        salefeed = skinport.SaleFeed(data=data)
        
        # Resetăm bugetul zilnic dacă e necesar
        current_time = time.time()
        if current_time - self.last_reset > 86400:  # 24 ore
            self.spent_today = 0.0
            self.last_reset = current_time
            logging.info("Daily budget reset")
        
        # Procesăm doar listările noi
        if salefeed.event_type == 'listed':
            for sale in salefeed.sales:
                # Verificăm bugetul
                if sale.sale_price > self.config['max_budget_per_item'] or self.spent_today + sale.sale_price > self.config['daily_budget']:
                    continue
                
                # Evaluăm oportunitatea
                if self.evaluator.evaluate_listing(sale):
                    # Cumpărăm item-ul
                    success = await self.buy_item(sale)
                    
                    if success:
                        # Actualizăm bugetul cheltuit
                        self.spent_today += sale.sale_price
                        
                        # Listăm item-ul pentru vânzare
                        await self.list_item_for_sale(sale)
                        
                        # Salvăm starea curentă
                        self._save_state()
    
    async def buy_item(self, sale):
        """Cumpără un item."""
        if self.config['simulation_mode']:
            logging.info(f"[SIMULATION] Would buy: {sale.market_hash_name} with float {getattr(sale, 'wear', 0):.4f} at {sale.sale_price:.2f}")
            self.purchased_items.append({
                'id': sale.id,
                'market_hash_name': sale.market_hash_name,
                'float': getattr(sale, 'wear', 0),
                'purchase_price': sale.sale_price,
                'purchase_time': time.time()
            })
            return True
        else:
            # Aici ar trebui implementată logica reală de cumpărare
            # Această funcționalitate nu există în API-ul actual
            logging.warning("Real buying functionality not implemented")
            return False
    
    async def list_item_for_sale(self, purchased_sale):
        """Listează un item pentru vânzare."""
        # Calculează prețul de vânzare recomandat
        sell_price = self.evaluator.get_recommended_sell_price(
            purchased_sale.market_hash_name, 
            getattr(purchased_sale, 'wear', 0)
        )
        
        if not sell_price:
            logging.warning(f"Cannot determine sell price for {purchased_sale.market_hash_name}")
            return False
        
        # Verifică marja de profit
        purchase_price = purchased_sale.sale_price
        profit_margin = (sell_price - purchase_price) / purchase_price
        
        if profit_margin < self.config['min_profit_margin']:
            logging.info(f"Profit margin too low ({profit_margin:.2%}) for {purchased_sale.market_hash_name}")
            return False
        
        if self.config['simulation_mode']:
            logging.info(
                f"[SIMULATION] Would list: {purchased_sale.market_hash_name} "
                f"for {sell_price:.2f} (bought at {purchase_price:.2f}, profit: {profit_margin:.2%})"
            )
            self.active_sales.append({
                'market_hash_name': purchased_sale.market_hash_name,
                'float': getattr(purchased_sale, 'wear', 0),
                'purchase_price': purchase_price,
                'sell_price': sell_price,
                'list_time': time.time()
            })
            return True
        else:
            # Aici ar trebui implementată logica reală de listare
            # Această funcționalitate nu există în API-ul actual
            logging.warning("Real listing functionality not implemented")
            return False
    
    def _save_state(self):
        """Salvează starea bot-ului."""
        state = {
            'spent_today': self.spent_today,
            'last_reset': self.last_reset,
            'purchased_items': self.purchased_items,
            'active_sales': self.active_sales
        }
        
        try:
            with open('bot_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logging.error(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Încarcă starea salvată a bot-ului."""
        try:
            with open('bot_state.json', 'r') as f:
                state = json.load(f)
                self.spent_today = state.get('spent_today', 0.0)
                self.last_reset = state.get('last_reset', time.time())
                self.purchased_items = state.get('purchased_items', [])
                self.active_sales = state.get('active_sales', [])
                logging.info(f"Loaded state: {len(self.purchased_items)} purchased items, {len(self.active_sales)} active sales")
        except FileNotFoundError:
            logging.info("No saved state found, starting fresh")
        except Exception as e:
            logging.error(f"Failed to load state: {e}")
    
    def get_performance_summary(self):
        """Returnează un sumar al performanței bot-ului."""
        total_spent = sum(item['purchase_price'] for item in self.purchased_items)
        total_expected = sum(sale['sell_price'] for sale in self.active_sales)
        total_profit = total_expected - total_spent
        
        return {
            'total_items_purchased': len(self.purchased_items),
            'total_items_listed': len(self.active_sales),
            'total_spent': total_spent,
            'total_expected': total_expected,
            'total_profit': total_profit,
            'profit_margin': (total_profit / total_spent) if total_spent > 0 else 0,
            'spent_today': self.spent_today
        }