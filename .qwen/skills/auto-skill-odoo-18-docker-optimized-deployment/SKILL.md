---
name: odoo-18-docker-optimized-deployment
description: Deploy Odoo 18 CE with optimized Docker Compose configuration including health checks, standard naming conventions, and performance tuning
source: auto-skill
extracted_at: '2026-07-03T12:38:05.396Z'
---

# Odoo 18 CE - Docker Compose Optimized Deployment

## 📋 Configuración Estándar

### Nomenclatura de Contenedores

Seguir el estándar establecido en odoo8083:

| Componente | Patrón | Ejemplo |
|------------|--------|---------|
| **Web** | `odoo_web_{port}` | `odoo_web_8082` |
| **DB** | `db_odoo_{port}` | `db_odoo_5434` |

### Estructura de Directorios

```
/opt/odoo/odoo8082/
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── .env
├── requirements.txt
├── config/
│   └── odoo.conf
├── addons/
├── db-data/
└── web-data/
```

## 🚀 docker-compose.yml Optimizado

```yaml
services:
  web:
    container_name: odoo_web_8082
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8082:8069"
      - "8072:8072"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo:ro
      - ./addons:/mnt/extra-addons-customize:ro
    entrypoint: "/entrypoint.sh"
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

## 🔧 Dockerfile Optimizado

```dockerfile
FROM odoo:18.0

USER root

LABEL MAINTAINER="Provecchio Di Mora <soporte@provecchio.com>"
LABEL DESCRIPTION="Odoo 18.0 CE - Optimized"

# Herramientas de debugging
RUN apt-get update && apt-get install -y \
    curl \
    vim-tiny \
    jq \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Directorio custom scripts
RUN mkdir -p /opt/odoo/custom-scripts && chown odoo:odoo /opt/odoo/custom-scripts

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8069/web/health || exit 1

USER odoo

EXPOSE 8069 8072

ENTRYPOINT ["/entrypoint.sh"]
```

## 📝 entrypoint.sh Mejorado

```bash
#!/bin/bash
set -e

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. Validar variables críticas
log_info "Validando variables de entorno..."
[ -z "$HOST" ] && export HOST="db"
[ -z "$USER" ] && export USER="odoo"
[ -z "$PASSWORD" ] && { log_error "PASSWORD no definido"; exit 1; }
log_success "Variables validadas: HOST=$HOST, USER=$USER"

# 2. Espera inteligente para PostgreSQL
log_info "Esperando a PostgreSQL..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if nc -z "$HOST" 5432 2>/dev/null; then
        log_success "PostgreSQL está listo (intento $attempt/$max_attempts)"
        break
    else
        log_info "Esperando PostgreSQL... (intento $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    fi
done
[ $attempt -gt $max_attempts ] && { log_error "PostgreSQL no respondió"; exit 1; }

# 3. Detectar addons personalizados
log_info "Detectando addons personalizados..."
if [ -d "/mnt/extra-addons-customize" ]; then
    addon_count=$(find /mnt/extra-addons-customize -maxdepth 2 -name "__manifest__.py" | wc -l)
    log_success "Encontrados $addon_count módulos personalizados"
fi

# 4. Iniciar Odoo
log_success "Iniciando Odoo 18.0 CE..."
log_info "Conectando a PostgreSQL en $HOST:5432"
exec odoo --config /etc/odoo/odoo.conf "$@"
```

## ⚙️ odoo.conf Optimizado

```ini
[options]
# Administración
admin_passwd = soportecrossdimora.159753

# Base de datos
db_host = db
db_port = 5432
db_user = odoo
db_password = crossdimora.159753
db_name = postgres
dbfilter = ^prod$|^dimora$
db_maxconn = 64

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
log_db = True
log_db_level = 30

# Seguridad
unaccent = True

# Cron
max_cron_threads = 1

# Web
http_enable = True
http_port = 8069
list_db = True
proxy_mode = True

# Sistema
timezone = America/Asuncion
```

## 🐛 Troubleshooting

### Error: "Pool overlaps with other one on this address space"

**Causa:** Red custom de Docker Compose conflictúa con redes existentes.

**Solución:** Usar red por defecto (eliminar sección `networks` del docker-compose.yml):

```yaml
# ❌ REMOVER esto:
networks:
  odoo-network:
    driver: bridge
    ipam:
      config:
        - subnet: 10.202.0.0/16

# ✅ Usar red por defecto de Docker
```

### Error: "invalid literal for int() with base 10: 'WARNING'"

**Causa:** `log_db_level` en odoo.conf debe ser número, no string.

**Solución:**
```ini
# ❌ INCORRECTO
log_db_level = WARNING

# ✅ CORRECTO
log_db_level = 30
```

### Error: "Conflict. The container name is already in use"

**Causa:** Contenedores viejos no eliminados correctamente.

**Solución:**
```bash
# Eliminar TODOS los contenedores
docker rm -f $(docker ps -aq)

# Limpiar volúmenes y redes de Docker Compose
cd /opt/odoo/odoo8082
docker compose down -v --remove-orphans
rm -rf .docker/

# Reiniciar
docker compose up -d
```

### Error: "Module X: invalid manifest"

**Causa:** Módulo con errores en __manifest__.py o archivos faltantes.

**Solución:**
```bash
# Verificar sintaxis del manifest
python3 -c "import ast; ast.parse(open('addons/module/__manifest__.py').read())"

# Verificar archivos requeridos
ls -la addons/module/
# Debe tener: __init__.py, __manifest__.py

# Verificar directorios referenciados en el manifest
ls -la addons/module/wizard/
ls -la addons/module/models/
```

### Contenedor en estado "Restarting"

**Causa:** Odoo falla al iniciar y Docker lo reinicia automáticamente.

**Solución:**
```bash
# Ver logs completos
docker logs odoo_web_8082 --tail 100

# Buscar errores específicos
docker logs odoo_web_8082 2>&1 | grep -E '(ERROR|Traceback|ValueError)'

# Verificar health check
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082
docker inspect --format='{{.State.Health.Log}}' odoo_web_8082
```

## 📊 Comandos Útiles

### Verificar estado
```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' odoo_web_8082
docker inspect --format='{{.State.Health.Status}}' db_odoo_5434
```

### Ver logs
```bash
docker logs odoo_web_8082 --tail 50 -f
docker logs db_odoo_5434 --tail 50 -f
```

### Acceder a la DB
```bash
docker exec -it db_odoo_5434 psql -U odoo -d postgres
```

### Acceder al contenedor Odoo
```bash
docker exec -it odoo_web_8082 bash
```

### Reiniciar servicios
```bash
docker compose restart
docker compose down -v
docker compose up -d
```

## 🎯 Mejores Prácticas

1. **Nombres estándar:** Siempre usar `odoo_web_{port}` y `db_odoo_{port}`
2. **Health checks:** Esenciales para que Odoo espere a PostgreSQL
3. **Restart policies:** `unless-stopped` para web, `always` para db
4. **Volúmenes bind:** Para persistencia de datos y configuración
5. **Read-only config:** `./config:/etc/odoo:ro` para seguridad
6. **Logging con colores:** Facilita debugging en entrypoint.sh
7. **Espera inteligente:** Validar que PostgreSQL esté listo antes de iniciar Odoo
