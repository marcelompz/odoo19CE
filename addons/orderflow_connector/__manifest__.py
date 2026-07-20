{
    'name': 'OrderFlow Connector',
    'version': '19.0.2.0.1',
    'category': 'Sales/Sales',
    'summary': 'Sincronización bidireccional (Push/Pull) y Pull Import Wizard entre Odoo 19 CE y OrderFlow',
    'description': """
OrderFlow Connector para Odoo 19 CE (v19.0.2.0.1)
===================================================
Este módulo permite la integración fluida con la plataforma OrderFlow SaaS:
- Emisión automática de Webhooks al crear o modificar Clientes (res.partner).
- Notificación de cambios en Productos (product.template y product.product).
- Notificación de confirmación y cambio de estado en Pedidos de Venta (sale.order).
- Wizard interactivo de Importación/Pull desde OrderFlow hacia Odoo (Clientes, Productos y Pedidos).
- Panel de configuración gráfica en Ajustes -> Ventas -> OrderFlow.
    """,
    'author': 'OrderFlow Team',
    'website': 'https://pesallaccia.com',
    'license': 'LGPL-3',
    'depends': ['base', 'sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/orderflow_import_wizard_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
