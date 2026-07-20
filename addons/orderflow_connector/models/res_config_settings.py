import logging
import urllib.request
import urllib.error
import json
from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    orderflow_enabled = fields.Boolean(
        string="Habilitar Integración OrderFlow",
        config_parameter='orderflow.enabled',
        help="Activa el envío de webhooks hacia OrderFlow."
    )
    orderflow_webhook_url = fields.Char(
        string="URL de Webhook OrderFlow",
        config_parameter='orderflow.webhook_url',
        default="https://pesallaccia.com/api/v1/integrations/orderflow/webhook",
        help="Ejemplo: https://pesallaccia.com/api/v1/integrations/orderflow/webhook"
    )
    orderflow_api_key = fields.Char(
        string="API Key de Tenant OrderFlow",
        config_parameter='orderflow.api_key',
        help="API Key del tenant en OrderFlow (header x-api-key)"
    )

    # Opciones de selección de datos a compartir
    orderflow_sync_partners = fields.Boolean(
        string="Sincronizar Clientes (res.partner)",
        config_parameter='orderflow.sync_partners',
        default=True,
        help="Envía notificaciones ante creación o edición de clientes."
    )
    orderflow_sync_products = fields.Boolean(
        string="Sincronizar Productos (product.template)",
        config_parameter='orderflow.sync_products',
        default=True,
        help="Envía notificaciones ante cambios en productos y precios."
    )
    orderflow_sync_orders = fields.Boolean(
        string="Sincronizar Pedidos de Venta (sale.order)",
        config_parameter='orderflow.sync_orders',
        default=True,
        help="Envía notificaciones al confirmar pedidos de venta."
    )
    orderflow_sync_inventory = fields.Boolean(
        string="Sincronizar Stock / Inventario",
        config_parameter='orderflow.sync_inventory',
        default=False,
        help="Envía actualizaciones de cantidades de inventario a OrderFlow."
    )

    def action_test_orderflow_connection(self):
        """ Probar la conexión enviando una petición HTTP al Webhook / API de OrderFlow """
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        webhook_url = ICP.get_param('orderflow.webhook_url', '').strip()
        api_key = ICP.get_param('orderflow.api_key', '').strip()

        if not webhook_url:
            raise UserError(_("Por favor, ingrese la URL del Webhook de OrderFlow."))

        try:
            payload = json.dumps({'event': 'ping', 'data': {'test': True}}).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Odoo-OrderFlow-Test/19.0',
                    'x-api-key': api_key or ''
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                status_code = response.status
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Conexión Exitosa"),
                        'message': _("La conexión con OrderFlow respondió correctamente con HTTP %s.") % status_code,
                        'type': 'success',
                        'sticky': False,
                    }
                }
        except Exception as e:
            _logger.warning("[OrderFlow Connection Test Error]: %s", str(e))
            raise UserError(_("Error de Conexión con OrderFlow: %s") % str(e))

    def action_open_orderflow_web(self):
        """ Redirige al panel web de OrderFlow """
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://pesallaccia.com/admin',
            'target': 'new',
        }
