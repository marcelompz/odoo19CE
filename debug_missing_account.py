import sys
from odoo.addons.account.models.account_move_line import AccountMoveLine

original_create = AccountMoveLine.create

def patched_create(self, vals_list):
    if isinstance(vals_list, dict):
        vals_list = [vals_list]
    for vals in vals_list:
        if not vals.get('account_id'):
            with open('/tmp/missing_account.txt', 'a') as f:
                f.write("\\n!!! MISSING ACCOUNT_ID IN VALS !!!\\n")
                f.write(f"Vals: {vals}\\n")
                if 'name' in vals:
                    f.write(f"Name/Label: {vals.get('name')}\\n")
                if 'product_id' in vals and vals['product_id']:
                    prod = self.env['product.product'].browse(vals['product_id'])
                    f.write(f"Product: {prod.name}\\n")
    return original_create(self, vals_list)

AccountMoveLine.create = patched_create

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if session:
    try:
        session.action_pos_session_closing_control()
    except Exception as e:
        pass
