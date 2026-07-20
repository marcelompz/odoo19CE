from odoo import models, api
from .orderflow_webhook_utils import send_webhook_async

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProductTemplate, self).create(vals_list)
        for rec in records:
            send_webhook_async(self.env, 'product.created', {
                'id': rec.id,
                'name': rec.name,
                'list_price': rec.list_price,
                'default_code': rec.default_code or '',
                'barcode': rec.barcode or '',
            })
        return records

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for rec in self:
            send_webhook_async(self.env, 'product.updated', {
                'id': rec.id,
                'name': rec.name,
                'list_price': rec.list_price,
                'default_code': rec.default_code or '',
                'barcode': rec.barcode or '',
            })
        return res
