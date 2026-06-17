{
    'name': 'Mass Product Import with Inventory',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Products',
    'summary': 'Import products massively from Excel or manual entry with initial stock quantities',
    'description': """
        Mass Product Import with Inventory
        ==================================
        This module allows creating products massively with initial stock quantities through:
        
        * Excel file import (.xlsx format)
        * Manual batch entry directly in Odoo with validation
        
        Features:
        ---------
        - Download Excel template with predefined structure
        - Automatic category creation (Product & POS categories)
        - Initial stock quantity assignment via stock.quant
        - Product tracking configuration (None, Lot, Serial)
        - POS availability flag
        - Duplicate barcode validation
        - Preview and validation before creation
        
        Column mapping (Excel):
        -----------------------
        1. Product Name
        2. Barcode
        3. Available in POS (TRUE/FALSE)
        4. Product Category
        5. POS Category
        6. Sales Price
        7. Cost Price
        8. Quantity on Hand
        9. Product Type (Storable/Consumable/Service)
        10. Tracking (None/Lot/Serial)
    """,
    'author': 'Crossnexion E.A.S.',
    'website': 'https://www.crossnexion.com',
    'license': 'OPL-1',
    'depends': ['product', 'stock', 'point_of_sale'],
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/product_mass_import_preview_views.xml',
        'views/product_mass_import_wizard_views.xml',
        'views/product_batch_import_views.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
