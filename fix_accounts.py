import sys

product = env.ref('pos_customer_balance_ce.product_product_settle_due', raise_if_not_found=False)
if not product:
    print("❌ No se encontró el producto PAGO_CUENTA via XML ID")
    product = env['product.product'].search([('default_code', '=', 'PAGO_CUENTA')], limit=1)

income_account = env['account.account'].search([('account_type', '=', 'income')], limit=1)
if not income_account:
    print("❌ No se encontró CUALQUIER cuenta de ingresos en la BD")

if product and income_account:
    product.property_account_income_id = income_account
    print(f"✅ Cuenta de ingresos '{income_account.name}' asignada al producto '{product.name}'")

receta = env['product.product'].search([('name', '=', 'RECETA_EJEMPLO')], limit=1)
if receta and income_account:
    receta.property_account_income_id = income_account
    print(f"✅ Cuenta de ingresos '{income_account.name}' asignada al producto '{receta.name}'")

env.cr.commit()
print("Operación completada.")
