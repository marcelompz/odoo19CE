---
name: odoo-19-product-import-fields
description: Fix product.template field names and values for Odoo 19 CE imports
source: auto-skill
extracted_at: '2026-07-02T18:40:40.795Z'
---

# Odoo 19 Product Template Field Changes

## Problem

When creating products programmatically in Odoo 19 CE, using Odoo 18 field names/values causes errors:

```
ValueError: Invalid field 'detailed_type' in 'product.template'
ValueError: Invalid field 'uom_po_id' in 'product.template'
```

## Root Cause

Odoo 19 changed the product template field structure:

| Field | Odoo 18 | Odoo 19 |
|-------|---------|---------|
| Type field name | `detailed_type` | `type` |
| Storable value | `'product'` | `'goods'` |
| Purchase UoM field | `uom_po_id` (on template) | Removed from template |

## Solution

### Correct Field Mapping for Odoo 19

```python
# ❌ WRONG (Odoo 18)
template_vals = {
    'name': name,
    'detailed_type': 'product',  # Doesn't exist in Odoo 19
    'uom_po_id': uom.id,  # Doesn't exist on template
    # ...
}

# ✅ CORRECT (Odoo 19)
template_vals = {
    'name': name,
    'type': 'goods',  # Changed from 'detailed_type': 'product'
    'uom_id': uom.id,  # Only uom_id on template
    # uom_po_id removed - only on product.product if needed
    # ...
}
```

### Valid `type` Values in Odoo 19

```python
'goods'     # Producto Almacenable (was 'product')
'service'   # Servicio (same)
'combo'     # Combinado (NEW in Odoo 19)
'consu'     # Consumible (same)
```

### Complete Working Example

```python
def _get_or_create_product(self, name, category_name=None, available_in_pos=False, cost=0.0, uom_name='Unidades'):
    if not name or str(name).lower() == 'nan':
        return False

    name = str(name).strip()
    product = self.env['product.product'].search([('name', '=', name)], limit=1)

    if not product:
        uom = self._get_or_create_uom(uom_name)
        
        # Create product.template first (Odoo 19 fields)
        template_vals = {
            'name': name,
            'type': 'goods',  # Odoo 19: 'goods' instead of 'product'
            'standard_price': cost,
            'uom_id': uom.id if uom else False,
            # NO 'uom_po_id' - doesn't exist on template in Odoo 19
            'available_in_pos': available_in_pos,
        }
        
        if category_name:
            category = self.env['product.category'].search([('name', '=', category_name)], limit=1)
            if not category:
                category = self.env['product.category'].create({'name': category_name})
            template_vals['categ_id'] = category.id

        template = self.env['product.template'].create(template_vals)
        
        # Get the created product variant
        product = template.product_variant_id

        if available_in_pos:
            template.is_pos_bom = True

    return product
```

## Deployment Checklist

After updating Python code:

1. **Clear asset cache from database:**
   ```sql
   DELETE FROM ir_attachment WHERE url LIKE '%/web/assets/%';
   ```

2. **Update the module:**
   ```bash
   docker compose exec web8084 odoo -c /etc/odoo/odoo.conf -d <database> -u <module_name> --stop-after-init
   ```

3. **Restart Odoo:**
   ```bash
   docker compose restart web8084
   ```

4. **Force browser cache clear:**
   - `Ctrl + Shift + R` (Windows/Linux)
   - `Cmd + Shift + R` (Mac)
   - Or open DevTools → Application → Clear storage → Clear site data

5. **Verify in browser:**
   - Open DevTools Console
   - Check for JavaScript errors
   - Confirm no `Invalid field` errors in network requests

## Related Issues

### Import Wizard Validation

Add pre-import validation to catch issues early:

```python
def action_validate(self):
    """Validate file and dependencies before import."""
    errors = []
    
    # Check dependencies
    try:
        import openpyxl
        from packaging import version
        if version.parse(openpyxl.__version__) < version.parse("3.1.5"):
            errors.append(f"openpyxl {openpyxl.__version__} installed, need >= 3.1.5")
    except ImportError:
        errors.append("openpyxl not installed")
    
    # Validate Excel file
    if self.import_file:
        try:
            file_content = base64.b64decode(self.import_file)
            xl = pd.ExcelFile(io.BytesIO(file_content))
            # Check required sheets exist
        except Exception as e:
            errors.append(f"Invalid Excel file: {str(e)}")
    
    if errors:
        raise UserError("\n".join(errors))
    
    return {'type': 'ir.actions.client', 'tag': 'display_notification', ...}
```

### Import Type Selection

Allow users to choose import type (MRP vs POS):

```python
import_type = fields.Selection([
    ('both', 'Recetas MRP y POS BoM'),
    ('mrp', 'Solo Recetas MRP (Fabricación)'),
    ('pos', 'Solo Recetas POS BoM (Comidas)'),
], string='Tipo de Importación', default='both', required=True)

def action_import(self):
    import_mrp = self.import_type in ['both', 'mrp']
    import_pos = self.import_type in ['both', 'pos']
    
    # Import MRP BoM only if selected
    if import_mrp and 'MRP BoM (Subproducts)' in xl.sheet_names:
        # ... process MRP recipes
    
    # Import POS BoM only if selected
    if import_pos and 'POS BoM (Comidas)' in xl.sheet_names:
        # ... process POS recipes
```

## Key Differences: MRP BoM vs POS BoM

| Aspect | MRP BoM | POS BoM |
|--------|---------|---------|
| Model | `mrp.bom` | `pos.product.bom` |
| Level | Template (product.template) | Variant (product.product) |
| UoM | Uses template default UoM | Explicit UoM on each line |
| Purpose | Manufacturing with planning | Quick POS recipes without planning |
| Phantom | Supported | Not supported |

## Testing Checklist

- [ ] Clear browser cache completely (Ctrl+Shift+R)
- [ ] Verify no JavaScript errors in DevTools Console
- [ ] Test with sample product creation
- [ ] Check product form shows correct type ("Producto Almacenable")
- [ ] Verify UoM is set correctly
- [ ] Test import with both MRP and POS sheets
- [ ] Verify imported recipes appear in correct module

## References

- Odoo 19 CE product.template model
- Odoo 19 product type selection values
- Excel recipe import wizard pattern
