from odoo import models
from .orderflow_webhook_utils import send_webhook_async

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            send_webhook_async(self.env, 'sale.order.confirmed', {
                'id': rec.id,
                'name': rec.name,
                'partner_id': rec.partner_id.id,
                'partner_name': rec.partner_id.name,
                'amount_total': rec.amount_total,
                'state': rec.state,
                'lines': [{
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal,
                } for line in rec.order_line]
            })
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'state' in vals:
            for rec in self:
                send_webhook_async(self.env, 'sale.order.status_changed', {
                    'id': rec.id,
                    'name': rec.name,
                    'state': rec.state,
                    'amount_total': rec.amount_total,
                })
        return res
