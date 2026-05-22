FROM odoo:19.0

LABEL MAINTAINER = "Crossnexion EAS <contacto@crossnexion.com>"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages -r /tmp/requirements.txt
