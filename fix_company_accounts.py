import sys

company = env.company

print(f"Current Company: {company.name} (ID: {company.id})")

accounts = env['account.account'].search([('account_type', '=', 'asset_receivable')])
print(f"Total receivable accounts in DB: {len(accounts)}")
for acc in accounts[:5]:
    # Try to see companies
    if hasattr(acc, 'company_ids'):
        print(f" - {acc.name} | company_ids: {[c.name for c in acc.company_ids]}")
    elif hasattr(acc, 'company_id'):
        print(f" - {acc.name} | company_id: {acc.company_id.name}")
