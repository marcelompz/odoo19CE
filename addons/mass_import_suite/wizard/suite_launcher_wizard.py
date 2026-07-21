# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class MassImportSuiteWizard(models.TransientModel):
    _name = 'mass.import.suite'
    _description = 'Mass Import Suite Launcher'

    def action_open_product_import(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.mass.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_open_recipe_import(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'excel.recipe.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
