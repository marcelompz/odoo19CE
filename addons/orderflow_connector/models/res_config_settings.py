from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    orderflow_enabled = fields.Boolean(
        string="Habilitar Integración OrderFlow",
        config_parameter='orderflow.enabled',
        help="Activa el envío de webhooks hacia OrderFlow ante eventos de clientes, productos y ventas."
    )
    orderflow_webhook_url = fields.Char(
        string="URL de Webhook OrderFlow",
        config_parameter='orderflow.webhook_url',
        help="Ejemplo: https://pesallaccia.com/api/v1/integrations/webhook/odoo"
    )
    orderflow_api_key = fields.Char(
        string="API Key de Tenant OrderFlow",
        config_parameter='orderflow.api_key',
        help="API Key del tenant en OrderFlow (header x-api-key)"
    )
