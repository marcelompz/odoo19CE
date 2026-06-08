{
    'name': "Crossnexion - POS Settle Due CE",
    'summary': """
        Allows paying customer debts directly from the POS Community Edition.
    """,
    'description': """
        This module introduces the Settle Due functionality for the Odoo 19 Community Edition POS.
        It adds a 'Settle Due' button to the partner list which automatically adds a generic payment
        product to the cart, and reconciles the resulting payment with the customer's open invoices.
    """,
    'author': 'Crossnexion E.A.S.',
    'website': 'https://www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Point of Sale',
    'version': '19.0.1.0.0',
    'depends': ['point_of_sale', 'account', 'pos_customer_balance_ce'],
    'data': [
        'data/product_data.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_settle_due_ce/static/src/app/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
