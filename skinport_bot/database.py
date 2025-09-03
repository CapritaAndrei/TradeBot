import time
import math
import logging
import sqlite3
import os

class MarketDatabase:
    """Bază de date pentru stocarea informațiilor de piață folosind SQLite."""
    
    def __init__(self, db_config=None):
        config = db_config or {'db_path': 'skinport_bot.db'}
        self.db_path = config.get('db_path', 'skinport_bot.db')
        self._setup_db()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _setup_db(self):
        """Inițializează schema bazei de date."""
        # Creăm conexiunea
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Creare tabele
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            market_hash_name TEXT UNIQUE,
            avg_price REAL DEFAULT 0,
            sales_volume_7d INTEGER DEFAULT 0,
            updated_at INTEGER
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_hash_name TEXT UNIQUE,
            category_id INTEGER,
            last_updated INTEGER,
            FOREIGN KEY (category_id) REFERENCES item_categories (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            price REAL,
            float_value REAL,
            timestamp INTEGER,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_category_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            float_min REAL,
            float_max REAL,
            avg_price REAL,
            sales_count INTEGER,
            FOREIGN KEY (category_id) REFERENCES item_categories (id)
        )
        ''')
        
        # Comitem schimbările
        conn.commit()
        conn.close()
    
    def add_sale_with_float(self, market_hash_name, sale_data):
        """Adaugă o vânzare cu float în baza de date."""
        conn = self._get_connection()
        
        try:
            cursor = conn.cursor()
            # Verifică dacă categoria de item există
            cursor.execute(
                "SELECT id FROM item_categories WHERE market_hash_name = ?",
                (market_hash_name,)
            )
            result = cursor.fetchone()
            
            if not result:
                # Creează categoria dacă nu există
                cursor.execute(
                    "INSERT INTO item_categories (market_hash_name, name, updated_at) VALUES (?, ?, ?)",
                    (market_hash_name, market_hash_name, int(time.time()))
                )
                conn.commit()
                
                # Obține ID-ul generat
                cursor.execute(
                    "SELECT id FROM item_categories WHERE market_hash_name = ?",
                    (market_hash_name,)
                )
                result = cursor.fetchone()
            
            item_category_id = result['id']
            
            # MODIFICARE: Verifică dacă această vânzare există deja
            timestamp = sale_data.get("timestamp", int(time.time()))
            price = sale_data.get("price", 0)
            float_value = sale_data.get("float", 0)
            
            cursor.execute(
                "SELECT id FROM item_sales WHERE item_id = ? AND timestamp = ? AND price = ? AND float_value = ?",
                (item_category_id, timestamp, price, float_value)
            )
            existing_sale = cursor.fetchone()
            
            if existing_sale:
                # Vânzarea există deja, nu o mai adăugăm
                logging.debug(f"Ignoring duplicate sale for {market_hash_name} (timestamp: {timestamp})")
                return True
            
            # Adaugă vânzarea deoarece nu există încă
            cursor.execute(
                "INSERT INTO item_sales (item_id, price, float_value, timestamp) "
                "VALUES (?, ?, ?, ?)",
                (
                    item_category_id,
                    price,
                    float_value,
                    timestamp
                )
            )
            
            # Actualizează sau creează bucket-ul de float corespunzător
            float_min = math.floor(float_value * 100) / 100
            float_max = float_min + 0.01
            
            # Verifică dacă bucket-ul există
            cursor.execute(
                "SELECT id, avg_price, sales_count FROM item_category_stats "
                "WHERE category_id = ? AND float_min = ? AND float_max = ?",
                (item_category_id, float_min, float_max)
            )
            bucket = cursor.fetchone()
            
            if bucket:
                # Actualizează bucket-ul
                bucket_id, old_avg, old_count = bucket['id'], bucket['avg_price'], bucket['sales_count']
                new_count = old_count + 1
                new_avg = ((old_avg * old_count) + price) / new_count
                
                cursor.execute(
                    "UPDATE item_category_stats SET avg_price = ?, sales_count = ? "
                    "WHERE id = ?",
                    (new_avg, new_count, bucket_id)
                )
            else:
                # Creează bucket nou
                cursor.execute(
                    "INSERT INTO item_category_stats (category_id, float_min, float_max, avg_price, sales_count) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (item_category_id, float_min, float_max, price, 1)
                )
            
            # Actualizează statisticile din categoria de item
            self._update_item_category_stats(item_category_id)
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding sale: {e}")
            return False
        finally:
            conn.close()
    
    def _update_item_category_stats(self, item_category_id):
        """Actualizează statisticile pentru o categorie de item."""
        conn = self._get_connection()
        
        try:
            cursor = conn.cursor()
            # Calculează prețul mediu din toate vânzările din ultimele 7 zile
            week_ago = int(time.time()) - 7 * 86400
            cursor.execute(
                "SELECT AVG(price) as avg_price, COUNT(*) as sales_count FROM item_sales "
                "WHERE item_id = ? AND timestamp > ?",
                (item_category_id, week_ago)
            )
            result = cursor.fetchone()
            
            if result and result['avg_price']:
                avg_price = result['avg_price']
                sales_volume_7d = result['sales_count']
                
                # Calculează tendința (% schimbare) față de săptămâna anterioară
                two_weeks_ago = int(time.time()) - 14 * 86400
                cursor.execute(
                    "SELECT AVG(price) as prev_avg FROM item_sales "
                    "WHERE item_id = ? AND timestamp > ? AND timestamp < ?",
                    (item_category_id, two_weeks_ago, week_ago)
                )
                prev_result = cursor.fetchone()
                prev_avg = prev_result['prev_avg'] if prev_result and prev_result['prev_avg'] else 0
                
                trend_7d = ((avg_price / prev_avg) - 1) * 100 if prev_avg and prev_avg > 0 else 0
                
                # Calculează scor de prioritate bazat pe volum, preț și vechimea datelor
                last_update = int(time.time())
                cursor.execute(
                    "SELECT updated_at FROM item_categories WHERE id = ?",
                    (item_category_id,)
                )
                last_cat_update_result = cursor.fetchone()
                last_cat_update = last_cat_update_result['updated_at'] if last_cat_update_result else 0
                age_hours = (last_update - last_cat_update) / 3600
                
                # Prioritizează itemurile populare, valoroase și cu date vechi
                priority_score = (sales_volume_7d * 0.5) + (avg_price * 0.001) + (age_hours * 0.1)
                
                # Actualizează categoria
                cursor.execute(
                    "UPDATE item_categories SET updated_at = ? "
                    "WHERE id = ?",
                    (last_update, item_category_id)
                )
                
                conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating item category stats: {e}")
    
    def get_price_for_float(self, market_hash_name, float_value):
        """Obține prețul estimat pentru un item cu float specific."""
        conn = self._get_connection()
        
        try:
            cursor = conn.cursor()
            # Obține ID-ul categoriei
            cursor.execute(
                "SELECT id FROM item_categories WHERE market_hash_name = ?",
                (market_hash_name,)
            )
            result = cursor.fetchone()
            
            if not result:
                return None
            
            item_category_id = result['id']
            
            # Determină bucket-ul de float
            float_min = math.floor(float_value * 100) / 100
            float_max = float_min + 0.01
            
            # Încearcă să găsească bucket-ul exact
            cursor.execute(
                "SELECT avg_price, sales_count FROM item_category_stats "
                "WHERE category_id = ? AND float_min = ? AND float_max = ?",
                (item_category_id, float_min, float_max)
            )
            result = cursor.fetchone()
            
            if result and result['sales_count'] >= 3:  # Avem cel puțin 3 vânzări în acest bucket
                return result['avg_price']
            
            # Dacă nu găsim bucket exact sau nu sunt suficiente date,
            # căutăm vânzări individuale recente cu float-uri similare
            cursor.execute(
                "SELECT price FROM item_sales "
                "WHERE item_id = ? AND ABS(float_value - ?) < 0.02 "
                "ORDER BY timestamp DESC LIMIT 5",
                (item_category_id, float_value)
            )
            results = cursor.fetchall()
            
            if results:
                prices = [row['price'] for row in results]
                return sum(prices) / len(prices)
            
            # Dacă tot nu găsim, folosim prețul mediu al categoriei
            cursor.execute(
                "SELECT avg_price FROM item_categories WHERE id = ?",
                (item_category_id,)
            )
            result = cursor.fetchone()
            
            return result['avg_price'] if result else None
        except Exception as e:
            logging.error(f"Error getting price for float: {e}")
            return None
    
    def get_priority_items_for_update(self, limit=8):
        """Obține itemurile care necesită actualizare prioritară."""
        conn = self._get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT market_hash_name FROM item_categories "
                "ORDER BY updated_at ASC LIMIT ?",
                (limit,)
            )
            
            return [row['market_hash_name'] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting priority items: {e}")
            return []
