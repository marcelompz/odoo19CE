---
name: odoo-18-provecchio-automated-deployment
description: Complete automated Odoo 18 CE deployment for Provecchio Di Mora with Paraguayan accounting modules, OrderFlow integration, and automatic module installation
source: auto-skill
extracted_at: '2026-07-03T16:10:37.957Z'
---

# Odoo 18 CE Automated Deployment - Provecchio Di Mora

## Overview

Complete automated deployment procedure for Odoo 18 CE with:
- ✅ Paraguayan accounting modules (l10n_py v18)
- ✅ OrderFlow integration (XML-RPC API)
- ✅ Automatic module installation on database creation
- ✅ Health checks and monitoring
- ✅ Environment variables configuration (no odoo.conf)

## Directory Structure

```
/srv/odoo8082/                    # Production deployment directory
├── docker-compose.yml            # Docker Compose configuration
├── Dockerfile                    # Custom Odoo image with debugging tools
├── entrypoint.sh                 # Automated module installation script
├── modules.conf                  # List of modules to auto-install
├── .env                          # Environment variables (credentials)
├── .gitignore                    # Exclude sensitive files
├── addons/                       # Custom modules
└── /opt/odoo/l10n_py/v18/       # Paraguayan accounting modules (bind mount)
```

## Key Configuration Files

### 1. docker-compose.yml

```yaml
services:
  web:
    container_name: odoo_web_8082
    image: odoo:18.0
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons-customize:ro
      - /opt/odoo/l10n_py/v18:/mnt/extra-addons-l10n_py:ro  # Paraguayan modules
    environment:
      # Database
      - HOST=db
      - PORT=5432
      - USER=odoo
      - PASSWORD=crossdimora.159753
      
      # Odoo Configuration
      - ODOO_DB_FILTER=^prod$
      - ODOO_ADMIN_PASSWD=soportecrossdimora.159753
      
      # Performance
      - WORKERS=2
      - LIMIT_MEMORY_HARD=2684354560
      - LIMIT_MEMORY_SOFT=2147483648
      - LIMIT_REQUEST=100
      
      # Addons paths (CRITICAL: includes l10n_py)
      - ADDONS_PATH=/mnt/extra-addons-customize,/mnt/extra-addons-l10n_py,/usr/lib/python3/dist-packages/odoo/addons
      
      # System
      - TZ=America/Asuncion
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8069/web/database/selector"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s

  db:
    container_name: db_odoo_5434
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=crossdimora.159753
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U odoo -d postgres"]

volumes:
  odoo-db-data:
  odoo-web-data:
```

### 2. modules.conf

```conf
# ===========================================
# MÓDULOS A INSTALAR AUTOMÁTICAMENTE
# ===========================================

# Base
base
web

# Localización Paraguay
l10n_py

# Contabilidad
account
account_check_printing

# Inventario
stock

# Fabricación
mrp

# Punto de Venta
point_of_sale
pos_product_bom

# Ventas
sale_management

# Compras
purchase

# Contactos
contacts

# Empleados
hr

# Configuración regional
base_address_city
base_address_extended
base_geolocalize

# Reportes
account_reports

# Factura Electrónica Paraguay
electronic_invoice_cross
pos_einvoice_cross
de_send_email_cross
```

### 3. entrypoint.sh

Key features:
1. **Waits for PostgreSQL** (30 attempts, 2s intervals)
2. **Reads modules.conf** and parses module list
3. **Creates database 'prod'** automatically
4. **Sets Paraguay as country** (code: PY)
5. **Installs all modules** from modules.conf
6. **Starts Odoo** with proper configuration

```bash
#!/bin/bash
set -e

# 1. Wait for PostgreSQL
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if nc -z "$HOST" 5432 2>/dev/null; then
        break
    fi
    sleep 2
    attempt=$((attempt + 1))
done

# 2. Read modules from modules.conf
if [ -f /mnt/extra-addons-customize/modules.conf ]; then
    MODULES=$(grep -v '^#' modules.conf | grep -v '^$' | tr '\n' ',')
    
    # 3. Create database and install modules
    python3 << PYTHON
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

registry = Registry.new('prod', force_demo=False, force_load=True, update_module=True)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Set country to Paraguay
    country = env['res.country'].search([('code', '=', 'PY')], limit=1)
    if country:
        env['res.company'].search([], limit=1).write({'country_id': country.id})
    
    # Install modules
    for module_name in '${MODULES}'.split(','):
        module = env['ir.module.module'].search([('name', '=', module_name.strip())], limit=1)
        if module and module.state == 'uninstalled':
            module.button_immediate_install()
    
    cr.commit()
PYTHON
fi

# 4. Start Odoo
exec odoo "$@"
```

## Deployment Procedure

### Step 1: Prepare Server

```bash
# SSH to server
ssh root@dimoraserverlocal

# Create deployment directory
mkdir -p /srv/odoo8082
cd /srv/odoo8082
```

### Step 2: Clone Repository

```bash
git clone https://github.com/marcelompz/odoo18CE.git .
```

### Step 3: Verify l10n_py Path

```bash
# Verify Paraguayan modules exist
ls -la /opt/odoo/l10n_py/v18/

# Should contain:
# - l10n_py/
# - electronic_invoice_cross/
# - pos_einvoice_cross/
# - de_send_email_cross/
```

### Step 4: Deploy

```bash
# Start containers
docker compose up -d

# Wait for health checks (90 seconds)
sleep 90

# Verify status
docker compose ps
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082

# Should show: healthy
```

### Step 5: Verify Installation

```bash
# Check installed modules
docker exec odoo_web_8082 python3 << 'PYTHON'
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

registry = Registry.new('prod')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get Paraguayan modules
    py_modules = env['ir.module.module'].search([
        ('state', '=', 'installed'),
        ('name', 'in', ['l10n_py', 'electronic_invoice_cross', 'pos_einvoice_cross'])
    ])
    
    print(f"Paraguayan modules installed: {len(py_modules)}")
    for m in py_modules:
        print(f"  ✅ {m.name}")
    
    # Verify country
    company = env['res.company'].search([], limit=1)
    if company.country_id:
        print(f"Country: {company.country_id.name}")
PYTHON
```

## OrderFlow Integration

### API Credentials

```
URL: http://localhost:8082
Database: prod
Username: orderflow_api
Password: orderflow.159753
```

### XML-RPC Endpoints

```javascript
// Node.js example for OrderFlow
const xmlrpc = require('xmlrpc');

const config = {
  url: 'localhost:8082',
  db: 'prod',
  username: 'orderflow_api',
  password: 'orderflow.159753'
};

// Authenticate
const common = xmlrpc.createClient({ 
  host: config.url, 
  port: 8082, 
  path: '/xmlrpc/2/common' 
});

common.methodCall('authenticate', [
  config.db, 
  config.username, 
  config.password, 
  {}
], (err, uid) => {
  if (uid) {
    console.log('✅ Authenticated:', uid);
    
    // Create/Update contact
    const models = xmlrpc.createClient({ 
      host: config.url, 
      port: 8082, 
      path: '/xmlrpc/2/object' 
    });
    
    models.methodCall('execute_kw', [
      config.db, uid, config.password,
      'res.partner', 'create', [{
        name: 'Juan Pérez',
        email: 'juan@sorteo.com',
        phone: '+595981234567',
      }]
    ], (err, contactId) => {
      console.log('✅ Contact created:', contactId);
    });
  }
});
```

### Available Operations

| Operation | Model | Method | Purpose |
|-----------|-------|--------|---------|
| Create Contact | `res.partner` | `create` | New customer from sorteo |
| Update Contact | `res.partner` | `write` | Update email/phone |
| Search Contact | `res.partner` | `search_read` | Find existing customer |
| Create Sale | `sale.order` | `create` | Create quotation |
| Check Stock | `stock.quant` | `search_read` | Verify inventory |

## Troubleshooting

### Issue: Permission Denied on Sessions

**Symptom:** `PermissionError: [Errno 13] Permission denied: '/var/lib/odoo/sessions'`

**Solution:** Use Docker named volumes instead of bind mounts:

```yaml
volumes:
  - odoo-web-data:/var/lib/odoo  # Named volume (correct)
  # NOT: - ./web-data:/var/lib/odoo  # Bind mount (causes permission issues)
```

### Issue: l10n_py Modules Not Found

**Symptom:** Modules don't appear in Apps list

**Solution:** Verify ADDONS_PATH includes l10n_py:

```yaml
environment:
  - ADDONS_PATH=/mnt/extra-addons-customize,/mnt/extra-addons-l10n_py,/usr/lib/python3/dist-packages/odoo/addons
```

Verify volume mount:

```yaml
volumes:
  - /opt/odoo/l10n_py/v18:/mnt/extra-addons-l10n_py:ro  # Correct path
```

### Issue: Database Connection Failed

**Symptom:** `FATAL: password authentication failed for user "odoo"`

**Solution:** Ensure passwords match in both services:

```yaml
# Web service
environment:
  - PASSWORD=crossdimora.159753

# DB service
environment:
  - POSTGRES_PASSWORD=crossdimora.159753
```

Recreate with clean volumes:

```bash
docker compose down -v
docker compose up -d
```

## Health Check Verification

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082

# Should return: healthy

# Check logs
docker logs odoo_web_8082 --tail 50 | grep -E '(SUCCESS|ERROR|Modules loaded)'

# Test web access
curl -sI http://localhost:8082 | head -3

# Should return: HTTP/1.1 303 SEE OTHER (redirect to login)
```

## Production Checklist

- [ ] `/srv/odoo8082/` directory created
- [ ] Repository cloned from GitHub
- [ ] `/opt/odoo/l10n_py/v18/` exists with modules
- [ ] `docker-compose.yml` has correct l10n_py path
- [ ] `modules.conf` includes all required modules
- [ ] `.env` file created with secure passwords
- [ ] Containers started: `docker compose up -d`
- [ ] Health check: `healthy` (wait 90s)
- [ ] Database `prod` created automatically
- [ ] Paraguayan modules installed
- [ ] OrderFlow API user created
- [ ] XML-RPC connection tested from OrderFlow

## Key Success Indicators

1. **Container Status:** `healthy`
2. **Database:** `prod` exists in PostgreSQL
3. **Modules:** `l10n_py`, `electronic_invoice_cross` installed
4. **Country:** Paraguay configured
5. **OrderFlow:** XML-RPC authentication successful
6. **Logs:** No permission errors, no connection failures
