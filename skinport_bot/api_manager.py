import asyncio
import time
import logging

class SkinportAPIManager:
    """Manager pentru API-ul Skinport cu rate limiting și caching avansat."""
    
    def __init__(self, client, db):
        self.client = client  # Clientul Skinport existent
        self.db = db          # Baza de date implementată
        self.call_history = []
        self.call_limit = 8   # Limită de 8 call-uri
        self.period = 300     # Perioadă de 5 minute (300 secunde)
        self.lock = asyncio.Lock()
    
    async def can_make_api_call(self):
        """Verifică dacă putem face un nou call API."""
        async with self.lock:
            current_time = time.time()
            
            # Curățăm istoricul vechi
            self.call_history = [t for t in self.call_history if current_time - t < self.period]
            
            # Verificăm dacă suntem sub limită
            return len(self.call_history) < self.call_limit
    
    async def register_api_call(self):
        """Înregistrează un call API."""
        async with self.lock:
            self.call_history.append(time.time())
    
    async def wait_for_rate_limit(self):
        """Așteaptă până când putem face un nou call API."""
        while not await self.can_make_api_call():
            # Calculăm cât trebuie să așteptăm
            oldest_call = min(self.call_history) if self.call_history else time.time()
            wait_time = self.period - (time.time() - oldest_call) + 1  # +1 secundă pentru siguranță
            
            logging.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
    
    async def update_sales_history(self, market_hash_names):
        """Actualizează istoricul de vânzări pentru itemurile specificate."""
        if not market_hash_names:
            return False
        
        # Așteptăm dacă am atins limita
        await self.wait_for_rate_limit()
        
        try:
            # Înregistrăm call-ul
            await self.register_api_call()
            
            # Facem call-ul API
            sales_history = await self.client.get_sales_history(*market_hash_names)
            
            # Adaugă log pentru a vedea ce primim de la API
            logging.info(f"Received sales history data for {len(sales_history)} items")
            
            total_sales_added = 0  # Contor pentru vânzări adăugate
            
            # Procesăm și stocăm datele
            for item in sales_history:
                # Pentru fiecare perioadă de timp
                item_sales_added = 0  # Contor pentru vânzări per item
                
                for period_name in ['last_24_hours', 'last_7_days', 'last_30_days', 'last_90_days']:
                    # Obține atributul ca dicționar
                    period_data = getattr(item, period_name, None)
                    if not period_data:
                        continue
                    
                    # Extrage vânzările dacă există
                    # Acces adaptat pentru a gestiona diferite structuri de date
                    if isinstance(period_data, dict):
                        sales = period_data.get('sales', [])
                    else:
                        # Încercăm să accesăm ca atribut
                        sales = getattr(period_data, 'sales', [])
                        # Convertim la listă dacă e necesar
                        if not isinstance(sales, list):
                            sales = []
                    
                    # Adaugă logging pentru numărul de vânzări găsite
                    logging.info(f"Found {len(sales)} sales for {item.market_hash_name} in {period_name}")
                    
                    for sale in sales:
                        # Conversia sale la dict dacă e necesar
                        if not isinstance(sale, dict):
                            # Încercăm să extragem atributele din obiect
                            sale_dict = {}
                            for attr in ['timestamp', 'price', 'float']:
                                if hasattr(sale, attr):
                                    sale_dict[attr] = getattr(sale, attr)
                            sale = sale_dict
                        
                        # Adaugă vânzarea în baza de date
                        success = self.db.add_sale_with_float(
                            item.market_hash_name,
                            {
                                'timestamp': sale.get('timestamp', int(time.time())),
                                'price': sale.get('price', 0),
                                'float': sale.get('float', 0),
                            }
                        )
                        
                        # Incrementăm contorul dacă s-a adăugat cu succes
                        if success:
                            item_sales_added += 1
                            total_sales_added += 1
                
                logging.info(f"Added {item_sales_added} new sales for {item.market_hash_name}")
            
            logging.info(f"Updated sales history for {len(market_hash_names)} items, added {total_sales_added} new sales")
            return True
            
        except Exception as e:
            logging.error(f"Error updating sales history: {e}")
            return False
    
    async def background_update_loop(self):
        """Rulează în fundal pentru a actualiza continuu baza de date."""
        while True:
            try:
                # Obține itemurile prioritare pentru actualizare
                priority_items = self.db.get_priority_items_for_update(limit=8)
                
                if priority_items:
                    await self.update_sales_history(priority_items)
                else:
                    logging.info("No priority items to update")
                
                # Așteaptă până la următoarea rundă de actualizări
                await asyncio.sleep(60)  # Un minut între încercări
            except Exception as e:
                logging.error(f"Error in background update loop: {e}")
                await asyncio.sleep(60)  # Așteaptă în caz de eroare 