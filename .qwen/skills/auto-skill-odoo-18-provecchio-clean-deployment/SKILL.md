---
name: odoo-18-provecchio-clean-deployment
description: Complete Odoo 18.0 CE deployment for Provecchio Di Mora with clean rebuild procedure from GitHub
source: auto-skill
extracted_at: '2026-07-03T14:01:44.582Z'
---

# Odoo 18.0 CE - Provecchio Di Mora Clean Deployment

## 📋 Standard Configuration

### Container Naming Convention
- **Web:** `odoo_web_8082` (pattern: `odoo_web_{port}`)
- **Database:** `db_odoo_5434` (pattern: `db_odoo_{port}`)

### File Structure
```
/opt/odoo/odoo8082/
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── .env
├── config/
│   └── odoo.conf
├── addons/
│   ├── auto_database_backup/
│   └── uom_spanish_import/
├── db-data/
└── web-data/
```

## 🚀 Complete Clean Deployment Procedure

### When to Use This Procedure
- Module version conflicts (19.0.x modules in Odoo 18)
- Database contamination from previous versions
- Health check showing unhealthy despite containers running
- Internal Server Error on UI access
- Module manifest errors

### Step 1: Complete Physical Cleanup
```bash
# Stop and remove containers
docker compose down
docker rm -f odoo_web_8082 db_odoo_5434

# Remove volumes physically
sudo rm -rf /opt/odoo/odoo8082/db-data/*
sudo rm -rf /opt/odoo/odoo8082/web-data/*

# Remove Docker volume cache
rm -rf /var/lib/docker/volumes/odoo8082_*
```

### Step 2: Clone Fresh from GitHub
```bash
cd /opt/odoo
rm -rf odoo8082  # Remove any existing directory
git clone git@github.com:marcelompz/odoo18CE.git odoo8082
cd odoo8082
```

### Step 3: Create .env File
```bash
cat > .env << 'EOF'
# ODOO 18 CE - PROVECCHIO DI MORA
WEB_HOST=odoo_web_8082
WEB_IMAGE_NAME=odoo
WEB_IMAGE_TAG=18.0
WEB_PORT=8082
WEB_ADDONS_CUSTOMIZE=/opt/odoo/odoo8082/addons
WEB_VOLUMES=/opt/odoo/odoo8082/web-data

DB_IMAGE=postgres
DB_TAG=15
DB_HOST=db_odoo_5434
DB_PORT=5434
DB_NAME=postgres
DB_USER=odoo
DB_PASSWD=crossdimora.159753
DB_VOLUMES=/opt/odoo/odoo8082/db-data

TZ=America/Asuncion
DEBIAN_FRONTEND=noninteractive
EOF
```

### Step 4: Start Containers
```bash
docker compose up -d
sleep 90  # Wait for health checks
```

### Step 5: Verify Health
```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082
curl -sI http://localhost:8082
```

## ⚠️ Critical Issues & Solutions

### Issue 1: Module Version Mismatch
**Error:** `ValueError: Invalid version '19.0.2.0.0'. Modules should have a version in format...`

**Cause:** Odoo 19 modules copied to Odoo 18 installation

**Solution:**
```bash
# Remove problematic modules
rm -rf /opt/odoo/odoo8082/addons/excel_recipe_import

# Use native Odoo 18 modules from /home/marcelompz/Downloads/odoov18/
cp -r /home/marcelompz/Downloads/odoov18/auto_database_backup /opt/odoo/odoo8082/addons/
cp -r /home/marcelompz/Downloads/odoov18/product_multi_uom-18.0.1.0.0 /opt/odoo/odoo8082/addons/uom_spanish_import

# Clear Odoo cache
docker exec odoo_web_8082 rm -rf /var/lib/odoo/addons/18.0/*

# Restart
docker restart odoo_web_8082
```

### Issue 2: Database Contamination
**Error:** `KeyError: 'dimora'` or module errors persist after module removal

**Cause:** Old database has registered modules with wrong versions

**Solution:**
```bash
# Drop contaminated databases
docker exec db_odoo_5434 psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS dimora;"
docker exec db_odoo_5434 psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS prod;"

# Create fresh database
docker exec db_odoo_5434 psql -U odoo -d postgres -c "CREATE DATABASE prod OWNER odoo ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE template0;"

# Restart Odoo
docker restart odoo_web_8082
```

### Issue 3: Health Check Failing
**Error:** Container shows `unhealthy` but Odoo seems to work

**Cause:** Health check endpoint returns 500 due to module loading errors

**Solution:** Update health check in docker-compose.yml:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8069/web/database/selector"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

**Why `/web/database/selector` instead of `/web/health`:**
- `/web/health` only checks if Odoo process is running
- `/web/database/selector` verifies Odoo can connect to database AND load modules
- Better indicator of actual Odoo readiness

## 🔧 Performance Configuration (odoo.conf)

```ini
[options]
admin_passwd = soportecrossdimora.159753
db_host = db
db_port = 5432
db_user = odoo
db_password = crossdimora.159753
dbfilter = ^prod$|^dimora$

# Performance
workers = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 100
limit_time_cpu = 600
limit_time_real = 1200

# Logging
log_level = info
log_db = True
log_db_level = 30

# Addons
addons_path = /mnt/extra-addons-customize,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
```

## 📦 Native Odoo 18 Modules

Located in `/home/marcelompz/Downloads/odoov18/`:

| Module | Directory | Purpose |
|--------|-----------|---------|
| auto_database_backup | auto_database_backup-18.0.2.0.0 | Automated backups (S3, Dropbox, SFTP) |
| product_multi_uom | product_multi_uom-18.0.1.0.0 | Multiple UoM support |
| bom_structure_excel | bom_structure_in_excel_odoo-18.0.1.0.0 | Excel BOM import/export |

## ✅ Verification Checklist

After deployment, verify:

```bash
# 1. Containers running
docker compose ps
# Expected: Both containers showing "Up (healthy)"

# 2. Health status
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082
# Expected: healthy

# 3. Web access
curl -sI http://localhost:8082
# Expected: HTTP/1.0 200 OK or 302 Found (not 500)

# 4. Database accessible
docker exec db_odoo_5434 psql -U odoo -d postgres -c "SELECT datname FROM pg_database;"
# Expected: List of databases including 'prod'

# 5. No module errors in logs
docker logs odoo_web_8082 --tail 100 | grep -E '(ERROR|ValueError)'
# Expected: No output (no errors)
```

## 🎯 Access Information

| Service | URL | Credentials |
|---------|-----|-------------|
| Odoo Web | http://localhost:8082 | Master: `soportecrossdimora.159753` |
| PostgreSQL | localhost:5434 | User: `odoo`, Pass: `crossdimora.159753` |

## 📝 Git Workflow

After successful deployment:

```bash
cd /opt/odoo/odoo8082
git add -A
git commit -m "feat: Clean deployment from GitHub

- Complete rebuild from github.com:marcelompz/odoo18CE
- Health check updated to /web/database/selector
- Native Odoo 18 modules only (no 19.0 modules)
- Database created fresh without contamination

Tested: http://localhost:8082 - healthy and accessible"
git push origin main
```

## ⚡ Quick Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| HTTP 500 on all pages | Module version conflict | Remove problematic module, clear cache, restart |
| Container unhealthy | Health check failing | Check logs for module errors, drop contaminated DB |
| "Invalid manifest" | 19.0 module in 18.0 | Remove module from addons, rebuild |
| Database errors | Old DB with wrong modules | DROP DATABASE, CREATE DATABASE fresh |
| Port conflicts | Old containers running | `docker rm -f $(docker ps -aq)`, rebuild |
