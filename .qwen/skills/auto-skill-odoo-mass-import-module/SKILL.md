---
name: odoo-mass-import-module
description: Create Odoo modules for mass product import with Excel and manual batch entry, including stock quantity assignment
source: auto-skill
extracted_at: '2026-06-17T17:30:44.292Z'
---

## Odoo Mass Import Module Creation

When creating Odoo modules for mass data import (products, partners, etc.) with stock/quantity assignment, follow this pattern:

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
| Product Type (storable) | `product` | Not `consu` - that's for consumables |
| Product Type (consumable) | `consu` | |
| Product Type (service) | `service` | |
| POS Category field | `pos_categ_id` | Many2one, not Many2many |
| Stock assignment | `stock.quant` + `inventory_mode=True` | Native API since Odoo 16 |

### Validation Checklist

- [ ] Barcode uniqueness check before creation
- [ ] Required field validation (name, prices)
- [ ] Negative value prevention
- [ ] Preview state before confirming
- [ ] Error messages displayed in tree view (decoration-danger)
- [ ] Category auto-creation if not exists
- [ ] Stock only applied when qty > 0
- [ ] Security access for stock user and manager groups

### Menu Placement

For inventory-related imports, place under `stock.menu_stock_root`:

```xml
<menuitem id="menu_product_mass_import_root"
          name="Importación Masiva"
          parent="stock.menu_stock_root"
          sequence="50"/>
```
