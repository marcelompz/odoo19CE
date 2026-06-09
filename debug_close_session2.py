import sys
import traceback

session = env['pos.session'].search([('state', '!=', 'closed')], limit=1)
if not session:
    print("No open sessions found.")
    sys.exit(0)

print(f"Trying to close session: {session.name} (ID: {session.id})")

try:
    session.action_pos_session_closing_control()
    print("Session closed successfully!")
except Exception as e:
    print("\n=== TRACEBACK ===")
    traceback.print_exc()
