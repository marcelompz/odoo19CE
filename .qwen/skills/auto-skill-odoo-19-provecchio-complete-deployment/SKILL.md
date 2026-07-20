---
name: odoo-19-provecchio-complete-deployment
description: Complete Odoo 19 CE deployment for Provecchio Di Mora with Docker, DNS, SSL, Python dependencies, and troubleshooting
source: auto-skill
extracted_at: '2026-07-02T22:19:43.562Z'
---

# Complete Odoo 19 CE Deployment for Provecchio Di Mora

This skill covers the complete deployment workflow for Odoo 19 CE on a local server with DNS, SSL, automated backups, and recipe imports.

## Architecture

- **Server:** Local server (192.168.69.240)
- **Domain:** dimora.provecchio.com (local DNS via dnsmasq)
- **Port:** 8083
- **Database:** PostgreSQL 15 on port 5435
- **Containers:** odoo_web_8083, odoo_db_5435

## Prerequisites

- Docker and Docker Compose installed
- Root access to server
- Cloudflare account for DNS management
- Domain pointing to server IP

## Step 1: Clone Repository and Configure

```bash
# Clone repository
git clone https://github.com/marcelompz/odoo19CE.git /opt/odoo8083
cd /opt/odoo8083

# Create .env from example
cp .env.example .env
nano .env  # Adjust ports, passwords as needed
```

### .env Configuration

```bash
# Web (Odoo)
WEB_HOST=odoo_web_8083
WEB_PORT=8083
WEB_IMAGE_NAME=odoo
WEB_IMAGE_TAG=19.0
WEB_ADDONS_CUSTOMIZE=/opt/odoo8083/addons

# Database
DB_NAME=dimora
DB_USER=odoo
DB_PASSWD=crossdimora.159753
DB_HOST=db5435
DB_IMAGE=postgres
DB_TAG=15
DB_PORT=5435

# Volumes
DB_VOLUMES=/opt/odoo8083/db-data
WEB_VOLUMES=/opt/odoo8083/web-data
```

## Step 2: Start Containers

```bash
# Start Odoo and PostgreSQL
docker compose up -d

# Wait 2-3 minutes for Odoo to initialize
docker logs -f odoo_web_8083

# Verify running
docker compose ps
```

## Step 3: Configure Local DNS (dnsmasq)

For local network access without internet:

```bash
# Install dnsmasq
apt-get update && apt-get install -y dnsmasq

# Configure
cat << 'EOF' > /etc/dnsmasq.conf
interface=enp5s0
bind-interfaces
no-resolv
address=/dimora.provecchio.com/192.168.69.240
server=8.8.8.8
cache-size=1000
EOF

# Restart
systemctl restart dnsmasq
systemctl status dnsmasq
```

### Configure Router

Set DNS Primary to `192.168.69.240` in your router so all devices (tablets, phones) resolve the domain locally.

## Step 4: Configure SSL with Let's Encrypt

```bash
# Install Cloudflare plugin
pip3 install certbot-dns-cloudflare --break-system-packages

# Create credentials file
cat << 'EOF' > /root/.secrets.ini
dns_cloudflare_api_token = YOUR_CLOUDFLARE_API_TOKEN
EOF
chmod 600 /root/.secrets.ini

# Get certificate
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets.ini \
  -d dimora.provecchio.com \
  --non-interactive --agree-tos \
  --email soporte@crossnexion.com

# Configure nginx for SSL
cat << 'EOF' > /etc/nginx/sites-available/dimora.provecchio.com
server {
    listen 80;
    server_name dimora.provecchio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dimora.provecchio.com;

    ssl_certificate /etc/letsencrypt/live/dimora.provecchio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dimora.provecchio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    location / {
        proxy_pass http://localhost:8083;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
EOF

# Enable and reload
ln -sf /etc/nginx/sites-available/dimora.provecchio.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

## Step 5: Install Python Dependencies

For auto_database_backup module:

```bash
# Install required packages
docker exec odoo_web_8083 pip3 install --break-system-packages \
    dropbox \
    boto3 \
    paramiko \
    nextcloud-api-wrapper \
    dnspython \
    pandas \
    openpyxl

# Verify installation
docker exec odoo_web_8083 python3 -c "
import dropbox, boto3, paramiko
from nextcloud import NextCloud
print('✅ All dependencies installed')
"
```

## Step 6: Restore Database Backup

```bash
# Copy backup to server
scp backup.zip root@server:/opt/odoo8083/
cd /opt/odoo8083

# Extract
unzip backup.zip

# Restore database
docker exec -i odoo_db_5435 psql -U odoo -d dimora < dump.sql

# Copy filestore to Docker volume
VOL_PATH=/var/lib/docker/volumes/odoo8083_odoo-web-data/_data
rm -rf $VOL_PATH/filestore
cp -r filestore $VOL_PATH/
chown -R 999:root $VOL_PATH/filestore

# Restart Odoo
docker restart odoo_web_8083
sleep 20

# Verify
curl -sI http://192.168.69.240:8083 | head -3
```

## Step 7: Verify Installation

```bash
# Check containers
docker compose ps

# Check Odoo logs
docker logs odoo_web_8083 --tail 50 | grep -E '(loaded|ERROR|http)'

# Test access
curl -sI http://192.168.69.240:8083

# Check database
docker exec odoo_db_5435 psql -U odoo -d dimora -c "
SELECT COUNT(*) as products FROM product_product;
SELECT COUNT(*) as recipes_mrp FROM mrp_bom;
SELECT COUNT(*) as recipes_pos FROM pos_product_bom;
"
```

## Troubleshooting

### Internal Server Error (500)

**Cause:** Missing Python dependencies or module not found.

```bash
# Check logs
docker logs odoo_web_8083 --tail 100 | grep -E '(ERROR|Traceback|ModuleNotFoundError)'

# Install missing dependency
docker exec odoo_web_8083 pip3 install --break-system-packages <package_name>

# Restart Odoo
docker restart odoo_web_8083
```

### Module auto_database_backup Fails to Load

**Cause:** Python dependencies not installed.

```bash
# Install all dependencies
docker exec odoo_web_8083 pip3 install --break-system-packages \
    dropbox boto3 paramiko nextcloud-api-wrapper

# Mark module as uninstalled if corrupted
docker exec odoo_db_5435 psql -U odoo -d dimora -c "
UPDATE ir_module_module SET state='uninstalled' 
WHERE name='auto_database_backup';
"

# Restart Odoo
docker restart odoo_web_8083
```

### Assets Not Loading (CSS/JS/Images Broken)

**Cause:** Filestore not copied to Docker volume.

```bash
# Copy filestore
VOL_PATH=/var/lib/docker/volumes/odoo8083_odoo-web-data/_data
cp -r /opt/odoo8083/filestore $VOL_PATH/
chown -R 999:root $VOL_PATH/filestore

# Restart Odoo
docker restart odoo_web_8083
```

### DNS Not Resolving Locally

**Cause:** dnsmasq not running or router not configured.

```bash
# Check dnsmasq status
systemctl status dnsmasq

# Test resolution
dig dimora.provecchio.com +short

# Should return: 192.168.69.240
```

### Let's Encrypt Certificate Fails

**Cause:** Port 80 blocked or DNS not propagated.

```bash
# Check DNS propagation
dig dimora.provecchio.com +short

# Should return your server IP (not Cloudflare IPs)

# Check port 80 is open
iptables -L -n | grep ':80'

# Use DNS challenge instead (doesn't require port 80)
certbot certonly --dns-cloudflare ...
```

## Post-Installation

### Enable auto_database_backup Module

1. Login to Odoo as admin
2. Go to **Apps**
3. Search for "auto_database_backup"
4. Click **Activate** (may need to remove "Apps" filter)
5. Configure backup destinations

### Configure POS for Tablets

1. Go to **Point of Sale → Configuration → Settings**
2. Enable POS for each tablet
3. Create users for waiters
4. Set up recipes in POS BoM

### Import Products and Recipes

Use the `excel_recipe_import` module:

1. Go to **Manufacturing → Import Excel Recipes**
2. Select import type: MRP only, POS only, or Both
3. Upload Excel file with sheets:
   - `MATERIA PRIMA` (raw materials)
   - `MRP BoM (Subproducts)` (manufacturing recipes)
   - `POS BoM (Comidas)` (POS recipes)
4. Click **Validate** then **Import**

## Maintenance

### Update from GitHub

```bash
cd /opt/odoo8083
git pull origin main
docker compose restart odoo_web_8083
```

### Clean Temporary Files

```bash
# Clean tmp directory
find /opt/odoo8083/tmp -type f -mtime +30 -delete

# Clean Odoo logs
docker exec odoo_web_8083 find /var/lib/odoo/log -type f -mtime +7 -delete
```

### Backup Database

```bash
# Manual backup
docker exec odoo_db_5435 pg_dump -U odoo dimora > backup_$(date +%Y%m%d).sql

# Or use auto_database_backup module
```

## Key Files

- `/opt/odoo8083/.env` - Environment variables (DO NOT COMMIT)
- `/opt/odoo8083/.env.example` - Template for .env
- `/opt/odoo8083/docker-compose.yml` - Docker configuration
- `/opt/odoo8083/requirements.txt` - Python dependencies
- `/opt/odoo8083/config/odoo.conf` - Odoo configuration
- `/opt/odoo8083/tmp/` - Temporary import files (not committed)

## Support

- **Email:** soporte@crossnexion.com
- **GitHub:** https://github.com/marcelompz/odoo19CE
- **Documentation:** See README.md in repository
