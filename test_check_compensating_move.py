move = env['account.move'].search([('ref', '=', 'Compensación Abono TPV 000033')])
print(f"Move: {move.name}")
for l in move.line_ids:
    print(f"  Line: {l.name} | Account: {l.account_id.code} {l.account_id.name} | Debit: {l.debit} | Credit: {l.credit} | Reconciled: {l.reconciled}")

partner = env['res.partner'].search([('name', 'ilike', 'Marcelo Pesallaccia')], limit=1)
print(f"\nPartner: {partner.name}")
print(f"Partner Receivable Account: {partner.property_account_receivable_id.code} {partner.property_account_receivable_id.name}")
print(f"Partner Debt (credit): {partner.credit}")
print(f"Partner Debt (debit): {partner.debit}")
print(f"Partner Outstanding Debt: {getattr(partner, 'outstanding_debt', 'N/A')}")

# find all open invoices/lines for partner
lines = env['account.move.line'].search([
    ('partner_id', '=', partner.id),
    ('account_id', '=', partner.property_account_receivable_id.id),
    ('reconciled', '=', False)
])
print(f"\nOpen lines for {partner.name}:")
for l in lines:
    print(f"  {l.move_id.name} | {l.name} | Debit: {l.debit} | Credit: {l.credit}")
