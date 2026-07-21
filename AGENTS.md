# AGENTS - Ajustes específicos de esta instancia

## Instancia
- **Odoo**: 19 CE
- **Base de datos**: `prod`
- **Addons path**: `/mnt/extra-addons,/mnt/extra-addons-l10n,/usr/lib/python3/dist-packages/odoo/addons`
- **Container**: `odoo_web_8084`
- **Puerto**: 8084

## Formato XML requerido

Esta instancia usa un schema RELAX NG personalizado que **solo acepta**:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="..." model="ir.ui.view">...</record>
    <record id="..." model="ir.actions.act_window">...</record>
    <menuitem id="..." .../>
</odoo>
```

**NO acepta:**
- `<openerp>` como raíz
- `<data>` como wrapper
- `<tree>` en listas (usa `<list>`)
- `<chatter>` como widget (usar `<div class="oe_chatter">`)

## Módulos modificados

### product_mass_import
- **Problema original**: XML con `<data>`, `<tree>`, `<odoo>` mixto con `<data>`
- **Solución**: Reformatear todo a `<odoo>` plano con `<record>` y `<list>`
- **Tipo de producto**: Cambiado de `combo` (inválido en Odoo 19 CE) a `product`, `consu`, `service`
- **Batch creation**: Ahora vincula `product_id` a las líneas después de crear productos
- **Reload**: `action_confirm` retorna `display_notification + act_window_reload` para forzar refresco en Odoo 19 OWL
- **Menú**: Ahora aparece como raíz en el menú principal (no solo en Inventario)

### excel_recipe_import
- **Problema**: Vista exigía campo `import_type` que no existía en el modelo
- **Solución**: Agregado campo `import_type` (Selection) al wizard `excel.recipe.import.wizard`

### mass_import_suite (nuevo)
- **Propósito**: Módulo paraguas que agrupa `product_mass_import` y `excel_recipe_import`
- **Dependencias**: `product_mass_import`, `excel_recipe_import`
- **Menú**: Raíz "Mass Import Suite" con submenús "Productos" y "Recetas"

### orderflow_connector
- **Problema**: Orden de carga de XML - `menu_views.xml` se cargaba después de `orderflow_import_wizard_views.xml`
- **Solución**: Reordenar manifest para cargar `menu_views.xml` primero

## Orden de instalación recomendado

1. `product_mass_import` (depende de product, stock, pos)
2. `excel_recipe_import` (depende de product, mrp, pos_product_bom)
3. `mass_import_suite` (depende de los dos anteriores)
4. `orderflow_connector` (independiente)

## Docker Compose

- Conflicto de merge resuelto en `docker-compose.yml`
- Volúmenes unificados: `odoo-web-data`, `./config`, `./addons`, `./migracion`
- Removido `./addons:/mnt/extra-addons:ro` duplicado

## Accesos directos útiles

- Batch import: `/web#action=product_mass_import.product_batch_import_action`
- Excel wizard: `/web#action=product_mass_import.product_mass_import_wizard_action`
- Recipe wizard: `/web#action=orderflow_connector.action_orderflow_import_wizard` (si orderflow está instalado)
