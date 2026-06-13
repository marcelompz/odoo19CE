partner = env['res.partner'].search([('name', 'ilike', 'CLI0014')], limit=1)
if partner:
    print(f"Partner {partner.name} found. Debt: {partner.outstanding_debt}")
    orders = env['pos.order'].search([('partner_id', '=', partner.id)], order='id desc', limit=3)
    for o in orders:
        print(f"\nOrder: {o.name} - State: {o.state} - Session: {o.session_id.name}")
        for l in o.lines:
            print(f"  Line: {l.product_id.name} | qty: {l.qty} | subtotal: {l.price_subtotal_incl}")
        # check moves
        domain = [('ref', 'ilike', f"%{o.name}%")]
        moves = env['account.move'].search(domain)
        if moves:
            for m in moves:
                print(f"  Compensating move: {m.name} - State: {m.state} - Ref: {m.ref}")
        else:
            print(f"  No compensating move found containing {o.name}")
else:
    print("Partner not found")
