#!/bin/bash

# Crear directorio de logs si no existe y configurar archivo de log con fecha/hora
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/deploy_$(date +'%Y%m%d_%H%M%S').log"

# Redirigir toda la salida estándar y de errores a la terminal y al archivo de log simultáneamente
exec > >(tee -i "$LOG_FILE") 2>&1

# Estilos de texto
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}       DESPLIEGUE AUTOMÁTICO DE ODOO 19 CE          ${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${GREEN} Registro de salida guardándose en: $LOG_FILE${NC}\n"

# Leer puerto y credenciales del .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo -e "${RED}Error: No se encontró el archivo .env${NC}"
    exit 1
fi

# Valores por defecto de flags CLI
CLEAN_DB=false
AUTO_YES=false

# Procesar argumentos CLI de forma dinámica
for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN_DB=true
            ;;
        -y|--yes)
            AUTO_YES=true
            ;;
        --import-products|--with-products)
            export IMPORT_PRODUCTS=true
            ;;
        --skip-products|--no-products)
            export IMPORT_PRODUCTS=false
            ;;
        --import-recipes|--with-recipes)
            export IMPORT_RECIPES=true
            ;;
        --skip-recipes|--no-recipes)
            export IMPORT_RECIPES=false
            ;;
        --help|-h)
            echo -e "${BOLD}Uso:${NC} ./deploy.sh [OPCIONES]"
            echo -e "Opciones:"
            echo -e "  --clean              Limpia la base de datos y datos web antes de iniciar"
            echo -e "  -y, --yes            Ejecuta de forma no interactiva omitiendo prompts"
            echo -e "  --import-products    Activa la importación automática de productos"
            echo -e "  --skip-products      Desactiva la importación automática de productos"
            echo -e "  --import-recipes     Activa la importación automática de recetas"
            echo -e "  --skip-recipes       Desactiva la importación automática de recetas"
            echo -e "  --help, -h           Muestra esta ayuda"
            exit 0
            ;;
    esac
done

PORT=${WEB_PORT:-8084}
DB_NAME=${DB_NAME:-prod}
EMAIL=${ADMIN_EMAIL:-soporte@crossnexion.com}
PASS=${ADMIN_PASSWORD:-Cross1983_}
IMPORT_PRODUCTS=${IMPORT_PRODUCTS:-false}
IMPORT_RECIPES=${IMPORT_RECIPES:-false}
DB_VOLS=${DB_VOLUMES:-./db-data}
WEB_VOLS=${WEB_VOLUMES:-./web-data}

echo -e "\n${BOLD}Configuración Dinámica:${NC}"
echo -e "  • Limpieza DB: ${YELLOW}$CLEAN_DB${NC}"
echo -e "  • Importar Productos: ${YELLOW}$IMPORT_PRODUCTS${NC}"
echo -e "  • Importar Recetas:   ${YELLOW}$IMPORT_RECIPES${NC}"

if [ "$AUTO_YES" = false ]; then
    echo -e "\n${YELLOW}[!] ADVERTENCIA: Se detendrán los contenedores de Docker (db, web, init).${NC}"
    read -p "¿Desea continuar con el deploy? (s/N): " confirm
    if [[ ! "$confirm" =~ ^[sSyY]$ ]]; then
        echo -e "\n${RED}Operación cancelada por el usuario.${NC}"
        exit 0
    fi
fi

echo -e "\n${BLUE}[1/4] Deteniendo contenedores existentes...${NC}"
docker compose down

if [ "$CLEAN_DB" = false ] && [ "$AUTO_YES" = false ]; then
    echo -e "\n${YELLOW}¿Desea vaciar la base de datos y recrear el entorno desde cero? (s/N): ${NC}\c"
    read confirm_clean
    if [[ "$confirm_clean" =~ ^[sSyY]$ ]]; then
        CLEAN_DB=true
    fi
fi

if [ "$CLEAN_DB" = true ]; then
    if [ "$AUTO_YES" = false ]; then
        echo -e "\n${YELLOW}[!] ADVERTENCIA: Se eliminarán todos los volúmenes de datos de la base de datos.${NC}"
        read -p " ¿Confirma que desea vaciar la base de datos por completo? (s/N): " confirmacion
        if [[ ! "$confirmacion" =~ ^[sSyY]$ ]]; then
            echo -e "\n${RED}Operación de limpieza cancelada por el usuario.${NC}"
            exit 0
        fi
    fi
    # Usar contenedor temporal para borrar las carpetas del host que tienen permisos de root
    docker run --rm -v "${DB_VOLS}":/db -v "${WEB_VOLS}":/web alpine sh -c "rm -rf /db/* /web/*"
    echo -e "${GREEN}✓ Volúmenes de datos limpiados.${NC}"
fi

echo -e "\n${BLUE}[2/4] Iniciando contenedor de Base de Datos...${NC}"
IMPORT_PRODUCTS="$IMPORT_PRODUCTS" IMPORT_RECIPES="$IMPORT_RECIPES" docker compose up -d db5436

echo -e "\n${BLUE}[2.5/4] Construyendo imagen de Odoo 19 local...${NC}"
docker compose build web8084

echo -e "\n${BLUE}[3/4] Iniciando contenedor de Inicialización Automática...${NC}"
IMPORT_PRODUCTS="$IMPORT_PRODUCTS" IMPORT_RECIPES="$IMPORT_RECIPES" docker compose up -d init

echo -e "${YELLOW}[*] Siguiendo logs del contenedor de inicialización en tiempo real:${NC}\n"

# Seguir los logs de init_db hasta que el contenedor se detenga
docker logs -f odoo_init_db_18 2>/dev/null || docker logs -f odoo_init_db_19 2>/dev/null || true

# Obtener código de salida del contenedor init (o 0 si se eliminó limpiamente con auto_remove)
if docker ps -a --format '{{.Names}}' | grep -q '^odoo_init_db_19$'; then
    EXIT_CODE=$(docker inspect odoo_init_db_19 --format='{{.State.ExitCode}}')
else
    EXIT_CODE=0
fi

if [ "$EXIT_CODE" -eq 0 ]; then
    echo -e "\n${GREEN}✓ Inicialización y carga de datos completada con éxito!${NC}"
    docker rm odoo_init_db_19 2>/dev/null || true
else
    echo -e "\n${RED}✗ Error: La inicialización falló con código de salida $EXIT_CODE.${NC}"
    exit 1
fi

echo -e "\n${BLUE}[4/4] Levantando servidor Web de Odoo 19...${NC}"
docker compose up -d web8084
docker network connect traefik-public odoo_web_8084 2>/dev/null || true

echo -e "\n${BOLD}${GREEN}============================================================${NC}"
echo -e "${BOLD}${GREEN}  ¡Despliegue finalizado con éxito!                         ${NC}"
echo -e "${BOLD}${GREEN}  Acceso web: http://localhost:$PORT                        ${NC}"
echo -e "${BOLD}${GREEN}  Base de datos: $DB_NAME                                   ${NC}"
echo -e "${BOLD}${GREEN}  Usuario: $EMAIL                                           ${NC}"
echo -e "${BOLD}${GREEN}  Contraseña: $PASS                                         ${NC}"
echo -e "${BOLD}${GREEN}  Log guardado en: $LOG_FILE                                ${NC}"
echo -e "${BOLD}${GREEN}============================================================${NC}\n"

