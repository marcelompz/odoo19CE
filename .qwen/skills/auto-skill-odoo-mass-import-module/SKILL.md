---
name: odoo-mass-import-module
description: Create Odoo modules for mass product import with Excel and manual batch entry, including stock quantity assignment, batch processing optimizations, and fuzzy category matching
source: auto-skill
extracted_at: '2026-06-18T00:12:39.731Z'
---

## Odoo Mass Import Module Creation

When creating Odoo modules for mass data import (products, partners, etc.) with stock/quantity assignment, follow this pattern:

### Performance Optimization - Avoid N+1 Queries

**CRITICAL:** For imports of 100+ records, use batch processing to avoid N+1 query problem:

```python
# ❌ SLOW - 10,000 queries for 10,000 rows
for row in rows:
    existing = self.env['product.product'].search([('barcode', '=', row.barcode)])
    category = self.env['product.category'].search([('name', '=', row.categ_name)])
    product = self.env['product.product'].create(vals)

# ✅ FAST - 3-4 queries total for 10,000 rows
# 1. Batch validate all barcodes
excel_barcodes = [row.barcode for row in rows if row.barcode]
existing_barcodes = set(self.env['product.product'].search(
    [('barcode', 'in', excel_barcodes)]
).mapped('barcode'))

# 2. Batch cache categories
unique_categ_names = set(rows.mapped('categ_name'))
categories_cache = {name: self.env['product.category'].search([('name', '=', name)], limit=1)
                    for name in unique_categ_names if name}

# 3. Batch create all products
product_vals_list = [build_vals(row) for row in valid_rows]
created_products = self.env['product.product'].create(product_vals_list)

# 4. Batch create inventory adjustments
quant_vals_list = [{'product_id': p.id, 'location_id': loc.id, 'inventory_quantity': qty}
                   for p, qty in products_to_quant]
quants = self.env['stock.quant'].with_context(inventory_mode=True).create(quant_vals_list)
for quant in quants:
    quant.action_apply_inventory()
```

**Expected Performance:**
- N+1 approach: ~30-60 seconds for 1,000 products
- Batch approach: ~2-5 seconds for 1,000 products

### Fuzzy Match for Categories (Avoid Duplicates)

**Problem:** User imports "Artículos de electricidad" but "Articulos de Electricidad" already exists → creates duplicate.

**Solution:** Implement fuzzy matching with normalization:

```python
import unicodedata

def normalize_text(text):
    """
    Normalize text: lowercase, remove accents, strip extra spaces.
    Example: "Artículos de Electricidad" → "articulos de electricidad"
    """
    if not text:
        return ''
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = ' '.join(text.split())
    return text


def find_best_match_category(category_name, categories_env):
    """
    Find existing category with similar name (fuzzy match).
    Returns category or None.
    
    Strategies (in order):
    1. Exact match (normalized)
    2. Containment (one contains the other)
    3. Word similarity (≥80% common words)
    """
    if not category_name:
        return None
    
    normalized_input = normalize_text(category_name)
    all_categories = categories_env.search([])
    
    # 1. Exact normalized match
    for categ in all_categories:
        if normalize_text(categ.name) == normalized_input:
            return categ
    
    # 2. Containment match
    for categ in all_categories:
        normalized_categ = normalize_text(categ.name)
        if normalized_categ in normalized_input or normalized_input in normalized_categ:
            return categ
    
    # 3. Word similarity (80% threshold)
    input_words = set(normalized_input.split())
    for categ in all_categories:
        normalized_categ = normalize_text(categ.name)
        categ_words = set(normalized_categ.split())
        
        if not categ_words or not input_words:
            continue
        
        common_words = input_words & categ_words
        total_words = input_words | categ_words
        
        if len(total_words) > 0:
            similarity = len(common_words) / len(total_words)
            if similarity >= 0.8:
                return categ
    
    return None
```

**Usage in import:**

```python
# Before creating category, check for fuzzy match
category = find_best_match_category(categ_name, self.env['product.category'])

if category:
    # Reuse existing (avoid duplicate)
    categories_matched.append((categ_name, category.name))
else:
    # Create new
    category = self.env['product.category'].create({'name': categ_name})
    categories_created.append(categ_name)

categories_cache[categ_name] = category
```

**Match Examples:**

| Excel Input | Existing Category | Match Reason |
|-------------|-------------------|--------------|
| `Artículos de electricidad` | `Articulos de Electricidad` | Exact normalized (accents ignored) |
| `Hogar y Jardín` | `Hogar` | Containment |
| `Deportes Acuáticos` | `Deportes` | 80% word similarity |
| `Electrónica Pro` | `Electrónica` | Containment |
| `Nueva Cat XYZ` | (none) | No match → Create new |

**Post-import notification:**

```python
message = f"Se crearon {count} productos exitosamente."

if categories_matched:
    matched_list = ', '.join([f'"{orig}" → "{match}"' for orig, match in categories_matched])
    message += f'\n\n📁 Categorías reutilizadas: {matched_list}'

if categories_created:
    message += f'\n📁 Categorías creadas: {", ".join(categories_created)}'
```

### Module Structure

```
module_name/
├── __init__.py
├── __manifest__.py
├── data/
│   └── sequence.xml
├── i18n/
│   └── es.po
├── models/
│   ├── __init__.py
│   ├── import_wizard.py       # TransientModel for Excel import
│   └── batch_import.py        # Model for manual batch entry
├── security/
│   └── ir.model.access.csv
└── views/
    ├── wizard_views.xml
    ├── batch_views.xml
    └── menu_views.xml
```

### Key Implementation Patterns

#### 1. Wizard Model (Excel Import)

```python
class ProductMassImportWizard(models.TransientModel):
    _name = 'product.mass.import.wizard'
    
    file_data = fields.Binary(string='Archivo Excel (.xlsx)', required=True)
    location_id = fields.Many2one('stock.location', required=True, 
                                   domain=[('usage', '=', 'internal')])
    state = fields.Selection([('draft', 'Borrador'), ('preview', 'Vista Previa'), ('done', 'Completado')])
    preview_ids = fields.One2many('product.mass.import.preview', 'wizard_id')
    
    def action_download_template(self):
        """Generate Excel template with openpyxl"""
        wb = openpyxl.Workbook()
        ws = wb.active
        # Add headers and example row
        # Return as base64 download
        
    def action_parse_excel(self):
        """Parse Excel and populate preview with validation"""
        data = base64.b64decode(self.file_data)
        wb = openpyxl.load_workbook(filename=io.BytesIO(data), data_only=True)
        # Parse rows, validate each, store in preview_ids
        # Return notification with valid/invalid counts
        
    def action_confirm_import(self):
        """Create products and apply inventory"""
        for preview in valid_products:
            product = self.env['product.product'].create(product_vals)
            if preview.qty_on_hand > 0:
                products_to_quant.append((product, preview.qty_on_hand))
        
        # Apply stock via stock.quant with inventory_mode
        for product, qty in products_to_quant:
            self.env['stock.quant'].with_context(inventory_mode=True).create({
                'product_id': product.id,
                'location_id': self.location_id.id,
                'inventory_quantity': qty,
            }).action_apply_inventory()
```

#### 2. Batch Import Model (Manual Entry in Odoo)

```python
class ProductBatchImport(models.Model):
    _name = 'product.batch.import'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(default='Nuevo')
    line_ids = fields.One2many('product.batch.import.line', 'batch_id')
    state = fields.Selection([('draft', 'Borrador'), ('validated', 'Validado'), ('done', 'Completado')])
    
    def action_validate(self):
        for line in self.line_ids:
            line.action_validate()  # Triggers _compute_validation
        self.state = 'validated'
    
    def action_confirm(self):
        # Same creation logic as wizard
        # Post message with created count
```

#### 3. Line Validation (Computed Fields)

```python
class ProductBatchImportLine(models.Model):
    _name = 'product.batch.import.line'
    
    is_valid = fields.Boolean(compute='_compute_validation', store=True)
    error_message = fields.Text(compute='_compute_validation', store=True)
    
    @api.depends('name', 'barcode', 'list_price', 'standard_price', 'qty_on_hand')
    def _compute_validation(self):
        for line in self:
            error_msgs = []
            if not line.name:
                error_msgs.append("Nombre requerido")
            if line.barcode:
                existing = self.env['product.product'].search([('barcode', '=', line.barcode)], limit=1)
                if existing:
                    error_msgs.append(f"Código duplicado: {existing.name}")
            if line.list_price < 0:
                error_msgs.append("Precio negativo")
            line.error_message = ', '.join(error_msgs) if error_msgs else False
            line.is_valid = len(error_msgs) == 0
```

#### 4. Manifest Configuration

```python
{
    'depends': ['product', 'stock', 'point_of_sale'],
    'external_dependencies': {'python': ['openpyxl']},
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/wizard_views.xml',
        'views/batch_views.xml',
        'views/menu_views.xml',
    ],
}
```

#### 5. Sequence Definition

```xml
<record id="seq_product_batch_import" model="ir.sequence">
    <field name="name">Secuencia de Importación en Lote</field>
    <field name="code">product.batch.import</field>
    <field name="prefix">PBI/</field>
    <field name="padding">5</field>
</record>
```

### Critical Odoo 19 Considerations

| Field/Concept | Odoo 19 Value | Notes |
|---------------|---------------|-------|
| Product Type (goods/storable) | `consu` | **CHANGED in Odoo 19**: `consu` = "Goods" (includes storable) |
| Product Type (consumable) | `consu` | Same as storable - both are "Goods" |
| Product Type (service) | `service` | Non-tangible products |
| Product Type (combo) | `combo` | Combined products (new in Odoo 19) |
| POS Category field | `pos_categ_id` | Many2one, not Many2many |
| Stock assignment | `stock.quant` + `inventory_mode=True` | Native API since Odoo 16 |
| List views | `<list>` | Renamed from `<tree>` in Odoo 19 |
| List view reference | `list_view_ref` | Changed from `tree_view_ref` |
| View attrs syntax | `invisible="field != 'value'"` | **CHANGED**: Old `attrs="{'invisible': [...]}"` deprecated |

**Odoo 19 Product Type Note:**

In Odoo 18/19, the `type` field structure changed:

```python
# Odoo 17 and earlier:
type = Selection([('product', 'Storable'), ('consu', 'Consumable'), ('service', 'Service')])

# Odoo 18/19:
type = Selection([('consu', 'Goods'), ('service', 'Service'), ('combo', 'Combo')])
```

The `is_stored` boolean field that existed in intermediate versions was removed. Now:
- **`consu` (Goods)**: Includes both storable and consumable physical products
- **`service`**: Non-tangible services
- **`combo`**: Combined products

The distinction between "storable" and "consumable" is now handled via category configurations and routes, not the `type` field.

**Correct mapping for imports:**

```python
# Map Excel values to Odoo 19 type field
product_type = 'consu'  # Default to "Goods" (includes storable)

if row_type.lower() in ['servicio', 'service']:
    product_type = 'service'
elif row_type.lower() in ['combo']:
    product_type = 'combo'
# 'almacenable', 'storable', 'product', 'consumible' → all map to 'consu'
```

### Odoo 19 View Syntax Changes

**One2many field with custom list view:**

```xml
<!-- Odoo 19: Use 'list' not 'tree', and 'list_view_ref' in context -->
<field name="preview_ids" 
       context="{'list_view_ref': 'module.view_id'}" 
       mode="list"/>
```

**List view definition:**

```xml
<record id="my_view_list" model="ir.ui.view">
    <field name="model">my.model</field>
    <field name="arch" type="xml">
        <list create="0" delete="0" decoration-danger="error_field != False">
            <!-- fields -->
        </list>
    </field>
</record>
```

### Installing Python Dependencies in Docker

**Manifest validation only (doesn't auto-install):**

```python
'external_dependencies': {'python': ['openpyxl']},
```

This only validates the package exists at install time - it does NOT install it.

**For Docker containers with externally-managed Python (Debian/PEP 668):**

```bash
docker exec -it <container> pip install --break-system-packages openpyxl
docker restart <container>
```

The `--break-system-packages` flag is needed because modern Debian-based containers use externally-managed Python environments.

### View Loading Order

XML files in `data` are loaded sequentially. If using view inheritance (`inherit_id`), ensure the parent view is defined in a file that loads **before** the child view, or define both views in the same file with the parent first.

**Safe pattern:** Define custom list view and wizard form in the same file, with list view first:

```xml
<odoo>
    <!-- 1. Define list view for preview model -->
    <record id="preview_view_list" model="ir.ui.view">
        <field name="model">product.mass.import.preview</field>
        ...
    </record>

    <!-- 2. Define wizard form that references it -->
    <record id="wizard_view_form" model="ir.ui.view">
        <field name="model">product.mass.import.wizard</field>
        ...
        <field name="preview_ids" context="{'list_view_ref': 'module.preview_view_list'}" mode="list"/>
    </record>
</odoo>
```

### Validation Checklist

- [ ] Barcode uniqueness check against database
- [ ] **Internal duplicate check** (same barcode appears twice in Excel file - use `seen_barcodes_in_file` set)
- [ ] Required field validation (name, reference)
- [ ] Negative value prevention (prices, quantities)
- [ ] Preview state before confirming
- [ ] Error messages displayed in list view (decoration-danger)
- [ ] **Category fuzzy match** (avoid duplicates due to typos/accents)
- [ ] Category auto-creation if no match found
- [ ] Stock only applied when qty > 0
- [ ] Security access for stock user and manager groups
- [ ] **Batch processing for 1000+ imports**
- [ ] **Post-import notification** with categories matched/created details

### Menu Placement

For inventory-related imports, place under `stock.menu_stock_root`:

```xml
<menuitem id="menu_product_mass_import_root"
          name="Importación Masiva"
          parent="stock.menu_stock_root"
          sequence="50"/>
```
