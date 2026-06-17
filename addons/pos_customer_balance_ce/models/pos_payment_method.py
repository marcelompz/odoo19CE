from odoo import models, fields

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    pricelist_id = fields.Many2one('product.pricelist', string='Associated Pricelist', help='If set, this pricelist will be automatically applied to the entire order when this payment method is selected.')
