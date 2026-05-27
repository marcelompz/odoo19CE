# Migración a Odoo 19 - Localización Paraguaya y Módulos de Facturación

Este repositorio contiene las adaptaciones y correcciones necesarias para hacer compatibles los módulos de la localización paraguaya (`l10n_py`) y sus dependencias (como `de_send_email_cross`) con la **versión 19 de Odoo**.

## 🛠️ Cambios Realizados

### 1. Módulo `l10n_py` (Plan de Cuentas e Impuestos)
Se realizaron ajustes estructurales clave para cumplir con la nueva lógica de carga de plantillas contables de Odoo 19 (`account.chart.template`):

*   **Visibilidad del Paquete Fiscal:** Se modificó el método `_get_py_template_data` en `models/template_py.py` agregando los atributos `name` y `visible: True`. Sin estos atributos, Odoo 19 no mostraba la opción "Paraguay - Accounting" en la lista desplegable de Paquetes de Localización Fiscal.
*   **Corrección en la Carga de Impuestos:** Se eliminó la columna obsoleta `chart_template_id` del archivo `data/template/account.tax-py.csv`. Dicha columna era propia de Odoo 14/15 y provocaba que la creación de impuestos fallara silenciosamente en versiones superiores.
*   **Convención de Nombres de Plantillas CSV:** Se respetó la nomenclatura estricta de los archivos CSV dentro de `data/template/` con el sufijo de país (`-py.csv`), que Odoo 19 utiliza de forma dinámica para mapear los modelos contables.
*   **Actualización del Manifest:** Se actualizó la versión del módulo a `19.0.1.0.1` para sincronizar con los estándares de esta versión.

### 2. Módulo `de_send_email_cross`
*   **Resolución de Dependencias:** El módulo requiere la librería externa de Python `dnspython`. Se agregó esta dependencia al archivo `requirements.txt` global del proyecto Docker.
*   **Actualización del Manifest:** Se adaptó la versión del módulo a `19.0.1.0.0`.

## 🚀 Instrucciones de Despliegue en Entorno Dockerizado

1. **Reconstruir dependencias de Python:**
   Asegúrate de reconstruir tu contenedor para que se instalen las nuevas dependencias (o instala manualmente en el contenedor en ejecución):
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```
   *(También puedes instalarlo al vuelo con: `docker exec -u root <container_name> pip3 install dnspython --break-system-packages && docker restart <container_name>`)*

2. **Instalación del Plan de Cuentas (IMPORTANTE):**
   El proceso de Odoo que instala los planes de cuentas e impuestos (`try_loading`) **solo se ejecuta una vez por compañía**. Si en un entorno de pruebas tuviste instalaciones fallidas, el sistema no reintentará la carga automáticamente al actualizar el módulo.
   *   **Solución recomendada:** Para probar la instalación, **crea una nueva base de datos** o **una nueva compañía**. Al seleccionar la localización en la nueva instancia, se cargarán correctamente todas las cuentas contables, impuestos (ej. ITAX_10, OTAX_10) y posiciones fiscales.

## 📌 Requisitos Previos (Odoo 19)
*   Módulos base: `account`, `contacts`, `l10n_latam_base`, `l10n_latam_invoice_document`, `uom`.
*   Entorno Python: Incluir dependencias de `requirements.txt` (boto3, paramiko, dnspython, etc.).
