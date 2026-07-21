# Changelog

Todos los cambios realizados en los módulos custom de esta instancia Odoo 19 CE.

## [2026-07-20] - Ajustes de compatibilidad Odoo 19 CE

### product_mass_import
- **fix(xml)**: Reformatear todas las vistas a `<odoo>` plano sin `<data>`, usando `<list>` en vez de `<tree>`
- **fix(xml)**: Corregir cierres de tags mal mezclados (`</tree>` sobrantes)
- **fix(model)**: Eliminar tipo de producto `combo` (no existe en Odoo 19 CE). Quedan: `product` (Almacenable), `consu` (Consumible), `service` (Servicio)
- **fix(model)**: Corregir mapeo de tipo en wizard Excel: "Almacenable" → `product` en lugar de `consu`
- **fix(batch)**: Vincular `product_id` a cada línea después de crear productos en `action_confirm`
- **fix(batch)**: Cambiar retorno de `action_confirm` a `display_notification + act_window_reload` para forzar refresco en Odoo 19 OWL
- **feat(menu)**: Mover menú a raíz del menú principal con `web_icon`
- **fix(manifest)**: Actualizar versión a `19.0.1.4.2`
- **fix(chatter)**: Reemplazar `<div class="oe_chatter">` obsoleto por estructura compatible
- **fix(view_mode)**: Cambiar `tree,form` a `list,form` en acción
- **fix(manifest)**: Remover `menu_views.xml` duplicado del manifest

### excel_recipe_import
- **fix(model)**: Agregar campo faltante `import_type` (Selection) al wizard `excel.recipe.import.wizard`
- **fix(manifest)**: Actualizar versión

### mass_import_suite (nuevo)
- **feat**: Crear módulo paraguas que agrupa `product_mass_import` y `excel_recipe_import`
- **feat**: Menú raíz "Mass Import Suite" con submenús "Productos" y "Recetas"
- **feat**: Icono del suite copiado desde `product_mass_import`

### orderflow_connector
- **fix(manifest)**: Reordenar carga de XML: `menu_views.xml` antes que `orderflow_import_wizard_views.xml` para evitar error de menú padre no encontrado

## [2026-07-20] - Infraestructura

### Docker Compose
- **fix**: Resolver conflictos de merge en `docker-compose.yml`
- **fix**: Unificar volúmenes entre servicios `web8084` e `init`

### Repositorio
- **fix**: Limpiar directorios anidados duplicados (`product_mass_import/product_mass_import/`)
- **chore**: Sincronizar cambios con GitHub (`marcelompz/odoo19CE`)
