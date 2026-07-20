---
name: odoo-18-provecchio-clean-rebuild
description: Complete Odoo 18.0 CE clean rebuild procedure for Provecchio Di Mora with Docker Compose, environment variables, and GitHub deployment
source: auto-skill
extracted_at: '2026-07-03T15:09:42.000Z'
---

# Odoo 18.0 CE - Clean Rebuild Procedure for Provecchio Di Mora

## Overview

Complete procedure for deploying Odoo 18.0 CE from GitHub with Docker Compose using environment variables (no odoo.conf required).

## Prerequisites

- Docker and Docker Compose installed
- Git configured with SSH access to GitHub
- Root access to server

## Step 1: Clone Repository

```bash
cd /opt/odoo
rm -rf odoo8082 2>/dev/null
git clone git@github.com:marcelompz/odoo18CE.git odoo8082
cd /opt/odoo/odoo8082
```

## Step 2: Create .env File

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

## Step 3: Docker Compose Configuration

The `docker-compose.yml` uses **Docker volumes** (not bind mounts) to avoid permission issues:

```yaml
services:
  web:
    container_name: odoo_web_8082
    image: odoo:18.0
    depends_on:
      - db
    ports:
      - "8082:8069"
      - "8072:8072"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons-customize:ro
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
      - LIMIT_TIME_CPU=600
      - LIMIT_TIME_REAL=1200
      
      # System
      - TZ=America/Asuncion
      - ODOO_LOG_LEVEL=info
      
    restart: unless-stopped
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
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=crossdimora.159753
      - TZ=America/Asuncion
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
  odoo-web-data:
```

## Step 4: Start Containers

```bash
# Remove any existing containers and volumes
docker compose down -v

# Start fresh containers
docker compose up -d

# Wait for health checks (90 seconds)
sleep 90

# Verify status
docker compose ps
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082
```

## Step 5: Verify Deployment

```bash
# Test web access
curl -sI http://localhost:8082

# Check logs
docker logs odoo_web_8082 --tail 30

# Expected: HTTP 303 SEE OTHER (redirect to login)
```

## Step 6: Access Odoo

1. **URL:** `http://localhost:8082`
2. **Create Database:**
   - Database name: `prod`
   - Master password: `soportecrossdimora.159753`
   - Email: `soporte@crossnexion.com`
   - Language: Spanish (Latin America)
   - Country: Paraguay

## Troubleshooting

### Permission Denied: /var/lib/odoo/sessions

**Problem:** Using bind mounts instead of Docker volumes.

**Solution:** Use Docker named volumes in docker-compose.yml:

```yaml
volumes:
  - odoo-web-data:/var/lib/odoo  # ✅ Docker volume
  # NOT: - ./web-data:/var/lib/odoo  # ❌ Bind mount
```

### Health Check Failing

**Problem:** Odoo can't connect to database.

**Solution:** Verify database credentials match:

```bash
# Check .env
grep DB_PASSWD .env

# Check docker-compose.yml
grep PASSWORD docker-compose.yml

# Both should be: crossdimora.159753
```

### Container Won't Start

**Solution:** Complete clean rebuild:

```bash
# Stop and remove everything
docker compose down -v

# Remove volumes physically
rm -rf /opt/odoo/odoo8082/web-data/*
rm -rf /opt/odoo/odoo8082/db-data/*

# Recreate
docker compose up -d
sleep 90
```

### Wrong Container Started (odoo8083 instead of odoo8082)

**Problem:** Running docker compose from wrong directory.

**Solution:** Always specify the compose file:

```bash
# WRONG (uses current directory)
docker compose up -d

# CORRECT (specify file)
docker compose -f /opt/odoo/odoo8082/docker-compose.yml up -d

# OR change to correct directory first
cd /opt/odoo/odoo8082
docker compose up -d
```

## Key Learnings

1. **Use Docker volumes, not bind mounts** for `/var/lib/odoo` to avoid permission issues
2. **Use environment variables** instead of odoo.conf (Odoo 18 native support)
3. **Health check endpoint:** `/web/database/selector` (not `/web/health`)
4. **Standard naming:** `odoo_web_{port}`, `db_odoo_{port}`
5. **Always specify compose file** when multiple Odoo instances exist
6. **Wait 90 seconds** for health checks to pass

## GitHub Deployment

After successful local deployment:

```bash
cd /opt/odoo/odoo8082

# Initialize git if needed
git init
git remote add origin git@github.com:marcelompz/odoo18CE.git

# Add files
git add docker-compose.yml .gitignore Dockerfile .env.example

# Commit and push
git commit -m "feat: Odoo 18.0 CE deployment for Provecchio Di Mora"
git push -u origin master
```

## Configuration Reference

| Setting | Value |
|---------|-------|
| **Web Port** | 8082 |
| **DB Port** | 5434 |
| **Container Names** | `odoo_web_8082`, `db_odoo_5434` |
| **Admin Password** | `soportecrossdimora.159753` |
| **DB Password** | `crossdimora.159753` |
| **Workers** | 2 |
| **Memory Hard Limit** | 2.5GB |
| **Memory Soft Limit** | 2GB |
| **Timezone** | `America/Asuncion` |
