{
    'name': 'OrderFlow Connector',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Sincronización bidireccional en tiempo real vía Webhooks entre Odoo 19 CE y OrderFlow',
    'description': """
OrderFlow Connector para Odoo 19 CE
====================================
Este módulo permite la integración fluida con la plataforma OrderFlow SaaS:
- Emisión automática de Webhooks al crear o modificar Clientes (res.partner).
- Notificación de cambios en Productos (product.template y product.product).
- Notificación de confirmación y cambio de estado en Pedidos de Venta (sale.order).
- Panel de configuración gráfica en Ajustes -> Ventas -> OrderFlow.
    """,
    'author': 'OrderFlow Team',
    'website': 'https://pesallaccia.com',
    'license': 'LGPL-3',
    'depends': ['base', 'sale', 'product'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
