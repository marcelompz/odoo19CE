---
name: Odoo Recipe Import Type Selection
description: Import recipes selectively for MRP (manufacturing) or POS (point of sale) using a wizard with import type selection
source: auto-skill
extracted_at: '2026-07-02T17:46:41.450Z'
---

# Odoo Recipe Import with Type Selection

When importing recipes from Excel into Odoo where you have **separate modules for Manufacturing (MRP BoM) and Point of Sale (POS BoM)**, use a wizard with import type selection to control which recipes are imported.

## Key Differences Between MRP and POS BoM

| Aspect | MRP BoM (Manufacturing) | POS BoM (Point of Sale) |
|--------|------------------------|------------------------|
| **Model** | `mrp.bom` + `mrp.bom.line` | `pos.product.bom` + `pos.product.bom.line` |
| **Product Level** | Template (`product_tmpl_id`) | Specific Product Variant (`product_id`) |
| **UoM Handling** | Uses default product UoM | Explicit `product_uom_id` on each line |
| **Purpose** | Manufacturing with planning | Quick recipes for POS without planning |
| **Excel Sheet** | `MRP BoM (Subproducts)` | `POS BoM (Comidas)` |

## Implementation Pattern

### 1. Add Import Type Selection Field

```python
import_type = fields.Selection([
    ('both', 'Recetas MRP y POS BoM'),
    ('mrp', 'Solo Recetas MRP (Fabricación)'),
    ('pos', 'Solo Recetas POS BoM (Comidas)'),
], string='Tipo de Importación', default='both', required=True)
```

### 2. Conditional Import Logic

```python
def action_import(self):
    # Validate dependencies first
    is_valid, errors, warnings = self._check_dependencies()
    if not is_valid:
        raise UserError("\n".join(errors))
    
    # Determine which types to import
    import_mrp = self.import_type in ['both', 'mrp']
    import_pos = self.import_type in ['both', 'pos']
    
    # Always import prerequisites (Materia Prima, Products)
    if 'MATERIA PRIMA' in xl.sheet_names:
        self._import_materia_prima(xl)
    
    # Import MRP BoM only if selected
    if import_mrp and 'MRP BoM (Subproducts)' in xl.sheet_names:
        self._import_mrp_bom(xl)
    
    # Import POS BoM only if selected
    if import_pos and 'POS BoM (Comidas)' in xl.sheet_names:
        self._import_pos_bom(xl)
```

### 3. MRP BoM Import Method

```python
def _import_mrp_bom(self, xl):
    df_mrp = xl.parse('MRP BoM (Subproducts)')
    for recipe_name, group in df_mrp.groupby('Recipe'):
        recipe_product = self._get_or_create_product(recipe_name, category_name='Subproducto')
        
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': recipe_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        
        for _, row in group.iterrows():
            comp_product = self._get_or_create_product(row.get('Component'))
            self.env['mrp.bom.line'].create({
                'bom_id': bom.id,
                'product_id': comp_product.id,
                'product_qty': float(row.get('Quantity', 1.0))
            })
```

### 4. POS BoM Import Method

```python
def _import_pos_bom(self, xl):
    df_pos = xl.parse('POS BoM (Comidas)')
    for recipe_name, group in df_pos.groupby('Recipe'):
        recipe_product = self._get_or_create_product(recipe_name, category_name='Comidas', available_in_pos=True)
        recipe_product.product_tmpl_id.is_pos_bom = True
        
        bom = self.env['pos.product.bom'].create({
            'product_id': recipe_product.id,  # Specific variant, not template
            'product_qty': 1.0,
            'product_uom_id': recipe_product.uom_id.id,
        })
        
        for _, row in group.iterrows():
            comp_product = self._get_or_create_product(row.get('Component'))
            self.env['pos.product.bom.line'].create({
                'pos_bom_id': bom.id,
                'product_id': comp_product.id,
                'product_qty': float(row.get('Quantity', 1.0)),
                'product_uom_id': comp_product.uom_id.id,  # Explicit UoM
            })
```

### 5. Add Dependency Validation

```python
def _check_dependencies(self):
    """Validate required Python packages before import."""
    errors = []
    
    # Check pandas
    if pd is None:
        errors.append("❌ La librería 'pandas' no está instalada")
    
    # Check openpyxl version
    try:
        import openpyxl
        from packaging import version
        if version.parse(openpyxl.__version__) < version.parse("3.1.5"):
            errors.append(f"❌ openpyxl {openpyxl.__version__}. Se requiere 3.1.5+")
    except ImportError:
        errors.append("❌ La librería 'openpyxl' no está instalada")
    
    return len(errors) == 0, errors, []
```

### 6. Update XML View

```xml
<group>
    <group>
        <field name="import_type"/>
    </group>
    <group>
        <field name="import_file" filename="import_filename"/>
    </group>
</group>
<footer>
    <button name="action_validate" string="Validar Archivo" type="object" class="btn-info"/>
    <button name="action_import" string="Importar" type="object" class="btn-primary"/>
</footer>
```

## Usage Workflow

1. **User uploads Excel file** with sheets: `MATERIA PRIMA`, `Products`, `MRP BoM (Subproducts)`, `POS BoM (Comidas)`

2. **User selects import type:**
   - `both` → Import all sheets
   - `mrp` → Import only MRP BoM (skip POS BoM)
   - `pos` → Import only POS BoM (skip MRP BoM)

3. **User clicks "Validar Archivo"** → Check dependencies and file structure

4. **User clicks "Importar"** → Import only selected recipe types

## Benefits

- **Selective imports** prevent accidentally overwriting POS recipes when updating MRP recipes
- **Clear separation** of concerns between manufacturing and point-of-sale workflows
- **Dependency validation** catches missing packages before import fails
- **Detailed feedback** shows exactly which sheets were imported and how many records

## Common Issues & Solutions

### Issue 1: `detailed_type` field error on product.product

**Error:** `ValueError: Invalid field 'detailed_type' in 'product.product'`

**Cause:** `detailed_type` exists on `product.template`, not `product.product`.

**Solution:** Create template first, then get variant:

```python
template = self.env['product.template'].create({
    'name': name,
    'detailed_type': 'product',  # 'product' = Almacenable
    'standard_price': cost,
    'uom_id': uom.id,
    'uom_po_id': uom.id,
    'categ_id': category.id,
})
product = template.product_variant_id  # Get the variant
```

### Issue 2: Validation closes wizard window

**Problem:** After clicking "Validar Archivo", the wizard window closes automatically, requiring user to reopen it.

**Solution:** Don't include `next` parameter in notification action (or use `ir.actions.do_nothing` if available):

```python
return {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': {
        'title': _('Resultado de Validación'),
        'message': message,
        'sticky': False,
        'type': 'success',
        # Don't include 'next' to keep window open
    }
}
```

### Issue 3: Browser cache shows old JavaScript

**Symptoms:** Error persists after code fix, especially `do_nothing` or `act_window_close` errors.

**Solutions:**
1. Hard refresh: `Ctrl + Shift + R` (not just `Ctrl + F5`)
2. Open DevTools → Application → Clear storage → Clear site data
3. Or use incognito/private window
4. Force asset regeneration: `odoo --dev=all`

## Module Manifest

```python
{
    'name': 'Excel Recipe Import',
    'version': '19.0.2.0.0',
    'external_dependencies': {
        'python': ['pandas', 'openpyxl', 'packaging'],
    },
    'depends': ['base', 'product', 'mrp', 'pos_product_bom'],
}
```

## Installation Requirements

```bash
# Install Python dependencies
pip install --break-system-packages pandas openpyxl>=3.1.5 packaging

# Update module
odoo -c /etc/odoo/odoo.conf -d <database> -u excel_recipe_import --stop-after-init
```

## Validated

2026-07-02 on Odoo 19 Community Edition with modules: `mrp`, `pos_product_bom`, `excel_recipe_import`

**Module location:** `/opt/odoo/odoo8083/addons/excel_recipe_import/`
