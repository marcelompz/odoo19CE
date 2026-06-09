import sys

# Find the Settle Due product
product = env.ref('pos_customer_balance_ce.product_product_settle_due', raise_if_not_found=False)

# Find a valid income account
try:
    income_account = env['account.account'].search([('account_type', '=', 'income'), ('company_ids', 'in', env.company.id)], limit=1)
except Exception:
    income_account = env['account.account'].search([('account_type', '=', 'income')], limit=1)

if product and income_account:
    product.property_account_income_id = income_account
    print(f"✅ Cuenta de ingresos '{income_account.name}' asignada al producto '{product.name}'")
else:
    print("❌ No se encontró el producto o una cuenta de ingresos válida en el sistema.")

# Also try to fix RECETA_EJEMPLO if it exists
receta = env['product.product'].search([('name', '=', 'RECETA_EJEMPLO')], limit=1)
if receta and income_account and not receta.property_account_income_id:
    receta.property_account_income_id = income_account
    print(f"✅ Cuenta de ingresos '{income_account.name}' asignada al producto '{receta.name}'")

env.cr.commit()
print("Operación completada.")
