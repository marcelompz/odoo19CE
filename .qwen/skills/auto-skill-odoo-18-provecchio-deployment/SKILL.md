---
name: odoo-18-provecchio-deployment
description: Complete Odoo 18.0 CE deployment for Provecchio Di Mora with Docker, native modules, and standard naming conventions
source: auto-skill
extracted_at: '2026-07-03T12:59:33.724Z'
---

# Odoo 18.0 CE Deployment for Provecchio Di Mora

## Overview

Complete deployment procedure for Odoo 18.0 CE using Docker Compose with optimized configuration, health checks, and native Odoo 18 modules from Cybrosys.

## Repository Structure

**GitHub:** `github.com/marcelompz/odoo18CE`

```
/opt/odoo/odoo8082/
├── docker-compose.yml      # Optimized with health checks
├── Dockerfile              # Simplified with debugging tools
├── entrypoint.sh           # Improved with validation and logging
├── .env                    # Complete configuration variables
├── config/
│   └── odoo.conf          # Performance-optimized settings
└── addons/
    ├── auto_database_backup/    # Native Odoo 18 (Cybrosys)
    └── uom_spanish_import/      # product_multi_uom (Cybrosys)
```

## Standard Naming Convention

Follow the pattern from odoo8083 for consistency:

| Component | Pattern | Example |
|-----------|---------|---------|
| **Web Container** | `odoo_web_{port}` | `odoo_web_8082` |
| **DB Container** | `db_odoo_{port}` | `db_odoo_5434` |
| **Web Port** | `{port}` | `8082` |
| **DB Port** | `543{port_last_digit}` | `5434` |

## Configuration Files

### 1. docker-compose.yml

```yaml
services:
  web:
    container_name: odoo_web_8082
    build: .
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8082:8069"
      - "8072:8072"  # longpolling
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo:ro
      - ./addons:/mnt/extra-addons-customize:ro
    environment:
      - HOST=db_odoo_5434
      - USER=odoo
      - PASSWORD=crossdimora.159753
      - TZ=America/Asuncion
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8069/web/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  db:
    container_name: db_odoo_5434
    image: postgres:15
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=crossdimora.159753
      - TZ=America/Asuncion
      - POSTGRES_INITDB_ARGS=--encoding=UTF8 --lc-collate=C --lc-ctype=C
    ports:
      - "5434:5432"
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U odoo -d postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

volumes:
  odoo-db-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/odoo/odoo8082/db-data
      o: bind
  odoo-web-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/odoo/odoo8082/web-data
      o: bind
```

### 2. .env

```bash
# WEB (ODOO)
WEB_HOST=odoo_web_8082
WEB_IMAGE_NAME=odoo
WEB_IMAGE_TAG=18.0
WEB_PORT=8082
WEB_ADDONS_CUSTOMIZE=/opt/odoo/odoo8082/addons
WEB_VOLUMES=/opt/odoo/odoo8082/web-data

# DATABASE (POSTGRESQL)
DB_IMAGE=postgres
DB_TAG=15
DB_HOST=db_odoo_5434
DB_PORT=5434
DB_NAME=postgres
DB_USER=odoo
DB_PASSWD=crossdimora.159753
DB_VOLUMES=/opt/odoo/odoo8082/db-data

# PERFORMANCE
ODOO_WORKERS=2
ODOO_LIMIT_MEMORY_HARD=2684354560
ODOO_LIMIT_REQUEST=100

# SYSTEM
TZ=America/Asuncion
DEBIAN_FRONTEND=noninteractive
```

### 3. odoo.conf

```ini
[options]
admin_passwd = soportecrossdimora.159753

# Database
db_host = db_odoo_5434
db_port = 5432
db_user = odoo
db_password = crossdimora.159753
db_name = postgres
dbfilter = ^prod$|^dimora$
db_maxconn = 64
log_db = True
log_db_level = 30

# Addons
addons_path = /mnt/extra-addons-customize,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo

# Performance
workers = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 100
limit_time_cpu = 600
limit_time_real = 1200

# Longpolling
longpolling_port = 8072

# Logging
log_level = info

# Security
unaccent = True

# Cron
max_cron_threads = 1

# Web
http_enable = True
http_port = 8069
list_db = True
proxy_mode = True

# System
timezone = America/Asuncion
```

### 4. Dockerfile

```dockerfile
FROM odoo:18.0

USER root

LABEL MAINTAINER="Provecchio Di Mora <soporte@provecchio.com>"
LABEL DESCRIPTION="Odoo 18.0 CE - Optimized for Provecchio Di Mora"

# Install debugging tools
RUN apt-get update && apt-get install -y \
    curl \
    vim-tiny \
    jq \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy improved entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create directory for custom scripts
RUN mkdir -p /opt/odoo/custom-scripts && chown odoo:odoo /opt/odoo/custom-scripts

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8069/web/health || exit 1

USER odoo

# Ports
EXPOSE 8069 8072

ENTRYPOINT ["/entrypoint.sh"]
```

## Native Odoo 18 Modules

Replace migrated Odoo 19 modules with native Odoo 18 versions from `/home/marcelompz/Downloads/odoov18/`:

### 1. auto_database_backup

```bash
# Source: /home/marcelompz/Downloads/odoov18/auto_database_backup/
# Destination: /opt/odoo/odoo8082/addons/auto_database_backup/
cp -r /home/marcelompz/Downloads/odoov18/auto_database_backup \
      /opt/odoo/odoo8082/addons/
```

**Features:**
- Automated database backups
- S3, Dropbox, SFTP support
- Scheduled backups via cron
- Email notifications

### 2. product_multi_uom (uom_spanish_import)

```bash
# Source: /home/marcelompz/Downloads/odoov18/product_multi_uom-18.0.1.0.0/
# Destination: /opt/odoo/odoo8082/addons/uom_spanish_import/
cp -r /home/marcelompz/Downloads/odoov18/product_multi_uom-18.0.1.0.0 \
      /opt/odoo/odoo8082/addons/uom_spanish_import
```

**Features:**
- Multiple UoM support
- Spanish UoM names
- Import/export compatibility

### 3. excel_recipe_import (bom_structure_in_excel_odoo)

```bash
# Source: /home/marcelompz/Downloads/odoov18/bom_structure_in_excel_odoo-18.0.1.0.0/
# For testing, move to /tmp first
cp -r /home/marcelompz/Downloads/odoov18/bom_structure_in_excel_odoo-18.0.1.0.0 \
      /tmp/excel_recipe_import

# When ready to test, copy to addons
cp -r /tmp/excel_recipe_import /opt/odoo/odoo8082/addons/
docker restart odoo_web_8082
```

**Features:**
- Export BOM Structure & Cost Reports to Excel
- Manufacturing & Warehouse integration
- Depends: `stock`, `mrp`

## Deployment Steps

### 1. Prepare Directory Structure

```bash
# Create directories
mkdir -p /opt/odoo/odoo8082/{db-data,web-data,config,addons}

# Set permissions
chown -R 999:root /opt/odoo/odoo8082/{db-data,web-data}
```

### 2. Copy Configuration Files

```bash
cd /opt/odoo/odoo8082

# Copy docker-compose.yml, Dockerfile, entrypoint.sh, .env, odoo.conf
# (from repository or create manually)
```

### 3. Copy Native Modules

```bash
# From /home/marcelompz/Downloads/odoov18/
cp -r /home/marcelompz/Downloads/odoov18/auto_database_backup \
      /opt/odoo/odoo8082/addons/

cp -r /home/marcelompz/Downloads/odoov18/product_multi_uom-18.0.1.0.0 \
      /opt/odoo/odoo8082/addons/uom_spanish_import

# For excel_recipe_import, keep in /tmp for individual testing
cp -r /home/marcelompz/Downloads/odoov18/bom_structure_in_excel_odoo-18.0.1.0.0 \
      /tmp/excel_recipe_import
```

### 4. Start Containers

```bash
cd /opt/odoo/odoo8082

# Clean any existing containers
docker rm -f $(docker ps -aq) 2>/dev/null

# Remove old volumes if needed
docker compose down -v

# Start fresh
docker compose up -d --build

# Wait for health checks (60 seconds)
sleep 60

# Verify status
docker compose ps
```

### 5. Create Database

```bash
# Option A: Via UI
# 1. Access http://localhost:8082/web/database/manager
# 2. Click "Create Database"
# 3. Database name: prod
# 4. Master password: soportecrossdimora.159753
# 5. Email: soporte@crossnexion.com
# 6. Uncheck "Demo data"

# Option B: Via command line
docker exec db_odoo_5434 psql -U odoo -d postgres -c \
  "CREATE DATABASE prod OWNER odoo;"
```

### 6. Install Modules

```bash
# Access Odoo: http://localhost:8082
# Login to database
# Go to Apps
# Update Apps List
# Install:
#   - auto_database_backup
#   - uom_spanish_import (product_multi_uom)
#   - excel_recipe_import (when ready to test)
```

## Troubleshooting

### Issue: Container naming conflict

**Error:** `Conflict. The container name "/odoo_web_8082" is already in use`

**Solution:**
```bash
# Remove all containers
docker rm -f $(docker ps -aq)

# Remove volumes if needed
docker compose down -v

# Start fresh
docker compose up -d
```

### Issue: Module version error (19.0.x.x)

**Error:** `ValueError: Invalid version '19.0.2.0.0'. Modules should have a version in format x.y, x.y.z, 18.0.x.y or 18.0.x.y.z`

**Solution:**
```bash
# Remove migrated Odoo 19 modules
rm -rf /opt/odoo/odoo8082/addons/{module_name}

# Copy native Odoo 18 modules
cp -r /home/marcelompz/Downloads/odoov18/{module_name} \
      /opt/odoo/odoo8082/addons/

# Clear Odoo cache
docker exec odoo_web_8082 rm -rf /var/lib/odoo/addons/18.0/*

# Restart Odoo
docker restart odoo_web_8082
```

### Issue: Invalid manifest error

**Error:** `ValueError: Module {module}: invalid manifest`

**Causes:**
1. Module folder structure incorrect (nested folders)
2. Missing `__init__.py` files
3. Version format incorrect

**Solution:**
```bash
# Check module structure
ls -la /opt/odoo/odoo8082/addons/{module_name}/

# Ensure __manifest__.py exists and is valid
python3 -c "exec(open('/opt/odoo/odoo8082/addons/{module_name}/__manifest__.py').read())"

# If structure is nested, fix it
mv /opt/odoo/odoo8082/addons/{module_name}/{nested_folder}/* \
   /opt/odoo/odoo8082/addons/{module_name}/
rm -rf /opt/odoo/odoo8082/addons/{module_name}/{nested_folder}

# Clear cache and restart
docker exec odoo_web_8082 rm -rf /var/lib/odoo/addons/18.0/*
docker restart odoo_web_8082
```

### Issue: log_db_level error

**Error:** `ValueError: invalid literal for int() with base 10: 'WARNING'`

**Solution:**
```bash
# Edit odoo.conf
sed -i 's/log_db_level = WARNING/log_db_level = 30/' \
       /opt/odoo/odoo8082/config/odoo.conf

# Restart Odoo
docker restart odoo_web_8082
```

### Issue: Health check failing

**Check status:**
```bash
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082
```

**View logs:**
```bash
docker logs odoo_web_8082 --tail 100
```

**Common causes:**
- PostgreSQL not ready (wait for db health check)
- Module loading errors (check logs)
- Port conflicts (verify with `docker ps`)

## Git Workflow

### Commit and Push Changes

```bash
cd /opt/odoo/odoo8082

# Check status
git status

# Add all changes
git add -A

# Commit
git commit -m "feat: Description of changes

- Detail 1
- Detail 2
- Detail 3"

# Push
git push origin main
```

### Pull Updates on Server

```bash
ssh root@dimoraserverlocal

cd /opt/odoo8082

# Pull updates
git pull origin main

# Restart containers
docker compose down
docker compose up -d --build
```

## Access Information

| Service | URL | Credentials |
|---------|-----|-------------|
| **Odoo Web** | `http://localhost:8082` | Master: `soportecrossdimora.159753` |
| **PostgreSQL** | `localhost:5434` | User: `odoo`, Pass: `crossdimora.159753` |
| **Longpolling** | `localhost:8072` | - |

## Key Differences from Odoo 19

| Aspect | Odoo 19 | Odoo 18 |
|--------|---------|---------|
| **Module version format** | `19.0.x.y` | `18.0.x.y` |
| **log_level choices** | `INFO`, `DEBUG` | `info`, `debug` (lowercase) |
| **log_db_level** | String accepted | Must be numeric (30 for WARNING) |
| **Base version** | `19.0.1.3` | `18.0.1.3` |

## Best Practices

1. **Always use native Odoo 18 modules** - Don't migrate Odoo 19 modules
2. **Test modules individually** - Move problematic modules to `/tmp` for isolation
3. **Clear cache after module changes** - `rm -rf /var/lib/odoo/addons/18.0/*`
4. **Use health checks** - Wait for `healthy` status before accessing
5. **Follow naming convention** - `odoo_web_{port}`, `db_odoo_{port}`
6. **Commit frequently** - Push configuration changes to GitHub
7. **Document issues** - Save troubleshooting steps for future reference
