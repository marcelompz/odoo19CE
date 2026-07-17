#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import/Update system settings, outgoing email servers, warehouses, journals, 
product categories accounting settings, and analytic accounts from JSON.
"""

import sys
import json
import os

sys.path.append('/usr/lib/python3/dist-packages')
os.environ.setdefault('ODOO_RC', '/etc/odoo/odoo.conf')

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

def import_settings():
    db_host = os.environ.get('DB_HOST', 'db5436')
    db_port = os.environ.get('DB_PORT', '5432')
    db_user = os.environ.get('DB_USER', 'odoo')
    db_password = os.environ.get('DB_PASSWD', 'cross.159753')
    db_name = os.environ.get('DB_NAME', 'prod')
    addons_path = os.environ.get('ADDONS_PATH', '/mnt/extra-addons-customize,/mnt/extra-addons-l10py,/usr/lib/python3/dist-packages/odoo/addons')
    valid_addons = [p for p in addons_path.split(',') if os.path.exists(p)]

    odoo.tools.config.parse_config([
        '--db_host', db_host,
        '--db_port', db_port,
        '--db_user', db_user,
        '--db_password', db_password,
        '--addons-path', ','.join(valid_addons),
    ])

    print("=" * 60)
    print(f"Importing System Settings on database: {db_name}")
    print("=" * 60)
    
    settings_path = '/mnt/migracion/settings.json'
    if not os.path.exists(settings_path):
        print("ℹ settings.json not found, skipping system settings update.")
        return
        
    with open(settings_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    registry = odoo.modules.registry.Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 0. Currency (PYG)
        try:
            pyg = env['res.currency'].with_context(active_test=False).search([('name', '=', 'PYG')], limit=1)
            if pyg and not pyg.active:
                pyg.write({'active': True})
                print("  ✓ Activated PYG currency (Guaraní) in the system.")
            
            company = env['res.company'].browse(1)
            if company.exists() and company.currency_id and not company.currency_id.active:
                company.currency_id.write({'active': True})
                print(f"  ✓ Activated company currency: {company.currency_id.name}")
        except Exception as e:
            print(f"  ⚠️ Currency configuration warning: {e}")
        
        # 1. Outgoing Mail Server (SMTP)
        try:
            smtp_data = config.get('smtp', {})
            if smtp_data and 'ir.mail_server' in env:
                print("Configuring Outgoing SMTP Email Server...")
                server_vals = {
                    'name': smtp_data.get('name', 'SMTP Server'),
                    'smtp_host': smtp_data.get('host'),
                    'smtp_port': int(smtp_data.get('port', 587)),
                    'smtp_encryption': smtp_data.get('encryption', 'starttls'),
                    'smtp_user': smtp_data.get('username'),
                    'smtp_pass': smtp_data.get('password'),
                }
                existing_smtp = env['ir.mail_server'].search([('name', '=', server_vals['name'])], limit=1)
                if existing_smtp:
                    existing_smtp.write(server_vals)
                    print(f"  ✓ Updated SMTP Server: {server_vals['name']}")
                else:
                    env['ir.mail_server'].create(server_vals)
                    print(f"  ✓ Created SMTP Server: {server_vals['name']}")
        except Exception as e:
            print(f"  ⚠️ SMTP Server configuration warning: {e}")
                
        # 2. Warehouses (Depósitos)
        try:
            warehouses_list = config.get('warehouses', [])
            if warehouses_list and 'stock.warehouse' in env:
                print("Configuring Warehouses (Depósitos)...")
                for wh_data in warehouses_list:
                    code = wh_data.get('code')
                    name = wh_data.get('name')
                    if not code or not name:
                        continue
                    wh = env['stock.warehouse'].search([('code', '=', code)], limit=1)
                    wh_vals = {
                        'name': name,
                        'code': code,
                    }
                    if wh:
                        wh.write(wh_vals)
                        print(f"  ✓ Updated Warehouse: {name} ({code})")
                    else:
                        env['stock.warehouse'].create(wh_vals)
                        print(f"  ✓ Created Warehouse: {name} ({code})")
        except Exception as e:
            print(f"  ⚠️ Warehouse configuration warning: {e}")
                    
        # 3. Product Categories (Costo y Valoración de Inventario)
        try:
            prod_cat_list = config.get('product_categories_config', [])
            if prod_cat_list and 'product.category' in env:
                print("Configuring Product Categories Costing and Inventory Valuation...")
                for cat_data in prod_cat_list:
                    cat_name = cat_data.get('name')
                    if not cat_name:
                        continue
                    cat = env['product.category'].search([('name', '=', cat_name)], limit=1)
                    if not cat:
                        cat = env['product.category'].create({'name': cat_name})
                        print(f"  Created Product Category: {cat_name}")
                    
                    cat_vals = {
                        'property_cost_method': cat_data.get('property_cost_method', 'average'),
                        'property_valuation': cat_data.get('property_valuation', 'real_time'),
                    }
                    
                    if 'account.account' in env:
                        val_code = cat_data.get('stock_valuation_account')
                        in_code = cat_data.get('stock_input_account')
                        out_code = cat_data.get('stock_output_account')
                        
                        if val_code:
                            acc = env['account.account'].search([('code', '=', val_code)], limit=1)
                            if acc:
                                cat_vals['property_stock_valuation_account_id'] = acc.id
                        if in_code:
                            acc = env['account.account'].search([('code', '=', in_code)], limit=1)
                            if acc:
                                cat_vals['property_stock_account_input_categ_id'] = acc.id
                        if out_code:
                            acc = env['account.account'].search([('code', '=', out_code)], limit=1)
                            if acc:
                                cat_vals['property_stock_account_output_categ_id'] = acc.id
                            
                    cat.write(cat_vals)
                    print(f"  ✓ Category configured: {cat_name}")
        except Exception as e:
            print(f"  ⚠️ Product categories configuration warning: {e}")

        # 4. Accounting Settings (Redondeo de IVA y Plazos de Pago)
        try:
            acc_data = config.get('accounting', {})
            if acc_data:
                print("Configuring Accounting Rounding & Payment Terms...")
                company = env['res.company'].browse(1)
                rounding = acc_data.get('tax_calculation_rounding_method', 'round_per_line')
                if company.exists():
                    company.write({'tax_calculation_rounding_method': rounding})
                    print(f"  ✓ Company Tax Rounding set to: {rounding}")
                
                rename_to = acc_data.get('payment_immediate_rename_to')
                if rename_to and 'account.payment.term' in env:
                    term = env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
                    if not term:
                        term = env['account.payment.term'].search([('name', '=ilike', 'inmediato')], limit=1)
                    if term:
                        term.write({'name': rename_to})
                        print(f"  ✓ Payment Term Immediate renamed to: {rename_to}")
        except Exception as e:
            print(f"  ⚠️ Accounting settings warning: {e}")

        # 5. Journals (Diarios Contables por Sucursal/Localidad)
        try:
            journals_list = config.get('journals', [])
            if journals_list and 'account.journal' in env:
                print("Configuring Account Journals (Diarios contables)...")
                for jr_data in journals_list:
                    code = jr_data.get('code')
                    name = jr_data.get('name')
                    jr_type = jr_data.get('type')
                    if not code or not name or not jr_type:
                        continue
                    jr = env['account.journal'].search([('code', '=', code)], limit=1)
                    jr_vals = {
                        'name': name,
                        'code': code,
                        'type': jr_type,
                    }
                    if jr:
                        upd_vals = {'name': name, 'code': code}
                        if jr.type != jr_type:
                            upd_vals['type'] = jr_type
                        jr.write(upd_vals)
                        print(f"  ✓ Updated Journal: {name} ({code})")
                    else:
                        env['account.journal'].create(jr_vals)
                        print(f"  ✓ Created Journal: {name} ({code})")
        except Exception as e:
            print(f"  ⚠️ Journals configuration warning: {e}")

        # 6. Analytic Accounts (Cuentas Analíticas por Sucursal)
        try:
            analytic_list = config.get('analytic_accounts', [])
            if analytic_list and 'account.analytic.account' in env and 'account.analytic.plan' in env:
                print("Configuring Analytic Accounts...")
                plan = env['account.analytic.plan'].search([], limit=1)
                if not plan:
                    plan = env['account.analytic.plan'].create({'name': 'Default Plan'})
                    print(f"  Created default Analytic Plan: {plan.name}")
                    
                for ana_data in analytic_list:
                    code = ana_data.get('code')
                    name = ana_data.get('name')
                    if not code or not name:
                        continue
                    ana = env['account.analytic.account'].search([('code', '=', code)], limit=1)
                    ana_vals = {
                        'name': name,
                        'code': code,
                        'plan_id': plan.id,
                    }
                    if ana:
                        ana.write(ana_vals)
                        print(f"  ✓ Updated Analytic Account: {name} ({code})")
                    else:
                        env['account.analytic.account'].create(ana_vals)
                        print(f"  ✓ Created Analytic Account: {name} ({code})")
        except Exception as e:
            print(f"  ⚠️ Analytic accounts configuration warning: {e}")

        # 7. POS Config (Punto de Venta)
        try:
            if 'pos.config' in env and 'account.journal' in env and 'pos.payment.method' in env:
                print("Configuring Point of Sale (POS)...")
                cash_journal = env['account.journal'].search([('type', '=', 'cash'), ('company_id', '=', 1)], limit=1)
                cash_method = env['pos.payment.method'].search([('journal_id', '=', cash_journal.id)], limit=1) if cash_journal else None
                if cash_journal and not cash_method:
                    cash_method = env['pos.payment.method'].create({
                        'name': 'Efectivo',
                        'journal_id': cash_journal.id,
                    })
                    print(f"  ✓ Created POS Payment Method: {cash_method.name}")

                bank_journal = env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', 1)], limit=1)
                bank_method = env['pos.payment.method'].search([('journal_id', '=', bank_journal.id)], limit=1) if bank_journal else None
                if bank_journal and not bank_method:
                    bank_method = env['pos.payment.method'].create({
                        'name': 'Banco/Tarjeta',
                        'journal_id': bank_journal.id,
                    })
                    print(f"  ✓ Created POS Payment Method: {bank_method.name}")

                invoice_journal = env['account.journal'].search([
                    ('type', '=', 'sale'),
                    ('company_id', '=', 1)
                ], limit=1)

                pos_config = env['pos.config'].search([('name', '=', 'Caja Principal')], limit=1)
                has_active_session = False
                if pos_config and 'pos.session' in env:
                    active_sessions = env['pos.session'].search([
                        ('config_id', '=', pos_config.id),
                        ('state', '!=', 'closed')
                    ])
                    if active_sessions:
                        has_active_session = True
                        print("  ℹ POS Caja Principal has active sessions. Skipping configuration updates to avoid Odoo locks.")

                if not has_active_session:
                    payment_methods = []
                    if cash_method:
                        payment_methods.append(cash_method.id)
                    if bank_method:
                        payment_methods.append(bank_method.id)
                        
                    pos_vals = {
                        'name': 'Caja Principal',
                    }
                    if hasattr(env['pos.config'], 'module_pos_restaurant'):
                        pos_vals['module_pos_restaurant'] = True
                    if invoice_journal:
                        pos_vals['invoice_journal_id'] = invoice_journal.id
                    if payment_methods:
                        pos_vals['payment_method_ids'] = [(6, 0, payment_methods)]

                    if pos_config:
                        pos_config.write(pos_vals)
                        print(f"  ✓ Updated POS Config: {pos_config.name}")
                    else:
                        pos_config = env['pos.config'].create(pos_vals)
                        print(f"  ✓ Created POS Config: {pos_config.name}")
        except Exception as e:
            print(f"  ⚠️ POS configuration warning: {e}")

        # 8. Configure Language (Español América Latina)
        try:
            lang_code = 'es_419'
            lang = env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)], limit=1)
            if lang:
                if not lang.active:
                    lang.write({'active': True})
                    print(f"  ✓ Activated language record {lang_code}")
                print("Installing/loading language translations: Spanish (Latin America) / Español (América Latina)...")
                try:
                    lang_installer = env['base.language.install'].create({
                        'lang_ids': [(6, 0, [lang.id])],
                        'overwrite': True,
                    })
                    lang_installer.lang_install()
                    print("  ✓ Language es_419 installed/loaded successfully.")
                except Exception as e:
                    print(f"  Warning: Could not install language es_419: {e}")
            else:
                print(f"  Warning: Language record {lang_code} not found in res.lang")
                    
            print("Setting default language es_419 for existing users and partners...")
            env['res.users'].search([]).write({'lang': lang_code})
            env['res.partner'].search([]).write({'lang': lang_code})
            print("  ✓ Updated existing users and partners language to es_419.")

            if 'ir.default' in env:
                env['ir.default'].set('res.partner', 'lang', lang_code)
                env['ir.default'].set('res.users', 'lang', lang_code)
                print("  ✓ Default language set for future contacts/users.")
        except Exception as e:
            print(f"  ⚠️ Language configuration warning: {e}")

        cr.commit()
        print("✓ System Settings configuration finished successfully!")

if __name__ == '__main__':
    import_settings()
