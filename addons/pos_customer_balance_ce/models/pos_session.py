from odoo import models

class PosSession(models.Model):
    _inherit = 'pos.session'

    def load_pos_data(self):
        loaded_data = super().load_pos_data()
        
        # Inject the settle due product id
        settle_due_product = self.env.ref('pos_customer_balance_ce.product_product_settle_due', raise_if_not_found=False)
        if settle_due_product:
            loaded_data['pos_customer_balance_ce.product_id'] = settle_due_product.id
        else:
            loaded_data['pos_customer_balance_ce.product_id'] = False
            
        return loaded_data
