---
name: odoo-19-letsencrypt-ssl-setup
description: Configure Let's Encrypt SSL for Odoo 19 CE behind nginx with Cloudflare DNS Challenge
source: auto-skill
extracted_at: '2026-07-02T21:19:40.779Z'
---

# Let's Encrypt SSL Setup for Odoo 19 CE Behind Nginx

## Problem

When deploying Odoo 19 CE behind nginx, **Let's Encrypt HTTP challenge fails** because:
- Odoo's website module intercepts ALL HTTP requests
- Including `/.well-known/acme-challenge/*` paths
- Odoo returns its own 404 page instead of letting nginx serve the challenge file
- Result: `404 Not Found` error from Let's Encrypt

## Solution: Use Cloudflare DNS Challenge

DNS Challenge doesn't require port 80 to be open or accessible from internet. Perfect for:
- Internal network deployments
- Servers behind firewalls/NAT
- Local development environments

## Prerequisites

1. **Cloudflare account** (free tier is sufficient)
2. **Domain added to Cloudflare** with nameservers updated
3. **DNS A record** pointing to your server IP (e.g., `dimora.provecchio.com → 192.168.69.240`)
4. **Nginx installed** and proxying to Odoo

## Step-by-Step Procedure

### Step 1: Create Cloudflare API Token

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Click **"Create Token"**
3. Choose **"Create Custom Token"**
4. Configure:
   - **Token name:** `Odoo SSL Certificate`
   - **Permissions:** `Zone` → `DNS` → `Edit`
   - **Zone Resources:** `Include` → `Specific zone` → `yourdomain.com`
5. Click **"Continue to summary"** → **"Create Token"**
6. **COPY THE TOKEN** (shown only once!)

### Step 2: Install Certbot DNS Plugin on Server

```bash
ssh root@your-server

# Install certbot-dns-cloudflare plugin
pip install certbot-dns-cloudflare --break-system-packages
```

### Step 3: Create Cloudflare Credentials File

```bash
# Create secure credentials file
cat << 'EOF' > /root/.secrets.ini
dns_cloudflare_api_token = YOUR_CLOUDFLARE_TOKEN_HERE
EOF

# Secure the file (CRITICAL - contains API token!)
chmod 600 /root/.secrets.ini
chown root:root /root/.secrets.ini
```

### Step 4: Obtain SSL Certificate

```bash
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets.ini \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --non-interactive \
  --agree-tos \
  --email admin@yourdomain.com
```

**Expected output:**
```
Congratulations! Your certificate and chain have been saved at:
/etc/letsencrypt/live/yourdomain.com/fullchain.pem
```

### Step 5: Configure Nginx for HTTPS

```bash
cat << 'EOF' > /etc/nginx/sites-available/yourdomain.com
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Logging
    access_log /var/log/nginx/yourdomain_access.log;
    error_log /var/log/nginx/yourdomain_error.log;

    # Client body size (important for Odoo file uploads)
    client_max_body_size 200M;

    # Odoo proxy configuration
    location / {
        proxy_pass http://localhost:8083;  # Adjust port as needed
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (for Odoo live chat, notifications)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts (important for long Odoo operations)
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
EOF

# Test and reload nginx
nginx -t && systemctl reload nginx
```

### Step 6: Configure Auto-Renewal

Let's Encrypt certificates expire after 90 days. Set up automatic renewal:

```bash
# Add cron job for automatic renewal
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --dns-cloudflare --dns-cloudflare-credentials /root/.secrets.ini --quiet && systemctl reload nginx") | crontab -
```

This renews certificates daily at 3 AM and reloads nginx if renewal succeeds.

### Step 7: Verify Installation

```bash
# Check certificate details
certbot certificates

# Test HTTPS connection
curl -I https://yourdomain.com

# Check SSL configuration (external)
# Visit: https://www.ssllabs.com/ssltest/analyze.html
```

## Troubleshooting

### Issue: "Could not find domain root"

**Solution:** Ensure DNS A record is correctly configured:
```bash
dig yourdomain.com +short
# Should return your server IP
```

### Issue: "API token invalid"

**Solution:** 
1. Verify token was copied correctly (no extra spaces)
2. Check token permissions in Cloudflare dashboard
3. Ensure zone is correctly specified

### Issue: Certificate not renewing automatically

**Solution:** Test renewal manually:
```bash
certbot renew --dry-run --dns-cloudflare --dns-cloudflare-credentials /root/.secrets.ini
```

Check cron logs:
```bash
grep CRON /var/log/syslog | grep certbot
```

## Alternative: Self-Signed Certificate (Temporary)

If you need HTTPS immediately while waiting for DNS propagation:

```bash
# Create self-signed certificate
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/yourdomain.key \
  -out /etc/nginx/ssl/yourdomain.crt \
  -subj "/CN=yourdomain.com/O=YourOrg/C=Country"

# Update nginx config to use self-signed cert
# (replace ssl_certificate paths in nginx config)
ssl_certificate /etc/nginx/ssl/yourdomain.crt;
ssl_certificate_key /etc/nginx/ssl/yourdomain.key;

# Reload nginx
nginx -t && systemctl reload nginx
```

**Note:** Browsers will show security warnings. Users must "Accept the risk and continue".

## Key Learnings from Provecchio Di Mora Deployment (2026-07-02)

1. **HTTP challenge fails with Odoo** - Odoo intercepts all requests including ACME challenges
2. **DNS Challenge is the solution** - No port 80 required, works behind firewalls
3. **Nginx must proxy to Odoo correctly** - WebSocket support essential for live features
4. **Cloudflare DNS must propagate** - Can take 15 min to 48 hours
5. **Proxy status should be "DNS only"** (grey cloud) in Cloudflare, not "Proxied" (orange cloud)

## References

- [Certbot DNS Plugins](https://certbot.eff.org/docs/using.html#dns-plugins)
- [Cloudflare API Tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
- [Odoo Nginx Configuration](https://www.odoo.com/documentation/19.0/administration/install/deploy.html)
