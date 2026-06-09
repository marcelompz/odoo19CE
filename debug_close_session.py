import sys
import traceback

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if not session:
    print("No open sessions found.")
    sys.exit(0)

print(f"Trying to close session: {session.name} (ID: {session.id})")

try:
    # Intenta validar y cerrar la caja programaticamente para atrapar el error
    # En Odoo 19:
    session.action_pos_session_closing_control()
    print("Session closed successfully!")
except Exception as e:
    print("\n=== ERROR AL CERRAR LA SESION ===")
    print(str(e))
    print("\n=== TRACEBACK ===")
    traceback.print_exc()
    
    # Intenta hacer un log mas profundo
    if hasattr(e, 'args'):
        print("\nArgs:", e.args)

