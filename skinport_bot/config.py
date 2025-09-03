# Eliminăm configurația MySQL și o înlocuim cu SQLite
DB_CONFIG = {
    'db_path': 'skinport_bot.db'
}

# Configurație pentru bot-ul de trading
BOT_CONFIG = {
    'max_budget_per_item': 100.0,  # Buget maxim per item (în EUR)
    'daily_budget': 500.0,         # Buget zilnic total (în EUR)
    'min_profit_margin': 0.10,     # Profit minim necesar (10%)
    'simulation_mode': True,       # Mod de simulare (fără tranzacții reale)
    'log_file': 'skinport_bot.log' # Fișier pentru logging
}

# Configurație pentru evaluatorul de oportunități
EVALUATOR_CONFIG = {
    'min_discount': 0.15,           # 15% discount minim pentru a considera o oportunitate
    'min_sales': 3,                 # Minim 3 vânzări pentru a considera datele valide
    'max_float_deviation': 0.02,    # Deviație maximă de float pentru comparare
    'confidence_threshold': 0.7,    # Prag de încredere
}

# Lista de iteme populare pentru colectarea datelor inițiale
POPULAR_ITEMS = [
    "AK-47 | Redline (Field-Tested)",
    "AWP | Asiimov (Field-Tested)",
    "M4A4 | Desolate Space (Field-Tested)",
    "USP-S | Kill Confirmed (Field-Tested)",
    "Glock-18 | Water Elemental (Factory New)",
    "Desert Eagle | Blaze (Factory New)",
    "Butterfly Knife | Doppler (Factory New)",
    "Karambit | Doppler (Factory New)"
]