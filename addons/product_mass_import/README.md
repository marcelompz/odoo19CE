# Mass Product Import with Inventory

Módulo para Odoo 19 que permite la creación masiva de productos con asignación de cantidades de inventario inicial.

## Características

- **Importación desde Excel**: Carga masiva de productos desde archivos .xlsx
- **Descarga de plantilla**: Plantilla Excel predefinida con estructura y ejemplo
- **Creación en lote en Odoo**: Entrada manual con validación en tiempo real
- **Asignación de stock inicial**: Aplica cantidades automáticamente vía `stock.quant`
- **Validaciones previas**: Detecta errores antes de crear productos
- **Categorías automáticas**: Crea categorías de producto y PdV si no existen

## Requisitos

### Dependencias del sistema

```bash
pip install -r requirements.txt
```

O directamente:

```bash
pip install openpyxl>=3.0.0
```

### Requisitos de Odoo

- Odoo 19.0
- Módulos dependientes: `product`, `stock`, `point_of_sale`

## Instalación

1. Copiar el módulo a la carpeta de addons personalizados
2. Instalar la dependencia `openpyxl` en el entorno de Odoo
3. Reiniciar el servidor de Odoo (para cargar el nuevo paquete Python)
4. En Odoo, activar modo desarrollador
5. Apps → Actualizar lista de aplicaciones
6. Buscar "Mass Product Import with Inventory" e instalar

## Uso

### Importación desde Excel

1. Ir a **Inventario → Importación Masiva → Importar desde Excel**
2. (Opcional) Click en "Descargar Plantilla" para obtener el archivo de ejemplo
3. Seleccionar archivo Excel (.xlsx)
4. Seleccionar ubicación de inventario para el stock inicial
5. Click en "Cargar Archivo" para ver vista previa
6. Revisar productos válidos y con errores
7. Click en "Confirmar Importación"

### Creación en Lote (desde Odoo)

1. Ir a **Inventario → Importación Masiva → Creación en Lote**
2. Click en "Crear"
3. Seleccionar ubicación de inventario
4. Click en "Agregar Línea" o editar directamente en la tabla
5. Click en "Validar" para verificar errores
6. Corregir líneas con errores (marcadas en rojo)
7. Click en "Confirmar" para crear productos

## Estructura del Archivo Excel

| Columna | Nombre | Tipo | Ejemplo |
|---------|--------|------|---------|
| A | Nombre del Producto | Texto | "Taladro Percutor 500W" |
| B | Código de Barras | Texto | "7701234567890" |
| C | Disponible en PdV | Booleano | "VERDADERO" / "FALSO" |
| D | Categoría de Producto | Texto | "Herramientas Eléctricas" |
| E | Categoría de PdV | Texto | "Herramientas" |
| F | Precio de Venta | Número | 150000.00 |
| G | Precio de Costo | Número | 100000.00 |
| H | Cantidad a la Mano | Número | 25 |
| I | Tipo de Producto | Texto | "Almacenable" / "Consumible" / "Servicio" |
| J | Trazabilidad | Texto | "Ninguno" / "Por Lote" / "Por Número de Serie" |

## Validaciones

El módulo valida los siguientes aspectos antes de crear productos:

- ✅ Nombre del producto requerido
- ✅ Código de barras único (no duplicado)
- ✅ Precio de venta no negativo
- ✅ Precio de costo no negativo
- ✅ Cantidad no negativa

Los productos con errores se marcan en rojo y no se crean hasta que se corrijan.

## Estructura del Módulo

```
product_mass_import/
├── __init__.py
├── __manifest__.py
├── requirements.txt
├── data/
│   └── sequence.xml
├── i18n/
│   └── es.po
├── models/
│   ├── __init__.py
│   ├── product_mass_import_wizard.py    # Wizard Excel
│   └── product_batch_import.py          # Creación en lote
├── security/
│   └── ir.model.access.csv
└── views/
    ├── menu_views.xml
    ├── product_batch_import_views.xml
    └── product_mass_import_wizard_views.xml
```

## Licencia

OPL-1 - Odoo Proprietary License v1

## Soporte

Crossnexion E.A.S. - https://www.crossnexion.com
