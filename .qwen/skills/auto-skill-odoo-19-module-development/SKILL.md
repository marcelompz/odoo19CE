---
name: odoo-19-module-development
description: Key differences and gotchas for developing modules in Odoo 19 vs earlier versions
source: auto-skill
extracted_at: '2026-06-17T22:02:47.235Z'
---

# Odoo 19 Module Development - Key Differences

## View XML Changes

### 1. `tree` → `list`
Odoo 19 renamed the `tree` view type to `list`:

```xml
<!-- BEFORE (Odoo 18 and earlier) -->
<tree>
    <field name="name"/>
</tree>

<!-- AFTER (Odoo 19) -->
<list>
    <field name="name"/>
</list>
```

**Also update `view_mode` in actions:**
```xml
<!-- BEFORE -->
<field name="view_mode">tree,form</field>

<!-- AFTER -->
<field name="view_mode">list,form</field>
```

### 2. `attrs` attribute removed
The `attrs` attribute is deprecated. Use direct domain expressions:

```xml
<!-- BEFORE -->
<field name="location_id" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
<field name="product_count" attrs="{'invisible': [('state', '!=', 'preview')]}"/>

<!-- AFTER -->
<field name="location_id" readonly="state != 'draft'"/>
<field name="product_count" invisible="state != 'preview'"/>
```

**For notebook/page elements:**
```xml
<!-- BEFORE -->
<notebook attrs="{'invisible': [('state', '!=', 'preview')]}">

<!-- AFTER -->
<notebook invisible="state != 'preview'">
```

### 3. Search view `groupby` limitations
Cannot use `groupby` on `selection` type fields:

```xml
<!-- THIS WILL FAIL -->
<search>
    <groupby name="state"/>  <!-- state is Selection -->
</search>

<!-- USE FILTERS INSTEAD -->
<search>
    <filter name="draft" string="Borrador" domain="[('state', '=', 'draft')]"/>
    <filter name="done" string="Completado" domain="[('state', '=', 'done')]"/>
</search>
```

## Python Dependencies

### Installing in Docker containers
External dependencies are NOT auto-installed from `external_dependencies` in manifest:

```bash
# For Debian-based containers with Python 3.12+
docker exec -it <container> pip install --break-system-packages <package>

# Example
docker exec -it odoo_web_8084 pip install --break-system-packages openpyxl
```

**Why `--break-system-packages`?** Python 3.12+ on Debian uses PEP 668 externally-managed environment.

### Manifest declaration (validation only)
```python
'external_dependencies': {
    'python': ['openpyxl'],  # Only validates existence, doesn't install
},
```

## Product Model Changes

### Product types in Odoo 19
**IMPORTANT:** Odoo 19 changed the product type selection:

```python
# Odoo 19 CORRECT values:
'consu'     # Goods (includes storable products) - DEFAULT
'service'   # Service (servicio)
'combo'     # Combo pack

# WRONG in Odoo 19:
'product'   # This was used in Odoo 16-18 for storable, NOW DEPRECATED
'storable'  # Never existed
```

**Example:**
```python
# Default to 'consu' (Goods) for physical products
product_type = 'consu'
if type_val in ['servicio', 'service']:
    product_type = 'service'
elif type_val == 'combo':
    product_type = 'combo'
# 'almacenable', 'storable', 'product' all map to 'consu' in Odoo 19
```

### Setting initial inventory
Use `stock.quant` with `inventory_mode=True`:

```python
self.env['stock.quant'].with_context(inventory_mode=True).create({
    'product_id': product.id,
    'location_id': location.id,
    'inventory_quantity': qty,
}).action_apply_inventory()
```

## Common Errors & Solutions

| Error | Solution |
|-------|----------|
| `View types not defined tree` | Change `<tree>` to `<list>` everywhere |
| `A partir de 17.0 ya no se usan los atributos "attrs"` | Replace `attrs="{'invisible': [...]}"` with `invisible="field != 'value'"` |
| `External ID not found` | Check file load order in manifest `data` list |
| `groupby` on selection field error | Remove `groupby`, use filters instead |
| `attributes construct error` | Check for malformed XML attributes (e.g., `target="new</field>` instead of `target="new"/>`) |

## Module Structure Template

```
module_name/
├── __init__.py
├── __manifest__.py
├── requirements.txt          # For pip install reference
├── models/
│   ├── __init__.py
│   └── model_name.py
├── views/
│   └── views.xml
├── security/
│   └── ir.model.access.csv
├── data/
│   └── data.xml
└── i18n/
    └── es.po
```

## Testing Checklist

After creating/updating a module:

1. Update app list: **Apps → Update Apps List**
2. Upgrade module (not just install)
3. **Hard refresh browser** (Ctrl+F5) to clear cached JS/assets
4. Check logs: `docker logs -f odoo_web_8084`
