import logging
import json
import urllib.request
import urllib.error
import threading

_logger = logging.getLogger(__name__)

def send_webhook_async(env, event_type, payload):
    """
    Envía una notificación webhook a OrderFlow sin bloquear la transacción de Odoo.
    """
    ICP = env['ir.config_parameter'].sudo()
    enabled = ICP.get_param('orderflow.enabled', 'False') == 'True'
    if not enabled:
        return

    webhook_url = ICP.get_param('orderflow.webhook_url', '').strip()
    api_key = ICP.get_param('orderflow.api_key', '').strip()

    if not webhook_url:
        _logger.debug("[OrderFlow Connector] Webhook URL no configurada.")
        return

    full_payload = {
        'event': event_type,
        'data': payload,
    }

    def _post():
        try:
            req_data = json.dumps(full_payload).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=req_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Odoo-OrderFlow-Connector/19.0',
                    'x-api-key': api_key,
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                _logger.info("[OrderFlow Connector] Webhook %s enviado exitosamente. Status: %s", event_type, resp.status)
        except Exception as e:
            _logger.warning("[OrderFlow Connector] Error al enviar Webhook %s: %s", event_type, str(e))

    thread = threading.Thread(target=_post)
    thread.daemon = True
    thread.start()
