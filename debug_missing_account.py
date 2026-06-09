import sys
import traceback
from odoo.addons.account.models.account_move_line import AccountMoveLine

original_create = AccountMoveLine.create

def patched_create(self, vals_list):
    if isinstance(vals_list, dict):
        vals_list = [vals_list]
    for vals in vals_list:
        if not vals.get('account_id'):
            print("\n!!! MISSING ACCOUNT_ID IN VALS !!!")
            print("Vals:", vals)
            # Try to print more context if possible
            if 'name' in vals:
                print("Name/Label:", vals.get('name'))
            if 'product_id' in vals:
                prod = self.env['product.product'].browse(vals['product_id'])
                print("Product:", prod.name)
    return original_create(self, vals_list)

AccountMoveLine.create = patched_create

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if not session:
    print("No open sessions found.")
    sys.exit(0)

try:
    print("Trying to close session:", session.name)
    session.action_pos_session_closing_control()
except Exception as e:
    print("Caught Exception:", e)
