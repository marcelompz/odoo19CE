# Odoo 19 CE - Despliegue Automático y Módulos Personalizados

Este repositorio (`git@github.com:marcelompz/odoo19CE.git`) contiene la configuración de Docker, automatización de inicialización y módulos personalizados adaptados para **Odoo 19 Community Edition**.

## 🚀 Despliegue Automático

El proyecto incluye scripts de inicialización automatizada equivalentes a los de la arquitectura de producción (compatibles con despliegues en `/srv` o `/opt`):

- **`./deploy.sh`**: Ejecuta el ciclo de despliegue:
  1. Detiene contenedores previos (`docker compose down`).
  2. Inicia el servicio de base de datos (`db5436`).
  3. Reconstruye la imagen local de Odoo 19 con dependencias optimizadas (`docker compose build`).
  4. Levanta el contenedor de inicialización `init` y transmite logs en tiempo real.
  5. Levanta el servicio web final de Odoo 19.

- **`./deploy.sh --clean`**: Solicita confirmación de seguridad para eliminar los volúmenes de datos (`db-data` y `web-data`) y reconstruir el entorno desde cero.

---

## 📦 Módulos Nativos y Personalizados (`modules.conf`)

La lista de módulos a instalar se gestiona dinámicamente desde el archivo `modules.conf`:

- **Módulos Core:** `base`, `web`, `mail`, `stock`, `purchase`, `sale`, `mrp`, `point_of_sale`, `pos_restaurant`.
- **Localización Paraguay:** `electronic_invoice_cross`, `pos_einvoice_cross`.
- **Personalizados Crossnexion:** `product_mass_import`, `ica_web_responsive`.
- **Creación de Recetas / BOM (Opcionales):** Los módulos `pos_product_bom` y `excel_recipe_import` vienen comentados por defecto en `modules.conf`. Para activarlos en una instancia determinada, simplemente descoméntalos antes de ejecutar `./deploy.sh --clean` o instálalos desde la interfaz web.

---

## 🛠️ Archivos de Configuración e Inicialización

- **`init_prod_db.sh`**: Script ejecutado por el contenedor `init`. Crea la base de datos `$DB_NAME`, instala los módulos configurados en `modules.conf`, configura credenciales de administrador, moneda PYG (Guaraní), localización y ejecuta los scripts de datos maestros.
- **`migracion/import_settings.py`**: Aplica configuraciones del sistema, SMTP, depósitos, redondeo de impuestos, plazos de pago y activa el idioma **Español (América Latina) `es_419`** para todos los usuarios y contactos por defecto.
- **`Dockerfile`**: Optimizado instalando bibliotecas de Python pesadas (`pandas`, `openpyxl`, `xlrd`, `paramiko`, `boto3`, `dropbox`) mediante paquetes binarios `.deb` para acelerar los tiempos de construcción.
