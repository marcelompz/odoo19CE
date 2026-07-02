---
name: odoo-19-excel-recipe-import-fixes
description: Fix excel_recipe_import module for Odoo 19 CE - product creation fields and validation
source: auto-skill
extracted_at: '2026-07-02T18:59:32.615Z'
---

# Excel Recipe Import Fixes for Odoo 19 CE

## Problem

The `excel_recipe_import` module failed to import MRP BoM recipes due to invalid field names in product.template creation for Odoo 19 CE.

## Root Causes Identified

1. **Invalid field `detailed_type`** - Doesn't exist in Odoo 19 CE product.template
2. **Invalid field `uom_po_id`** - Doesn't exist in Odoo 19 CE product.template
3. **Invalid field `type`** - Values vary by installation ('product' vs 'goods'), best to omit
4. **Translation function `_()` overwritten** - Loop variable `_` conflicts with translation function

## Solution

### 1. Remove Invalid Fields from product.template Creation

```python
# BEFORE (fails):
template_vals = {
    'name': name,
    'detailed_type': 'product',  # ❌ Invalid
    'standard_price': cost,
    'uom_id': uom.id if uom else False,
    'uom_po_id': uom.id if uom else False,  # ❌ Invalid
    'available_in_pos': available_in_pos,
}

# AFTER (works):
template_vals = {
    'name': name,
    'standard_price': cost,
    'uom_id': uom.id if uom else False,
    'available_in_pos': available_in_pos,
    # Let Odoo use default type value
}
```

### 2. Fix Translation Function Conflict

```python
# BEFORE (fails - _ is overwritten):
message = _("**Importación Exitosa**\n\n")

# AFTER (works):
message = "**Importación Exitosa**\n\n"
```

### 3. Add Import Type Selection

Allow users to choose import scope:
- `both` - Import both MRP and POS BoM
- `mrp` - Import only MRP BoM (Fabricación)
- `pos` - Import only POS BoM (Comidas)

```python
import_type = fields.Selection([
    ('both', 'Recetas MRP y POS BoM'),
    ('mrp', 'Solo Recetas MRP (Fabricación)'),
    ('pos', 'Solo Recetas POS BoM (Comidas)'),
], string='Tipo de Importación', default='both', required=True)
```

### 4. Add Pre-Import Validation

```python
def action_validate(self):
    """Validate dependencies and file structure before import."""
    # Check dependencies
    # Validate Excel file structure
    # Check required sheets exist
    # Show notification without closing window
```

## Dependencies Required

Ensure these Python packages are installed:
- `pandas` (any version)
- `openpyxl` >= 3.1.5
- `packaging`

Install with:
```bash
pip install --break-system-packages "openpyxl>=3.1.5" packaging
```

## Testing Results

### MRP BoM (Subproductos)
- File: `recetas_finales_generado.xlsx`
- Sheet: `MRP BoM (Subproducts)`
- Columns: `Recipe`, `Component`, `Quantity`
- Result: **54 MRP BoM recipes imported successfully**

### POS BoM (Comidas)
- File: `comida_finales_generado.xlsx`
- Sheet: `POS BoM (Comidas)` (must be renamed from MRP BoM if needed)
- Columns: `Recipe`, `Component`, `Quantity`
- Result: **134 POS BoM recipes imported successfully**

### Total: 188 recipes imported

## Deployment to Production

### 1. Push to GitHub
```bash
cd /opt/odoo/odoo8083
git add addons/excel_recipe_import/
git commit -m "feat: excel_recipe_import - POS BoM import with validation"
git push origin main
```

### 2. Deploy to Server
```bash
# On production server (e.g., dimoraserverlocal)
ssh root@server
cd /opt/odoo8083
git pull origin main
```

### 3. Restore Backup (if needed)
```bash
# Copy backup to server
scp backup.zip root@server:/opt/odoo8083/

# Extract and restore
cd /opt/odoo8083
unzip backup.zip
docker compose exec -T db5436 psql -U odoo -d dimora < dump.sql
# Copy filestore to Odoo data directory
docker compose restart web8084
```

### 4. Update Module
```bash
docker compose exec -T web8084 odoo -c /etc/odoo/odoo.conf -d dimora -u excel_recipe_import --stop-after-init
docker compose restart web8084
```

## File Locations

- Module: `/mnt/extra-addons-customize/excel_recipe_import/wizard/import_recipe_wizard.py`
- Manifest: `/mnt/extra-addons-customize/excel_recipe_import/__manifest__.py`
- View: `/mnt/extra-addons-customize/excel_recipe_import/wizard/import_recipe_wizard_views.xml`

## Key Takeaways

1. **Don't specify `type` field** - Let Odoo use its default value for product.template
2. **Check Odoo version** - Field names vary between versions (v18 vs v19)
3. **Avoid `_` as loop variable** - Conflicts with translation function
4. **Add validation before import** - Catch dependency issues early
5. **Keep wizard open after validation** - Let user click Import without reopening
6. **Sheet names must match exactly** - `MRP BoM (Subproducts)` or `POS BoM (Comidas)`
7. **Import type selection** - Choose MRP only, POS only, or both based on your needs
