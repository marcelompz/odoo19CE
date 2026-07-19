import json
import urllib.request
import urllib.parse
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class OrderflowImportWizard(models.TransientModel):
    _name = 'orderflow.import.wizard'
    _description = 'Wizard de Importación / Pull desde OrderFlow SaaS'

    entity_type = fields.Selection([
        ('partner', '👥 Clientes y Contactos'),
        ('product', '📦 Catálogo de Productos'),
        ('order', '🛒 Pedidos de Venta')
    ], string="Tipo de Registro a Consultar", default='product', required=True)

    line_ids = fields.One2many(
        'orderflow.import.line',
        'wizard_id',
        string="Registros Encontrados en OrderFlow"
    )

    total_count = fields.Integer(string="Total Encontrados", compute="_compute_total_count")
    selected_count = fields.Integer(string="Seleccionados", compute="_compute_total_count")

    @api.depends('line_ids', 'line_ids.selected')
    def _compute_total_count(self):
        for rec in self:
            rec.total_count = len(rec.line_ids)
            rec.selected_count = len(rec.line_ids.filtered(lambda l: l.selected))

    def action_fetch_orderflow_data(self):
        """Consulta la API de OrderFlow según el entity_type seleccionado"""
        self.ensure_one()
        self.line_ids.unlink()

        ICP = self.env['ir.config_parameter'].sudo()
        webhook_url = ICP.get_param('orderflow.webhook_url', '')
        api_key = ICP.get_param('orderflow.api_key', '')

        if not api_key:
            raise UserError("No se encuentra configurada la API Key de OrderFlow en Ajustes.")

        base_url = "https://pesallaccia.com/api/v1"
        if webhook_url:
            parsed = urllib.parse.urlparse(webhook_url)
            if parsed.scheme and parsed.netloc:
                base_url = f"{parsed.scheme}://{parsed.netloc}/api/v1"

        endpoint_map = {
            'partner': f"{base_url}/contacts",
            'product': f"{base_url}/products",
            'order': f"{base_url}/orders"
        }

        url = endpoint_map.get(self.entity_type)
        req = urllib.request.Request(
            url,
            headers={
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'Odoo19-OrderFlowConnector/2.0'
            },
            method='GET'
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                body = resp.read().decode('utf-8')
                data = json.loads(body)
        except Exception as e:
            _logger.error("Error al consultar OrderFlow (%s): %s", url, str(e))
            raise UserError(f"Error al conectar con OrderFlow en {url}: {str(e)}")

        items = data if isinstance(data, list) else (data.get('data') or data.get('items') or [])

        line_vals = []
        for item in items:
            ext_id = str(item.get('id') or item.get('order_id') or '')
            name = item.get('name') or item.get('order_id') or item.get('email') or 'Sin Nombre'
            
            detail = ''
            email_sku = ''

            if self.entity_type == 'product':
                email_sku = item.get('sku') or item.get('id', '')[:8]
                price = item.get('price', 0)
                detail = f"Precio: {price} | Categ: {item.get('category', 'General')}"
            elif self.entity_type == 'partner':
                email_sku = item.get('email') or item.get('phone') or ''
                detail = f"Tel: {item.get('phone', '')} | RUC/Tax: {item.get('taxId', '')}"
            elif self.entity_type == 'order':
                email_sku = item.get('customerName') or item.get('contactId') or ''
                detail = f"Total: {item.get('total', 0)} | Status: {item.get('status', 'CONFIRMED')}"

            line_vals.append({
                'wizard_id': self.id,
                'selected': True,
                'external_id': ext_id,
                'name': name,
                'email_or_sku': email_sku,
                'detail_info': detail,
                'raw_json': json.dumps(item, ensure_ascii=False),
                'import_status': 'pending'
            })

        if line_vals:
            self.env['orderflow.import.line'].create(line_vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'orderflow.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import_selected_records(self):
        """Importa a la base de datos de Odoo los registros seleccionados"""
        self.ensure_one()
        selected_lines = self.line_ids.filtered(lambda l: l.selected)

        if not selected_lines:
            raise UserError("No has seleccionado ningún registro para importar.")

        imported_count = 0
        for line in selected_lines:
            try:
                data = json.loads(line.raw_json or '{}')
                if self.entity_type == 'partner':
                    self._import_partner(data)
                elif self.entity_type == 'product':
                    self._import_product(data)
                elif self.entity_type == 'order':
                    self._import_order(data)

                line.write({'import_status': 'done', 'error_message': False})
                imported_count += 1
            except Exception as e:
                _logger.error("Error importando linea %s: %s", line.name, str(e))
                line.write({'import_status': 'error', 'error_message': str(e)})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Importación Finalizada',
                'message': f'Se importaron exitosamente {imported_count} de {len(selected_lines)} registros a Odoo.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _import_partner(self, data):
        Partner = self.env['res.partner'].sudo()
        email = data.get('email')
        name = data.get('name') or email or 'Cliente OrderFlow'

        domain = []
        if email:
            domain = [('email', '=', email)]
        elif name:
            domain = [('name', '=', name)]

        existing = Partner.search(domain, limit=1) if domain else Partner.browse()
        vals = {
            'name': name,
            'email': email or False,
            'phone': data.get('phone') or False,
            'comment': f"Importado desde OrderFlow (ID: {data.get('id')})"
        }
        if existing:
            existing.write(vals)
        else:
            Partner.create(vals)

    def _import_product(self, data):
        Product = self.env['product.template'].sudo()
        sku = data.get('sku')
        name = data.get('name') or 'Producto OrderFlow'
        price = float(data.get('price') or 0.0)

        existing = False
        if sku:
            existing = Product.search([('default_code', '=', sku)], limit=1)
        if not existing:
            existing = Product.search([('name', '=', name)], limit=1)

        vals = {
            'name': name,
            'list_price': price,
            'default_code': sku or False,
            'description': data.get('description') or False,
            'type': 'consu',
        }
        if existing:
            existing.write(vals)
        else:
            Product.create(vals)

    def _import_order(self, data):
        SaleOrder = self.env['sale.order'].sudo()
        Partner = self.env['res.partner'].sudo()
        Product = self.env['product.template'].sudo()

        order_ref = data.get('order_id') or data.get('id') or 'OF-ORDER'
        existing = SaleOrder.search([('client_order_ref', '=', order_ref)], limit=1)

        customer_name = data.get('customerName') or 'Cliente OrderFlow'
        partner = Partner.search([('name', '=', customer_name)], limit=1)
        if not partner:
            partner = Partner.create({'name': customer_name})

        if existing:
            return existing

        items = data.get('items') or []
        order_lines = []

        for item in items:
            prod_name = item.get('name') or 'Producto Genérico'
            prod_price = float(item.get('price') or 0.0)
            prod_qty = float(item.get('quantity') or 1.0)

            product = Product.search([('name', '=', prod_name)], limit=1)
            if not product:
                product = Product.create({'name': prod_name, 'list_price': prod_price})

            order_lines.append((0, 0, {
                'product_id': product.product_variant_id.id,
                'name': prod_name,
                'product_uom_qty': prod_qty,
                'price_unit': prod_price,
            }))

        order_vals = {
            'partner_id': partner.id,
            'client_order_ref': order_ref,
            'order_line': order_lines,
        }
        return SaleOrder.create(order_vals)


class OrderflowImportLine(models.TransientModel):
    _name = 'orderflow.import.line'
    _description = 'Línea del Wizard de Importación OrderFlow'

    wizard_id = fields.Many2one('orderflow.import.wizard', ondelete='cascade')
    selected = fields.Boolean(string="Importar", default=True)
    external_id = fields.Char(string="ID OrderFlow")
    name = fields.Char(string="Nombre / Ref")
    email_or_sku = fields.Char(string="Email / SKU")
    detail_info = fields.Char(string="Detalle / Precio")
    raw_json = fields.Text(string="Payload JSON")
    import_status = fields.Selection([
        ('pending', '⏳ Pendiente'),
        ('done', '✅ Importado'),
        ('error', '❌ Error')
    ], string="Estado", default='pending')
    error_message = fields.Char(string="Error Detallado")
