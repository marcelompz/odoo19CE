---
name: odoo-18-docker-deployment
description: Deploy Odoo 18 CE with Docker Compose including module compatibility testing, volume configuration, and container naming conventions
source: auto-skill
extracted_at: '2026-07-03T00:21:18.369Z'
---

# Odoo 18 CE Docker Deployment with Module Compatibility Testing

## Context

Deploy Odoo 18 CE from GitHub repository with custom modules migrated from Odoo 19, ensuring proper container naming, volume configuration, and systematic module compatibility testing.

## Key Learnings

### 1. Container Naming Convention

**CRITICAL:** Container names MUST match directory and port numbers:

```yaml
# For odoo8082 directory:
services:
  web8082:
    container_name: odoo_web_8082  # Matches directory (odoo8082) and port (8082)
    ports:
      - "8082:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo

  db5434:
    container_name: db5434  # Matches port (5434)
    ports:
      - "5434:5432"
```

**Why:** Prevents container name conflicts when running multiple Odoo instances on same server.

### 2. Volume Configuration

**CRITICAL:** Volume directories MUST exist before starting containers:

```bash
# Create directories BEFORE docker compose up
mkdir -p /opt/odoo/odoo8082/web-data
mkdir -p /opt/odoo/odoo8082/db-data

# Set correct permissions (Odoo runs as uid 999)
chown -R 999:root /opt/odoo/odoo8082/web-data
chown -R 999:root /opt/odoo/odoo8082/db-data
```

**Why:** Docker cannot create bind-mounted volumes automatically. Missing directories cause "volume not found" errors.

### 3. Environment Variables (.env)

**Required variables for Odoo 18:**

```bash
# Web Configuration
WEB_HOST=odoo_web_8082
WEB_PORT=8082
WEB_IMAGE_NAME=odoo
WEB_IMAGE_TAG=18.0
WEB_ADDONS_CUSTOMIZE=/opt/odoo8082/addons
WEB_VOLUMES=/opt/odoo8082/web-data

# Database Configuration
DB_HOST=db5434
DB_PORT=5434
DB_NAME=postgres
DB_USER=odoo
DB_PASSWD=crossdimora.159753  # Use production passwords
DB_IMAGE=postgres
DB_TAG=15
DB_VOLUMES=/opt/odoo8082/db-data
```

### 4. Module Migration (Odoo 19 → Odoo 18)

**Step-by-step process:**

```bash
# 1. Copy modules from Odoo 19 to Odoo 18
cp -r /opt/odoo/odoo8083/addons/* /opt/odoo/odoo8082/addons/

# 2. Update all manifests from 19.0 to 18.0
find /opt/odoo/odoo8082/addons/ -name "__manifest__.py" -exec sed -i "s/'19.0'/'18.0'/g" {} \;

# 3. Verify version update
grep "'version'" /opt/odoo/odoo8082/addons/excel_recipe_import/__manifest__.py
# Should show: 'version': '18.0.2.0.0'
```

**Why:** Odoo validates manifest version against running version. Mismatch prevents module installation.

### 5. Module Compatibility Testing Strategy

**Test modules ONE BY ONE in this order:**

```bash
# 1. Base dependencies first
- base
- product
- sale
- purchase
- stock

# 2. Custom infrastructure modules
- auto_database_backup  # Test backup functionality
- uom_spanish_import    # Test Spanish UoM import

# 3. Business logic modules
- excel_recipe_import   # Test recipe import
- pos_product_bom       # Test POS BoM

# 4. Integration modules
- Payment providers
- Shipping methods
- Accounting modules
```

**Testing procedure for each module:**

```bash
# 1. Access Odoo: http://localhost:8082
# 2. Go to: Apps → Update Apps List
# 3. Search for module
# 4. Click Install
# 5. Verify:
#    - No errors in logs: docker logs odoo_web_8082 --tail 100
#    - Module shows as "Installed"
#    - Related menus appear
#    - Functionality works (test import, test backup, etc.)
```

### 6. Common Issues and Solutions

#### Issue 1: Container name conflicts
```bash
# Error: "Container name already in use"
# Solution:
docker rm -f odoo_web_8082 db5434
docker compose up -d
```

#### Issue 2: Volume permission errors
```bash
# Error: "Permission denied" in logs
# Solution:
chown -R 999:root /opt/odoo/odoo8082/web-data
chown -R 999:root /opt/odoo/odoo8082/db-data
docker compose restart
```

#### Issue 3: Module manifest version mismatch
```bash
# Error: "Module version doesn't match Odoo version"
# Solution:
find /opt/odoo/odoo8082/addons/ -name "__manifest__.py" -exec sed -i "s/'19.0'/'18.0'/g" {} \;
docker compose restart odoo_web_8082
```

#### Issue 4: Network subnet conflicts
```bash
# Error: "Pool overlaps with other one"
# Solution: Change subnet in docker-compose.yml
# From: 10.201.0.0/16
# To:   10.202.0.0/16
```

### 7. Optimized Docker Compose Configuration

**Use the optimized configuration from README.md:**

```yaml
# Key features:
- Health checks (wait for PostgreSQL before starting Odoo)
- Restart policies (unless-stopped for web, always for db)
- Dedicated network with configurable subnet
- Build context with custom Dockerfile
- Longpolling port exposed (8072)
- Read-only volumes for configuration
```

**Why optimized config is better:**
- ✅ Prevents Odoo from starting before PostgreSQL is ready
- ✅ Auto-restart on failures
- ✅ Better isolation with dedicated network
- ✅ Health monitoring for production
- ✅ Performance optimized (workers, memory limits)

### 8. Git Workflow for Module Development

```bash
# 1. Clone clean repository
cd /opt/odoo
git clone git@github.com:marcelompz/odoo18CE.git odoo8082

# 2. Copy modules from development instance
cp -r /opt/odoo/odoo8083/addons/* /opt/odoo/odoo8082/addons/

# 3. Update manifests
find addons/ -name "__manifest__.py" -exec sed -i "s/'19.0'/'18.0'/g" {} \;

# 4. Commit and push
git add -A
git commit -m "feat: Add modules from odoo8083 for Provecchio Di Mora"
git push origin main

# 5. On production server
cd /opt/odoo8082
git pull origin main
docker compose up -d --build
```

## Procedure

### Step 1: Prepare Environment

```bash
# Create directories
mkdir -p /opt/odoo/odoo8082/{web-data,db-data,config,addons}

# Set permissions
chown -R 999:root /opt/odoo/odoo8082/{web-data,db-data}
```

### Step 2: Clone Repository

```bash
cd /opt/odoo
git clone git@github.com:marcelompz/odoo18CE.git odoo8082
cd odoo8082
```

### Step 3: Configure Environment

```bash
# Create .env with production passwords
cat << 'EOF' > .env
WEB_HOST=odoo_web_8082
WEB_PORT=8082
WEB_IMAGE_TAG=18.0
WEB_ADDONS_CUSTOMIZE=/opt/odoo8082/addons
WEB_VOLUMES=/opt/odoo8082/web-data

DB_HOST=db5434
DB_PORT=5434
DB_PASSWD=crossdimora.159753
DB_VOLUMES=/opt/odoo8082/db-data
EOF
```

### Step 4: Update odoo.conf

```bash
# Update admin password
sed -i 's/admin_passwd = .*/admin_passwd = soportecrossdimora.159753/' config/odoo.conf

# Update db password
sed -i 's/db_password = .*/db_password = crossdimora.159753/' config/odoo.conf
```

### Step 5: Start Containers

```bash
docker compose up -d
sleep 30
docker compose ps
```

### Step 6: Verify Access

```bash
# Check logs
docker logs odoo_web_8082 --tail 50

# Test access
curl -I http://localhost:8082
```

### Step 7: Install Modules One by One

```bash
# For each module:
# 1. Access http://localhost:8082
# 2. Apps → Update Apps List
# 3. Search module name
# 4. Install
# 5. Test functionality
# 6. Check logs for errors
```

### Step 8: Document Results

Create a compatibility matrix:

| Module | Status | Issues | Notes |
|--------|--------|--------|-------|
| excel_recipe_import | ✅ Working | None | Tested with 35MB backup |
| uom_spanish_import | ✅ Working | None | Spanish UoM names work |
| auto_database_backup | ⚠️ Partial | Nextcloud unavailable | S3/SFTP work |
| pos_product_bom | ✅ Working | None | POS BoM imports work |

## Best Practices

1. **Always test on localhost first** before deploying to production
2. **Keep modules in separate Git repository** for version control
3. **Update manifests** when migrating between Odoo versions
4. **Test one module at a time** to isolate compatibility issues
5. **Document all issues** and solutions for future reference
6. **Use health checks** in production deployments
7. **Set restart policies** for automatic recovery
8. **Monitor logs** during initial module installation

## References

- Repository: `https://github.com/marcelompz/odoo18CE`
- README with optimizations: `/opt/odoo/odoo8082/README.md`
- Production deployment: `/opt/odoo/odoo8083/.qwen/skills/auto-skill-odoo-19-provecchio-production-deployment/`
