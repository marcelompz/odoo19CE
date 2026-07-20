---
name: odoo-19-provecchio-production-deployment
description: Complete Odoo 19 CE production deployment with Docker, including troubleshooting for filestore permissions, dbfilter configuration, Python dependencies, and database restoration
source: auto-skill
extracted_at: '2026-07-02T23:14:49.956Z'
---

# Odoo 19 CE Production Deployment - Complete Procedure

## Overview

Complete procedure for deploying Odoo 19 CE in production with Docker Compose, including common troubleshooting steps for filestore permissions, database filters, Python dependencies, and backup restoration.

## Prerequisites

- Docker and Docker Compose installed
- Server with root access
- Backup file (ZIP format from Odoo UI)
- Master password for database operations

## Step 1: Initial Setup

### Create .env file

```bash
cd /opt/odoo8083
cat << 'EOF' > .env
# Web Configuration
WEB_HOST=odoo_web_8083
WEB_PORT=8083
WEB_IMAGE_NAME=odoo
WEB_IMAGE_TAG=19.0
WEB_ADDONS_CUSTOMIZE=/opt/odoo8083/addons

# Database Configuration
DB_NAME=prod
DB_USER=odoo
DB_PASSWD=your_secure_password
DB_HOST=db5435
DB_IMAGE=postgres
DB_TAG=15
DB_PORT=5435

# Volumes
DB_VOLUMES=/opt/odoo8083/db-data
WEB_VOLUMES=/opt/odoo8083/web-data
EOF
```

### Configure odoo.conf

```bash
cat << 'EOF' > /opt/odoo8083/config/odoo.conf
[options]
addons_path = /mnt/extra-addons,/mnt/extra-addons-customize
admin_passwd = your_admin_password
db_host = db5435
db_port = 5435
db_user = odoo
db_password = your_secure_password
dbfilter = ^prod$|^staging$
data_dir = /var/lib/odoo
EOF
```

**Important:** Update `dbfilter` to include all database names you'll use (e.g., `^prod$|^staging$|^dimora$`)

### Install Python Dependencies

Update `requirements.txt`:

```txt
# Backup modules
dropbox>=12.0
boto3>=1.26
paramiko>=3.0
nextcloud-api-wrapper

# DNS and SSL
dnspython>=2.0

# Excel import/export
pandas>=2.0
openpyxl>=3.1
```

## Step 2: Deploy Containers

```bash
cd /opt/odoo8083
docker compose up -d
sleep 30  # Wait for containers to start
```

## Step 3: Restore Database from Backup

### Via Web UI (Recommended)

1. Access: `http://<server>:8083/web/database/manager`
2. Click **Restore**
3. Fill in:
   - **Database:** `prod`
   - **File:** `<backup_file>.zip`
   - **Master Password:** `<master_password>`
4. Click **Restore**
5. **Wait 15-20 minutes** (do NOT close browser)

### Common Issues & Solutions

#### Issue 1: "No module named 'nextcloud_client'"

**Cause:** `auto_database_backup` module tries to import unavailable package.

**Solution:** Comment out Nextcloud imports:

```bash
sed -i 's/^import nextcloud_client/#import nextcloud_client  # Temporarily disabled/' /opt/odoo8083/addons/auto_database_backup/models/db_backup_configure.py
sed -i 's/^from nextcloud import NextCloud/#from nextcloud import NextCloud  # Temporarily disabled/' /opt/odoo8083/addons/auto_database_backup/models/db_backup_configure.py
docker restart odoo_web_8083
```

#### Issue 2: "File exists" errors during restore

**Cause:** Previous failed restore left files in filestore.

**Solution:** Complete cleanup:

```bash
# Stop containers
docker compose down -v

# Remove all volumes
docker volume rm -f $(docker volume ls -q | grep odoo)

# Remove all databases
docker compose up -d
sleep 5
docker exec odoo_db_5435 psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS prod;"
docker compose down -v

# Restart and try restore again
docker compose up -d
```

#### Issue 3: "Permission denied" on filestore

**Cause:** File permissions mismatch between host and container.

**Solution:** Let Odoo UI restore handle permissions automatically. Do NOT manually copy filestore files.

#### Issue 4: Database not accessible after restore (dbfilter)

**Cause:** `dbfilter` in odoo.conf doesn't include the database name.

**Solution:**

```bash
sed -i 's/dbfilter = .*/dbfilter = ^prod$|^staging$|^dimora$/' /opt/odoo8083/config/odoo.conf
docker restart odoo_web_8083
```

## Step 4: Verify Restoration

```bash
# Check database exists
docker exec odoo_db_5435 psql -U odoo -d postgres -c "SELECT datname FROM pg_database WHERE datname='prod';"

# Check products count (should be ~566)
docker exec odoo_db_5435 psql -U odoo -d prod -c "SELECT COUNT(*) FROM product_product;"

# Check MRP BOMs (should be 54)
docker exec odoo_db_5435 psql -U odoo -d prod -c "SELECT COUNT(*) FROM mrp_bom;"

# Check POS BOMs (should be 134)
docker exec odoo_db_5435 psql -U odoo -d prod -c "SELECT COUNT(*) FROM pos_product_bom;"
```

## Step 5: Post-Restore Configuration

### Install Missing Python Packages

```bash
# Inside container
docker exec odoo_web_8083 pip3 install --break-system-packages paramiko dnspython nextcloud-api-wrapper
```

### Enable Auto Backup Module

1. Access Odoo: `http://<server>:8083`
2. Go to: **Apps → Technical → Modules**
3. Search: `auto_database_backup`
4. Click **Install**

### Configure Local DNS (Optional)

For local network access by domain:

```bash
# Install dnsmasq
apt-get install -y dnsmasq

# Configure
cat << 'EOF' > /etc/dnsmasq.conf
interface=enp5s0
bind-interfaces
no-resolv
address=/dimora.provecchio.com/192.168.69.240
server=8.8.8.8
EOF

systemctl restart dnsmasq
```

## Complete Cleanup Procedure

If you need to start completely fresh:

```bash
cd /opt/odoo8083

# Stop and remove everything
docker compose down -v --remove-orphans

# Remove all databases
docker compose up -d
sleep 5
docker exec odoo_db_5435 psql -U odoo -d postgres -c "SELECT 'DROP DATABASE ' || quote_ident(datname) || ';' FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1');" | docker exec -i odoo_db_5435 psql -U odoo -d postgres

# Stop again and remove volumes
docker compose down -v --remove-orphans

# Clean Docker
docker system prune -f
docker volume prune -f

# Verify clean state
docker ps -a  # Should be empty
docker volume ls  # Should show no odoo volumes
```

## Troubleshooting Checklist

- [ ] **dbfilter includes database name** → Check `/opt/odoo8083/config/odoo.conf`
- [ ] **Python dependencies installed** → Run `pip3 install` commands above
- [ ] **Filestore permissions** → Use UI restore, not manual copy
- [ ] **Nextcloud imports disabled** → Comment out in `db_backup_configure.py`
- [ ] **Database accessible** → Check `docker exec odoo_db_5435 psql -l`
- [ ] **Containers running** → Check `docker compose ps`
- [ ] **Logs show no errors** → Check `docker logs odoo_web_8083 --tail 100`

## Key Learnings

1. **Always use UI restore** - Handles permissions automatically
2. **dbfilter must include all DB names** - Update before restore
3. **Filestore must be empty** before restore - Clean completely
4. **Nextcloud client unavailable** - Comment out imports
5. **Python deps in requirements.txt** - Install via Dockerfile or manually
6. **Database naming convention** - Use `prod` for production standardization
