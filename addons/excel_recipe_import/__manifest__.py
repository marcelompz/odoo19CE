# -*- coding: utf-8 -*-
{
    'name': 'Excel Recipe Import',
    'version': '19.0.1.0.1',
    'summary': 'Import Products, MRP BoMs and POS BoMs from Excel Template',
    'author': 'Crossnexion',
    'category': 'Manufacturing',
    'external_dependencies': {'python': ['pandas']},
    'depends': ['base', 'product', 'mrp', 'pos_product_bom'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_recipe_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}
