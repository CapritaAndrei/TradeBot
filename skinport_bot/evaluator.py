import logging
import time

class OpportunityEvaluator:
    """Evaluator de oportunități care ia în considerare float-ul."""
    
    def __init__(self, db, config=None):
        self.db = db
        self.config = config or {
            'min_discount': 0.15,          # 15% discount minim
            'min_sales': 3,                # Minim 3 vânzări pentru referință
            'max_float_deviation': 0.02,   # Deviație maximă de float pentru comparare
            'confidence_threshold': 0.7,   # Prag de încredere
        }
        self.opportunity_log = []  # Pentru analiza performanței
    
    def evaluate_listing(self, sale):
        """Evaluează o listare pentru a determina dacă este o oportunitate."""
        market_hash_name = sale.market_hash_name
        current_price = sale.sale_price
        float_value = getattr(sale, 'wear', 0)  # Presupunem că wear reprezintă float-ul
        
        # Obținem prețul de referință pentru acest float
        reference_price = self.db.get_price_for_float(market_hash_name, float_value)
        
        if not reference_price or reference_price <= 0:
            logging.info(f"No reference price found for {market_hash_name} with float {float_value}")
            return False
        
        # Calculăm discount-ul
        discount = (reference_price - current_price) / reference_price
        
        # Evaluăm oportunitatea
        is_opportunity = discount >= self.config['min_discount']
        
        if is_opportunity:
            # Înregistrăm pentru analiză
            self.opportunity_log.append({
                'timestamp': time.time(),
                'market_hash_name': market_hash_name,
                'float': float_value,
                'listing_price': current_price,
                'reference_price': reference_price,
                'discount': discount
            })
            
            logging.info(
                f"Opportunity detected: {market_hash_name} with float {float_value:.4f} "
                f"at {current_price:.2f} (ref: {reference_price:.2f}, discount: {discount:.2%})"
            )
        
        return is_opportunity
    
    def get_recommended_sell_price(self, market_hash_name, float_value):
        """Determină prețul recomandat de vânzare pentru un item achiziționat."""
        # Obține prețul de referință
        reference_price = self.db.get_price_for_float(market_hash_name, float_value)
        
        if not reference_price:
            return None
        
        # Recomandă un preț cu 5% sub referință pentru vânzare rapidă
        return reference_price * 0.95
    
    def get_opportunities_summary(self):
        """Returnează un sumar al oportunităților detectate."""
        if not self.opportunity_log:
            return "No opportunities detected yet."
        
        total_opportunities = len(self.opportunity_log)
        avg_discount = sum(op['discount'] for op in self.opportunity_log) / total_opportunities
        
        # Grupează oportunități după item
        items = {}
        for op in self.opportunity_log:
            item_name = op['market_hash_name']
            if item_name not in items:
                items[item_name] = []
            items[item_name].append(op)
        
        # Top 5 iteme cu cele mai multe oportunități
        top_items = sorted(items.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        
        summary = f"Total opportunities: {total_opportunities}\n"
        summary += f"Average discount: {avg_discount:.2%}\n\n"
        summary += "Top 5 items:\n"
        
        for item_name, ops in top_items:
            avg_item_discount = sum(op['discount'] for op in ops) / len(ops)
            summary += f"- {item_name}: {len(ops)} opportunities, avg discount: {avg_item_discount:.2%}\n"
        
        return summary 