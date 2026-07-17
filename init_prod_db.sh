#!/bin/bash
# Script de inicialización de base de datos Odoo 19 CE para Provecchio / OrderFlow
set -e

echo "============================================================"
echo "Inicialización de Odoo 19 CE - Base de datos PROD"
echo "============================================================"

DB_NAME="${DB_NAME:-prod}"
DB_HOST="${DB_HOST:-db5436}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-odoo}"
DB_PASSWD="${DB_PASSWD:-cross.159753}"
ADMIN_EMAIL="${ADMIN_EMAIL:-soporte@crossnexion.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Cross1983_}"

export PGPASSWORD="$DB_PASSWD"

# Verificar módulos l10n_py (montados en el contenedor)
echo "=== Verificando módulos l10n_py ==="
L10N_PY_DIR="/mnt/extra-addons-l10py"
if [ ! -d "$L10N_PY_DIR/l10n_py" ]; then
    L10N_PY_DIR="/mnt/extra-addons-l10n"
fi

if [ -d "$L10N_PY_DIR/l10n_py" ]; then
    echo "✓ Módulos l10n_py disponibles en $L10N_PY_DIR"
    ls -la "$L10N_PY_DIR"
else
    echo "⚠️ Módulos l10n_py no disponibles en $L10N_PY_DIR. Se continuará con los módulos cargados."
fi
echo ""

# Aplicar parche en caliente para el bug de res_users en electronic_invoice_cross si existe
BUGGY_FILE="$L10N_PY_DIR/electronic_invoice_cross/models/res_users.py"
if [ -f "$BUGGY_FILE" ]; then
    echo "=== Aplicando parche en caliente para electronic_invoice_cross ==="
    python3 -c "
file_path = '$BUGGY_FILE'
with open(file_path, 'r') as f:
    content = f.read()
target = \"'l10n_latam_identification_type_id': self.env.ref('l10n_py.it_vat'),\"
replacement = \"'l10n_latam_identification_type_id': self.env.ref('l10n_py.it_vat').id,\"
if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w') as f:
        f.write(content)
    print('  ✓ Bug de psycopg2 (l10n_latam.identification.type) corregido en caliente')
else:
    print('  ✓ El bug ya estaba corregido o el archivo es diferente')
"
fi
echo ""

# Esperar a que PostgreSQL esté disponible
echo "Esperando PostgreSQL en $DB_HOST:$DB_PORT..."
until psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c '\q' 2>/dev/null; do
  echo "  Esperando..."
  sleep 2
done
echo "✓ PostgreSQL disponible"

# Crear DB si no existe
echo "Creando base de datos '$DB_NAME'..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
  echo "✓ Base de datos '$DB_NAME' ya existe"
else
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"
  echo "✓ Base de datos '$DB_NAME' creada"
fi

# Verificar si Odoo ya está inicializado (si existe la tabla res_users)
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 FROM pg_tables WHERE tablename='res_users'" 2>/dev/null | grep -q 1; then
  echo "✓ Odoo ya está inicializado en '$DB_NAME'. Omitiendo configuración de arranque."
  exit 0
fi

# Leer los módulos desde modules.conf
MODULES_LIST=""
MODULES_FILE="/modules.conf"

if [ -f "$MODULES_FILE" ]; then
  echo "✓ Cargando lista de módulos desde $MODULES_FILE"
  MODULES_LIST=$(sed 's/^[[:space:]]*//;s/[[:space:]]*$//' "$MODULES_FILE" | grep -v '^#' | grep -v '^$' | tr '\n' ',' | sed 's/,$//')
else
  echo "⚠️ Archivo $MODULES_FILE no encontrado. Usando lista por defecto."
  MODULES_LIST="base,web,mail,mrp,point_of_sale,stock,purchase,sale,product_mass_import,ica_web_responsive,base_accounting_kit"
fi

echo "Módulos a instalar: $MODULES_LIST"

# Inicializar Odoo 19
echo "Inicializando Odoo en '$DB_NAME'..."
odoo \
     -d "$DB_NAME" \
     --init "$MODULES_LIST" \
     --stop-after-init \
     --without-demo=all \
     --db_host "$DB_HOST" \
     --db_port "$DB_PORT" \
     --db_user "$DB_USER" \
     --db_password "$DB_PASSWD" \
     --addons-path=/mnt/extra-addons-customize,/mnt/extra-addons-l10py,/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
     2>&1 | tail -30

echo "✓ Odoo 19 inicializado"

# Actualizar usuario admin
echo "Actualizando usuario admin..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
UPDATE res_users SET login='$ADMIN_EMAIL' WHERE login='admin';
EOF
echo "  ✓ Email actualizado a: $ADMIN_EMAIL"

# Establecer password usando ORM de Odoo
echo "Estableciendo password..."
python3 << PYEOF
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import odoo
import odoo.tools
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config([
    '--db_host', '$DB_HOST',
    '--db_port', '$DB_PORT',
    '--db_user', '$DB_USER',
    '--db_password', '$DB_PASSWD',
])

try:
    registry = odoo.modules.registry.Registry('$DB_NAME')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user = env['res.users'].search([('login', '=', '$ADMIN_EMAIL')], limit=1)
        if user:
            user.sudo().write({'password': '$ADMIN_PASSWORD'})
            cr.commit()
            print('  ✓ Password establecido con éxito')
        else:
            print('  ✗ Usuario no encontrado')
except Exception as e:
    print('  ✗ Error al establecer password:', e)
PYEOF

# Configurar Paraguay
echo "Configurando Paraguay..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
  "UPDATE res_company SET country_id=(SELECT id FROM res_country WHERE name='Paraguay' LIMIT 1) WHERE id=1;" 2>/dev/null || true

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
  "UPDATE res_company SET currency_id=(SELECT id FROM res_currency WHERE name='PYG' LIMIT 1) WHERE id=1;" 2>/dev/null || true

echo "✓ Paraguay configurado"

# Instalar módulos l10n_py si están disponibles
if [ -d "$L10N_PY_DIR/l10n_py" ]; then
    echo "Instalando módulos de localización Paraguay (l10n_py)..."
    odoo \
         -d "$DB_NAME" \
         --init l10n_py \
         --stop-after-init \
         --without-demo=all \
         --db_host "$DB_HOST" \
         --db_port "$DB_PORT" \
         --db_user "$DB_USER" \
         --db_password "$DB_PASSWD" \
         --addons-path=/mnt/extra-addons-customize,/mnt/extra-addons-l10py,/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
         2>&1 | tail -20
    echo "✓ Módulos de localización Paraguay instalados"
fi

echo ""
IMPORT_PRODUCTS_VAL="${IMPORT_PRODUCTS:-false}"
if [ "$IMPORT_PRODUCTS_VAL" = "true" ] || [ "$IMPORT_PRODUCTS_VAL" = "1" ]; then
    echo "  → Importando productos y comidas (IMPORT_PRODUCTS=true)..."
    python3 /mnt/migracion/import_products_direct.py 2>/dev/null || true
    python3 /mnt/migracion/import_comidas_direct.py 2>/dev/null || true
else
    echo "  ℹ Importación automática de productos desactivada por defecto (IMPORT_PRODUCTS=false). Omitiendo."
fi

echo "============================================================"
echo "✓ Inicialización de Odoo 19 CE completada con éxito"
echo "============================================================"
