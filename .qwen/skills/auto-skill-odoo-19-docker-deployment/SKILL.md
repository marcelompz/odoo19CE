---
name: odoo-19-docker-deployment
description: Deploy Odoo 19 CE with Docker Compose including container naming, port configuration, database setup, and troubleshooting
source: auto-skill
extracted_at: '2026-07-02T20:55:25.148Z'
---

# Odoo 19 CE Docker Deployment Guide

## Container Naming Convention

Use **port-based sequential naming** for clarity when hosting multiple Odoo instances:

| Component | Pattern | Example (port 8083) | Example (port 8084) |
|-----------|---------|---------------------|---------------------|
| Web service | `web{port}` | `web8083` | `web8084` |
| DB service | `db{port}` | `db5435` | `db5436` |
| Web container | `odoo_web_{port}` | `odoo_web_8083` | `odoo_web_8084` |
| DB container | `odoo_db_{port}` | `odoo_db_5435` | `odoo_db_5436` |

## Port Configuration

**Critical:** Docker uses **internal ports** for container-to-container communication and **external ports** for host access.

| Service | Internal Port | External Port | Usage |
|---------|---------------|---------------|-------|
| Odoo | `8069` | `{port}` (e.g., 8083) | Web interface |
| PostgreSQL | `5432` | `{port}` (e.g., 5435) | Database |

### docker-compose.yml Example

```yaml
services:
  web8083:
    container_name: odoo_web_8083
    image: odoo:19.0
    ports:
      - "8083:8069"  # External:Internal
    environment:
      - HOST=db5435      # Service name (NOT container name)
      - PORT=5432        # INTERNAL PostgreSQL port
      - USER=odoo
      - PASSWORD=your_password
  
  db5435:
    container_name: odoo_db_5435
    image: postgres:15
    ports:
      - "5435:5432"  # External:Internal
    environment:
      - POSTGRES_DB=dimora
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=your_password
```

## odoo.conf Configuration

**Critical:** Use **internal ports** and **service names** (not container names):

```ini
[options]
db_host = db5435      # ← Service name from docker-compose
db_port = 5432        # ← INTERNAL PostgreSQL port (NOT 5435!)
db_user = odoo
db_password = your_password
dbfilter = ^dimora$
admin_passwd = your_admin_password
addons_path = /mnt/extra-addons,/mnt/extra-addons-customize
```

### Common Mistakes

| ❌ Wrong | ✅ Correct | Why |
|----------|-----------|-----|
| `db_host = odoo_db_5435` | `db_host = db5435` | Must match service name in docker-compose |
| `db_port = 5435` | `db_port = 5432` | Must use INTERNAL port |
| `HOST=${DB_HOST}` | `HOST=db5435` | Hardcode or ensure .env matches service name |

## .env File

```bash
# Web Configuration
WEB_HOST=dimora
WEB_PORT=8083
WEB_IMAGE_NAME=odoo
WEB_IMAGE_TAG=19.0
WEB_ADDONS_CUSTOMIZE=/opt/odoo8083/addons

# Database Configuration
DB_NAME=dimora
DB_USER=odoo
DB_PASSWD=your_password
DB_HOST=db5435        # ← Must match service name
DB_PORT=5435          # ← External port (for host access)
DB_IMAGE=postgres
DB_TAG=15

# Volumes
DB_VOLUMES=/opt/odoo8083/db-data
WEB_VOLUMES=/opt/odoo8083/web-data
```

## Database Restoration

### From SQL Dump

```bash
# 1. Create database (if not exists)
docker exec odoo_db_5435 psql -U odoo -c "CREATE DATABASE dimora;"

# 2. Restore dump
docker exec -i odoo_db_5435 psql -U odoo -d dimora < /path/to/dump.sql

# 3. Copy filestore
cp -r /path/to/filestore/* /opt/odoo8083/web-data/filestore/

# 4. Restart Odoo
docker compose restart odoo_web_8083
```

### Verify Restoration

```bash
# Check product count
docker exec odoo_db_5435 psql -U odoo -d dimora -c "SELECT COUNT(*) FROM product_product;"

# Check MRP BoM count
docker exec odoo_db_5435 psql -U odoo -d dimora -c "SELECT COUNT(*) FROM mrp_bom;"

# Check POS BoM count
docker exec odoo_db_5435 psql -U odoo -d dimora -c "SELECT COUNT(*) FROM pos_product_bom;"
```

## Troubleshooting

### Connection Refused Errors

**Error:** `connection to server at "db5435" (10.201.0.2), port 5435 failed: Connection refused`

**Causes:**
1. Using external port (5435) instead of internal port (5432) in odoo.conf
2. DB_HOST doesn't match service name in docker-compose
3. PostgreSQL container not running

**Solution:**
```bash
# Check odoo.conf
grep -E 'db_host|db_port' /opt/odoo8083/config/odoo.conf
# Should show: db_host = db5435, db_port = 5432

# Check containers are running
docker ps | grep -E '(odoo_web|odoo_db)'

# Test connection from Odoo container
docker exec odoo_web_8083 python3 -c "import psycopg2; psycopg2.connect(host='db5435', port=5432, database='dimora', user='odoo', password='...')"
```

### Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'boto3'`

**Solution:**
```bash
docker exec odoo_web_8083 pip install --break-system-packages boto3
docker restart odoo_web_8083
```

### Database Not Appearing in Selector

**Causes:**
1. Database doesn't exist
2. dbfilter doesn't match database name
3. User doesn't have permissions

**Solution:**
```bash
# Check database exists
docker exec odoo_db_5435 psql -U odoo -c "\l" | grep dimora

# Check dbfilter in odoo.conf
grep dbfilter /opt/odoo8083/config/odoo.conf

# Grant permissions
docker exec odoo_db_5435 psql -U odoo -d dimora -c "GRANT ALL ON DATABASE dimora TO odoo;"
```

### Container Network Issues

**Check network:**
```bash
docker network inspect odoo8083_default | grep -E '(Name|Subnet|Container)'
```

**Test connectivity:**
```bash
# From Odoo container to DB
docker exec odoo_web_8083 ping db5435
docker exec odoo_web_8083 psql -h db5435 -p 5432 -U odoo -d dimora -c "SELECT version();"
```

## Deployment Checklist

- [ ] docker-compose.yml uses correct service names (web8083, db5435)
- [ ] Container names follow convention (odoo_web_8083, odoo_db_5435)
- [ ] Ports mapped correctly (external:internal)
- [ ] odoo.conf uses service name for db_host (NOT container name)
- [ ] odoo.conf uses INTERNAL port for db_port (5432, NOT 5435)
- [ ] .env DB_HOST matches docker-compose service name
- [ ] Database created and restored
- [ ] Filestore copied to web-data volume
- [ ] Required Python packages installed (boto3, etc.)
- [ ] Odoo logs show "Registry loaded" without errors
- [ ] Web interface accessible at http://server:port

## Quick Start Commands

```bash
# Full deployment
cd /opt/odoo8083
docker compose down -v
rm -rf db-data/* web-data/*
docker compose up -d
sleep 30

# Restore database
docker exec -i odoo_db_5435 psql -U odoo -d dimora < dump.sql
cp -r filestore/* /opt/odoo8083/web-data/filestore/
docker restart odoo_web_8083

# Check status
docker compose ps
docker logs odoo_web_8083 | grep -E '(Registry loaded|ERROR)' | tail -5
```
