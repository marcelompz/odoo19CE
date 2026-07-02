---
name: provecchio-odoo-deployment
description: Deploy Odoo 19 CE for Provecchio Di Mora with Docker Compose, nginx, and recipe imports
source: auto-skill
extracted_at: '2026-07-02T20:25:30.061Z'
---

# Provecchio Di Mora Odoo 19 CE Deployment

## Infrastructure Overview

**Server:** `dimoraserverlocal` (Hetzner Cloud, IP: 38.52.135.227)
**Domain:** `dimora.provecchio.com`
**Port:** `8083`
**Path:** `/opt/odoo8083`

## Container Naming Convention

Use consistent naming for easy management:

| Service | Container Name | Port | Purpose |
|---------|---------------|------|---------|
| `web8083` | `odoo_web_8083` | 8083:8069 | Odoo 19.0 web |
| `db5435` | `odoo_db_5435` | 5435:5432 | PostgreSQL 15 |

## docker-compose.yml Structure

```yaml
networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 10.201.0.0/16

services:
  web8083:
    container_name: odoo_web_8083
    image: odoo:19.0
    depends_on:
      - db5435
    ports:
      - "8083:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - /mnt/addons:/mnt/extra-addons
      - ./addons:/mnt/extra-addons-customize
    environment:
      - HOST=db5435
      - USER=odoo
      - PASSWORD=<db_password>
      - TZ=America/Asuncion

  db5435:
    container_name: odoo_db_5435
    image: postgres:15
    environment:
      - POSTGRES_DB=dimora
      - POSTGRES_PASSWORD=<db_password>
      - POSTGRES_USER=odoo
      - PGDATA=/var/lib/postgresql/data/pgdata
    ports:
      - "5435:5432"
    volumes:
      - odoo-db-data:/var/lib/postgresql/data/pgdata

volumes:
  odoo-db-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/odoo8083/db-data
      o: bind
  odoo-web-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/odoo8083/web-data
      o: bind
```

## Deployment Steps

### 1. Create Directory Structure

```bash
ssh root@dimoraserverlocal

mkdir -p /opt/odoo8083/{db-data,web-data,config,addons}
chmod -R 755 /opt/odoo8083
```

### 2. Clone Repository

```bash
cd /opt/odoo8083
git clone git@github.com:marcelompz/odoo19CE.git .
# Or copy existing code
```

### 3. Create .env File

**Never commit .env to Git!** Create manually on server:

```bash
cat << 'EOF' > /opt/odoo8083/.env
# Web Configuration
WEB_HOST=dimora
WEB_PORT=8083
WEB_IMAGE_NAME=odoo
WEB_IMAGE_TAG=19.0
WEB_ADDONS_CUSTOMIZE=/opt/odoo8083/addons

# Database Configuration
DB_NAME=dimora
DB_USER=odoo
DB_PASSWD=<secure_password>
DB_HOST=db5435
DB_IMAGE=postgres
DB_TAG=15
DB_PORT=5435

# Volumes
DB_VOLUMES=/opt/odoo8083/db-data
WEB_VOLUMES=/opt/odoo8083/web-data
EOF
```

### 4. Configure odoo.conf

```bash
# /opt/odoo8083/config/odoo.conf
[options]
addons_path = /mnt/extra-addons,/mnt/extra-addons-customize
admin_passwd = <admin_password>
db_host = db5435
db_port = 5435
db_name = dimora
db_user = odoo
db_password = <db_password>
list_db = True
proxy_mode = True
```

### 5. Start Containers

```bash
cd /opt/odoo8083
docker compose down -v --remove-orphans  # Clean up any old containers
docker compose up -d
sleep 30
docker compose ps
```

### 6. Restore Database Backup

**Option A: Command Line**

```bash
# Create database
docker exec odoo_db_5435 psql -U odoo -c 'CREATE DATABASE dimora;'

# Restore dump
docker exec -i odoo_db_5435 psql -U odoo -d dimora < /opt/odoo8083/dump.sql

# Copy filestore
mkdir -p /opt/odoo8083/web-data/filestore
cp -r /opt/odoo8083/filestore/* /opt/odoo8083/web-data/filestore/

# Restart Odoo
docker compose restart odoo_web_8083
```

**Option B: Odoo UI**

1. Go to `http://<server-ip>:8083`
2. Click "Create Database"
3. Fill in database name `dimora`, email, password
4. After creation, go to Settings → Technical → Database → Restore

### 7. Configure Nginx Reverse Proxy

```bash
cat << 'EOF' > /etc/nginx/sites-available/dimora.provecchio.com
server {
    listen 80;
    server_name dimora.provecchio.com;

    access_log /var/log/nginx/dimora_access.log;
    error_log /var/log/nginx/dimora_error.log;

    client_max_body_size 200M;

    location / {
        proxy_pass http://localhost:8083;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/dimora.provecchio.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 8. Configure Let's Encrypt SSL

**Prerequisites:**
- DNS A record must point to server IP
- Port 80 must be accessible from internet
- Nginx must be running

```bash
apt-get update && apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d dimora.provecchio.com \
  --non-interactive \
  --agree-tos \
  --email soporte@crossnexion.com \
  --redirect
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs odoo_web_8083

# Check if ports are in use
netstat -tlnp | grep 8083
netstat -tlnp | grep 5435

# Clean up and restart
docker compose down -v --remove-orphans
docker rm -f odoo_web_8083 odoo_db_5435
docker compose up -d
```

### Database Connection Failed

1. Verify `.env` has correct `DB_HOST=db5435` (matches service name)
2. Verify `odoo.conf` has `db_host = db5435` and `db_port = 5435`
3. Check database exists: `docker exec odoo_db_5435 psql -U odoo -c '\l'`
4. Restart containers: `docker compose restart`

### Nginx SSL Certificate Failed

- Verify DNS: `dig dimora.provecchio.com +short` → should return server IP
- Verify port 80 is open: `ufw allow 80/tcp`
- Check nginx is running: `systemctl status nginx`
- View certbot logs: `cat /var/log/letsencrypt/letsencrypt.log`

## Recipe Import Module

The `excel_recipe_import` module was enhanced for this deployment:

**Features:**
- Import type selector: Both, MRP only, POS only
- Pre-import validation (dependencies, file structure)
- Odoo 19 CE compatibility fixes

**Imported Data:**
- 54 MRP BoM recipes (subproductos)
- 134 POS BoM recipes (comidas)
- Total: 188 recipes

**Usage:**
1. Go to Manufacturing → Importador Excel (or POS → Importador Excel)
2. Select import type: "Solo Recetas MRP" or "Solo Recetas POS"
3. Click "Validar Archivo" first
4. Upload Excel file with correct sheet names:
   - `MRP BoM (Subproducts)` for manufacturing
   - `POS BoM (Comidas)` for point of sale
5. Click "Importar"

## Verified Deployment Data (2026-07-02)

After successful restoration:

```sql
SELECT COUNT(*) FROM product_product;        -- Returns: 566
SELECT COUNT(*) FROM mrp_bom;                -- Returns: 54
SELECT COUNT(*) FROM pos_product_bom;        -- Returns: 134
SELECT COUNT(*) FROM uom_uom;                -- Returns: ~20
```

**Total recipes:** 188 (54 MRP + 134 POS)

## Maintenance Commands

```bash
# View logs
docker compose logs -f odoo_web_8083
docker compose logs -f odoo_db_5435

# Restart services
docker compose restart odoo_web_8083
docker compose restart odoo_db_5435

# Backup database
docker exec odoo_db_5435 pg_dump -U odoo dimora > backup_$(date +%Y-%m-%d).sql

# Backup filestore
tar -czf filestore_backup_$(date +%Y-%m-%d).tar.gz /opt/odoo8083/web-data/filestore/

# Update repository
cd /opt/odoo8083
git pull origin main
docker compose restart odoo_web_8083

# Verify deployment
docker exec odoo_db_5435 psql -U odoo -d dimora -c "SELECT 'Products: ' || COUNT(*) FROM product_product UNION ALL SELECT 'MRP: ' || COUNT(*) FROM mrp_bom UNION ALL SELECT 'POS: ' || COUNT(*) FROM pos_product_bom;"
```
