---
name: odoo-19-provecchio-deployment
description: Complete Odoo 19 CE deployment for Provecchio Di Mora with Docker, DNS, SSL, and recipe imports
source: auto-skill
extracted_at: '2026-07-02T21:59:29.595Z'
---

# Odoo 19 CE Deployment - Provecchio Di Mora

Complete deployment procedure for Odoo 19 CE on local network with Docker Compose, local DNS, SSL certificates, and recipe imports for restaurant POS/MRP operations.

## Infrastructure Overview

- **Server:** Local network (192.168.69.240)
- **Domain:** dimora.provecchio.com
- **Port:** 8083
- **Containers:** odoo_web_8083, odoo_db_5435
- **Database:** dimora (PostgreSQL 15)
- **Use Case:** Restaurant/food business (internal use, no public website)

## Prerequisites

- Debian 12 server with Docker Compose
- Cloudflare DNS configured for domain
- Local network access (192.168.69.0/24)
- Backup file: `dimora_2026-07-02_19-28-00.zip` (contains dump.sql + filestore)

## Step 1: Docker Compose Configuration

Create `/opt/odoo8083/docker-compose.yml`:

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
    build: ./
    depends_on:
      - db5435
    ports:
      - "8083:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - /mnt/addons:/mnt/extra-addons
      - ./addons:/mnt/extra-addons-customize
    entrypoint: "/usr/bin/odoo -c /etc/odoo/odoo.conf"
    environment:
      - HOST=db5435
      - USER=odoo
      - PASSWORD=crossdimora.159753
      - TZ=America/Asuncion
      - DEBIAN_FRONTEND=noninteractive
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  db5435:
    container_name: odoo_db_5435
    image: postgres:15
    environment:
      - POSTGRES_DB=dimora
      - POSTGRES_PASSWORD=crossdimora.159753
      - POSTGRES_USER=odoo
      - PGDATA=/var/lib/postgresql/data/pgdata
      - TZ=America/Asuncion
      - DEBIAN_FRONTEND=noninteractive
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

## Step 2: Odoo Configuration

Create `/opt/odoo8083/config/odoo.conf`:

```ini
[options]
addons_path = /mnt/extra-addons,/mnt/extra-addons-customize
admin_passwd = soportecrossdimora.159753
db_host = db5435
db_port = 5432
db_user = odoo
db_password = crossdimora.159753
db_name = dimora
dbfilter = ^dimora$
list_db = True
proxy_mode = True
http_port = 8069
logfile = False
log_level = info
```

## Step 3: Start Containers

```bash
cd /opt/odoo8083
docker compose up -d
sleep 30
docker compose ps
```

## Step 4: Restore Database Backup

```bash
cd /opt/odoo8083

# Extract backup
unzip dimora_2026-07-02_19-28-00.zip

# Create database
docker exec odoo_db_5435 psql -U odoo -c "CREATE DATABASE dimora;"

# Restore dump
docker exec -i odoo_db_5435 psql -U odoo -d dimora < dump.sql

# Copy filestore to Docker volume (CRITICAL - prevents asset errors)
VOL_PATH=/var/lib/docker/volumes/odoo8083_odoo-web-data/_data
rm -rf $VOL_PATH/filestore
cp -r /opt/odoo8083/filestore $VOL_PATH/
chown -R 999:root $VOL_PATH/filestore

# Restart Odoo
docker restart odoo_web_8083
sleep 15
```

## Step 5: Install Python Dependencies

Required for custom modules (auto_database_backup, etc.):

```bash
docker exec odoo_web_8083 pip3 install --break-system-packages dropbox boto3
docker restart odoo_web_8083
sleep 15
```

## Step 6: Configure Local DNS (dnsmasq)

For internal network access without internet:

```bash
# Install dnsmasq
apt-get update && apt-get install -y dnsmasq

# Configure
cat << 'EOF' > /etc/dnsmasq.conf
interface=enp5s0
bind-interfaces
no-resolv
address=/dimora.provecchio.com/192.168.69.240
address=/provecchio.local/192.168.69.240
server=8.8.8.8
server=1.1.1.1
cache-size=1000
EOF

# Start service
systemctl enable dnsmasq && systemctl restart dnsmasq
systemctl status dnsmasq
```

### Router Configuration

Configure your router to use `192.168.69.240` as primary DNS server. This allows all devices on the network to resolve `dimora.provecchio.com` automatically.

### Alternative: Manual DNS on Tablets

For each tablet:
1. Settings → WiFi → Your network → Advanced → DNS
2. Set DNS to: `192.168.69.240`
3. Save

## Step 7: Configure Nginx Reverse Proxy

```bash
# Install nginx
apt-get install -y nginx

# Create config
cat << 'EOF' > /etc/nginx/sites-available/dimora.provecchio.com
server {
    listen 80;
    server_name dimora.provecchio.com;

    # Let's Encrypt challenge (if using DNS challenge, this is optional)
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files $uri =404;
    }

    # Odoo proxy
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
        client_max_body_size 200M;
    }
}
EOF

# Enable and test
ln -sf /etc/nginx/sites-available/dimora.provecchio.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

## Step 8: SSL Certificate Options

### Option A: Self-Signed (Quick, for internal use)

```bash
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/dimora.key \
  -out /etc/nginx/ssl/dimora.crt \
  -subj '/CN=dimora.provecchio.com/O=Provecchio/C=PY'

# Update nginx config to use SSL (see SSL configuration below)
```

### Option B: Let's Encrypt with Cloudflare DNS Challenge (Recommended)

```bash
# Install Cloudflare plugin
apt-get install -y python3-certbot-dns-cloudflare

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

# Auto-renewal cron
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --dns-cloudflare --dns-cloudflare-credentials /root/.secrets.ini --quiet && systemctl reload nginx") | crontab -
```

### Nginx SSL Configuration

```nginx
server {
    listen 80;
    server_name dimora.provecchio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dimora.provecchio.com;

    # For Let's Encrypt:
    ssl_certificate /etc/letsencrypt/live/dimora.provecchio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dimora.provecchio.com/privkey.pem;

    # OR for self-signed:
    # ssl_certificate /etc/nginx/ssl/dimora.crt;
    # ssl_certificate_key /etc/nginx/ssl/dimora.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Proxy configuration (same as above)
    location / {
        proxy_pass http://localhost:8083;
        # ... (rest of proxy config)
    }
}
```

## Step 9: Verify Deployment

### Check Containers

```bash
docker compose ps
# Should show: odoo_web_8083 (Up), odoo_db_5435 (Up)
```

### Check Logs

```bash
docker logs odoo_web_8083 --tail 30
# Should show: "HTTP service (werkzeug) running on <container_id>:8069"
# Should NOT show: "ERROR", "Failed to load registry"
```

### Check Database

```bash
docker exec odoo_db_5435 psql -U odoo -d dimora -c "SELECT COUNT(*) FROM product_product;"
# Should return: 566 (or your product count)

docker exec odoo_db_5435 psql -U odoo -d dimora -c "SELECT COUNT(*) FROM mrp_bom;"
# Should return: 54 (MRP recipes)

docker exec odoo_db_5435 psql -U odoo -d dimora -c "SELECT COUNT(*) FROM pos_product_bom;"
# Should return: 134 (POS recipes)
```

### Check Filestore

```bash
ls /var/lib/docker/volumes/odoo8083_odoo-web-data/_data/filestore/dimora/ | wc -l
# Should return: 240 (folder count)
```

### Test Access

From local network:
```bash
# Test DNS resolution
dig dimora.provecchio.com +short
# Should return: 192.168.69.240

# Test HTTP
curl -I http://192.168.69.240:8083
# Should return: HTTP/1.1 200 OK or 303 SEE OTHER

# Test HTTPS (if SSL configured)
curl -Ik https://192.168.69.240:443
# Should return: HTTP/1.1 200 OK
```

## Step 10: Access Odoo

### URL for Tablets/POS

```
http://192.168.69.240:8083/web/login
```

OR with DNS configured:

```
http://dimora.provecchio.com:8083/web/login
```

### Default Login

- **Database:** dimora
- **Email:** soporte@crossnexion.com
- **Password:** (set during database creation or from backup)
- **Master Password:** soportecrossdimora.159753

## Troubleshooting

### Issue: Website loads with broken assets (CSS/JS missing)

**Cause:** Filestore not copied to Docker volume

**Solution:**
```bash
VOL_PATH=/var/lib/docker/volumes/odoo8083_odoo-web-data/_data
rm -rf $VOL_PATH/filestore
cp -r /opt/odoo8083/filestore $VOL_PATH/
chown -R 999:root $VOL_PATH/filestore
docker restart odoo_web_8083
```

### Issue: Module import error (ModuleNotFoundError)

**Cause:** Missing Python library

**Solution:**
```bash
# For dropbox
docker exec odoo_web_8083 pip3 install --break-system-packages dropbox

# For boto3 (AWS)
docker exec odoo_web_8083 pip3 install --break-system-packages boto3

docker restart odoo_web_8083
```

### Issue: "Failed to load registry" error

**Cause:** Module dependency missing or database connection failed

**Solution:**
1. Check database is running: `docker compose ps`
2. Check logs: `docker logs odoo_web_8083 --tail 100`
3. Install missing Python libraries (see above)
4. Restart Odoo: `docker restart odoo_web_8083`

### Issue: DNS not resolving on tablets

**Solution:**
1. Verify dnsmasq is running: `systemctl status dnsmasq`
2. Check router DNS settings (should point to 192.168.69.240)
3. Test from server: `dig dimora.provecchio.com +short`
4. Manually configure DNS on tablet if needed

### Issue: SSL certificate warning in browser

**Normal for self-signed certificates.** Users must accept the warning.

**Solution:** Use Let's Encrypt with Cloudflare DNS challenge for production.

## Maintenance

### Backup Database

```bash
# Dump database
docker exec odoo_db_5435 pg_dump -U odoo dimora > dimora_backup_$(date +%Y-%m-%d).sql

# Backup filestore
tar -czf filestore_backup_$(date +%Y-%m-%d).tar.gz \
  /var/lib/docker/volumes/odoo8083_odoo-web-data/_data/filestore/dimora/
```

### Update Odoo Modules

```bash
cd /opt/odoo8083
git pull  # If using git
docker restart odoo_web_8083
```

### Monitor Disk Space

```bash
df -h
docker system df
```

## Key Learnings

1. **Filestore MUST be copied to Docker volume** after database restore, or assets will fail to load
2. **Python libraries** (dropbox, boto3) must be installed inside the container for custom modules
3. **Container naming convention:** odoo_web_{port}, odoo_db_{port} for clarity
4. **Internal DNS (dnsmasq)** is essential for mobile devices (tablets) that can't use /etc/hosts
5. **Database port:** Internal container port is 5432, external is 5435 (configured in docker-compose)
6. **Odoo config:** db_host must match Docker service name (db5435), db_port must be internal port (5432)
