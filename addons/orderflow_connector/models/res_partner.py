from odoo import models, api
from .orderflow_webhook_utils import send_webhook_async

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ResPartner, self).create(vals_list)
        for rec in records:
            if not rec.is_company and rec.type == 'contact':
                send_webhook_async(self.env, 'partner.created', {
                    'id': rec.id,
                    'name': rec.name,
                    'email': rec.email or '',
                    'phone': rec.phone or rec.mobile or '',
                    'vat': rec.vat or '',
                })
        return records

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for rec in self:
            send_webhook_async(self.env, 'partner.updated', {
                'id': rec.id,
                'name': rec.name,
                'email': rec.email or '',
                'phone': rec.phone or rec.mobile or '',
                'vat': rec.vat or '',
            })
        return res
