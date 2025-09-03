import logging
import time
from skinport_bot.database import MarketDatabase

# Configurăm logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Inițializăm baza de date
db = MarketDatabase({'db_path': 'skinport_bot.db'})

# Adăugăm câteva date de test
test_items = [
    "AK-47 | Redline (Field-Tested)",
    "AWP | Asiimov (Field-Tested)"
]

for item in test_items:
    # Adăugăm câteva vânzări cu float-uri diferite
    for i in range(5):
        sale_data = {
            "price": 20.0 + i * 1.5,  # Simulăm prețuri diferite
            "float": 0.15 + i * 0.05,  # Simulăm float-uri diferite
            "timestamp": int(time.time()) - i * 86400  # Simulăm timestamp-uri diferite
        }
        
        success = db.add_sale_with_float(item, sale_data)
        if success:
            logging.info(f"Added sale for {item} with float {sale_data['float']} at price {sale_data['price']}")
        else:
            logging.error(f"Failed to add sale for {item}")

# Testăm funcția de obținere a prețului pentru un float anume
for item in test_items:
    float_value = 0.22  # Un float de test
    price = db.get_price_for_float(item, float_value)
    logging.info(f"Estimated price for {item} with float {float_value}: {price}")

# Obținem itemele prioritare pentru actualizare
priority_items = db.get_priority_items_for_update(limit=5)
logging.info(f"Priority items for update: {', '.join(priority_items) if priority_items else 'None'}")

logging.info("Test completed successfully") 