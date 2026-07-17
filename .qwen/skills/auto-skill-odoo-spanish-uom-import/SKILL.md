---
name: Odoo Spanish UoM Import Fix
description: Fix unit of measure matching issues when importing Spanish data into Odoo 19 due to translated JSON field storage - includes reusable module approach with numeric ID handling
source: auto-skill
extracted_at: '2026-07-02T13:14:20.028Z'
---

## Problem

When importing product data with Spanish unit of measure names (e.g., "g", "Unidades", "kg") into Odoo 19, the import fails with errors like:

```
No se encontraron registros que coincidan con el siguiente nombre en el campo Unidad: g
```

Or SQL errors:
```
ERROR: null value in column "uom_id" of relation "product_template" violates not-null constraint
```

## Root Cause

Odoo 19 stores translated fields (like `uom.uom.name`) as JSON in the database:
```json
{'en_US': 'Units', 'es_419': 'Unidades'}
```

The standard Odoo import (`base_import`) and ORM search methods using `[('name', '=ilike', 'g')]` don't properly match against JSON fields, causing UoM lookups to fail and resulting in NULL values for the required `uom_id` field.

### Common Error

```
ERROR: null value in column "uom_id" of relation "product_template" violates not-null constraint
DETAIL: Failing row contains (8040, 1, null, null, null, null, 2, 2, consu, no, null, ...)
```

This happens when:
1. Excel has empty cells in the "Unidades" column
2. Excel has trailing empty rows
3. UoM name doesn't match any existing record and no fallback is provided

## Solution

### 1. Enhanced UoM Search Method

Create a robust `_get_or_create_uom()` method with multiple search strategies:

```python
def _get_or_create_uom(self, uom_name):
    """Get or create a unit of measure. Handles Spanish and English names.
    
    The uom.uom name field is translated (stored as JSON),
    so we need to search using both English and Spanish terms.
    """
    uom_name = str(uom_name).strip()
    if not uom_name or uom_name.lower() in ['nan', 'none', '']:
        uom_name = 'Unidades'

    uom_name_lower = uom_name.lower()

    # Spanish/English mappings to canonical forms that exist in DB
    mapping = {
        'mililitro': 'ml', 'mililitros': 'ml', 'ml': 'ml',
        'gramo': 'g', 'gramos': 'g', 'gr': 'g',
        'unidades': 'Unidades', 'unidad': 'Unidades', 'units': 'Unidades', 'u': 'Unidades',
        'kilo': 'kg', 'kilos': 'kg', 'kg': 'kg',
        'litro': 'L', 'litros': 'L', 'l': 'L',
    }
    search_name = mapping.get(uom_name_lower, uom_name)

    # Strategy 1: Try mapped name with ORM
    uom = self.env['uom.uom'].search([('name', '=ilike', search_name)], limit=1)
    
    # Strategy 2: Try original name
    if not uom and uom_name_lower != search_name.lower():
        uom = self.env['uom.uom'].search([('name', '=ilike', uom_name)], limit=1)
    
    # Strategy 3: Try English equivalent
    if not uom:
        english_fallbacks = {'unidades': 'Units', 'unidad': 'Units'}
        if uom_name_lower in english_fallbacks:
            uom = self.env['uom.uom'].search([('name', '=ilike', english_fallbacks[uom_name_lower])], limit=1)
    
    # Strategy 4: SQL-based JSON text search (most reliable)
    if not uom:
        self.env.cr.execute(
            "SELECT id FROM uom_uom WHERE name::text ILIKE %s LIMIT 1",
            (f'%{search_name}%',)
        )
        result = self.env.cr.fetchone()
        if result:
            uom = self.env['uom.uom'].browse(result[0])
    
    # Strategy 5: Fallback to default unit reference
    if not uom:
        uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
    
    # Strategy 6: Last resort - get any unit (usually ID 1 = Units/Unidades)
    if not uom:
        uom = self.env['uom.uom'].search([], limit=1, order='id')
    
    return uom
```

### 2. Key Implementation Points

1. **Always return a valid UoM** - Never return `False` or `None` since `uom_id` is a required NOT NULL field in Odoo 19

2. **Use SQL JSON text search as fallback** - Casting JSON to text enables proper ILIKE matching:
   ```python
   self.env.cr.execute(
       "SELECT id FROM uom_uom WHERE name::text ILIKE %s LIMIT 1",
       (f'%{search_name}%',)
   )
   ```

3. **Map Spanish variations to canonical forms** - The database has specific canonical names ('g', 'kg', 'L', 'Unidades'), so normalize input variations

4. **Handle the Excel sheet format explicitly** - For custom import wizards, add dedicated methods for each sheet format:

```python
def _get_or_create_product_from_materia_prima(self, row):
    """Handle specific column format from MATERIA PRIMA sheet."""
    default_code = str(row.get('Referencia interna', '')).strip() if pd.notna(row.get('Referencia interna')) else False
    name = str(row.get('Nombre', '')).strip() if pd.notna(row.get('Nombre')) else False
    uom_name = str(row.get('Unidades', 'Unidades')).strip() if pd.notna(row.get('Unidades')) else 'Unidades'
    
    # ... rest of product creation logic
    uom = self._get_or_create_uom(uom_name)
    # Always use uom.id, never pass uom object directly
    vals = {
        'uom_id': uom.id if uom else False,
        'uom_po_id': uom.id if uom else False,
        # ...
    }
```

## Testing

After implementing:

1. Upgrade the custom import module:
   ```bash
   docker exec -i odoo_web_8083 odoo -c /etc/odoo/odoo.conf -d <database> --update=<module_name> --stop-after-init
   ```

2. Test import with Spanish UoM values: "g", "Unidades", "kg", "ml", "L"

3. Verify products are created with valid `uom_id` values (not NULL)

## Related Files

- `/opt/odoo/odoo8083/addons/excel_recipe_import/wizard/import_recipe_wizard.py`
- `/opt/odoo/odoo8083/addons/uom_spanish_import/` (reusable module)
- Database table: `uom_uom` (name column is JSON)
- Odoo model: `uom.uom`, `product.template`, `product.product`

## Alternative: Reusable Module Approach

For a cleaner, reusable solution that works across all Odoo imports (not just custom wizards), create a dedicated module that intercepts the import flow:

### Module Structure

```
uom_spanish_import/
├── __init__.py
├── __manifest__.py
└── models/
    ├── __init__.py
    └── uom_import_fix.py
```

### Key Implementation

Override `product.template.load()` to fix UoM values before record creation:

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def load(self, fields, data):
        """Override load to fix UoM values before creating records."""
        fixed_data = self._fix_uom_in_load_data(fields, data)
        return super().load(fields, fixed_data)

    def _fix_uom_in_load_data(self, fields, data):
        """Fix UoM values in data before load."""
        uom_id_index = None
        for i, field in enumerate(fields):
            if field == 'uom_id':
                uom_id_index = i
                break
        
        if uom_id_index is None:
            return data
        
        fixed_data = []
        for row in data:
            fixed_row = list(row)
            
            if uom_id_index < len(fixed_row):
                uom_value = fixed_row[uom_id_index]
                if uom_value and not isinstance(uom_value, int):
                    uom_str = str(uom_value).strip()
                    if uom_str and len(uom_str) > 1:  # Skip single chars
                        uom_id = self._find_uom_id_for_load(uom_str)
                        if uom_id:
                            fixed_row[uom_id_index] = uom_id
            
            fixed_data.append(tuple(fixed_row))
        
        return fixed_data

    def _find_uom_id_for_load(self, uom_value):
        """Find UoM ID using SQL JSON text extraction."""
        if not uom_value:
            return False
        
        uom_value = str(uom_value).strip()
        uom_value_lower = uom_value.lower()
        
        # Spanish mapping
        SPANISH_UOM_MAPPING = {
            'gramo': 'g', 'gramos': 'g', 'g': 'g',
            'kilo': 'kg', 'kilos': 'kg', 'kg': 'kg',
            'unidad': 'Unidades', 'unidades': 'Unidades', 'u': 'Unidades',
            'mililitro': 'ml', 'mililitros': 'ml', 'ml': 'ml',
            'litro': 'L', 'litros': 'L', 'l': 'L',
            # ... add more as needed
        }
        
        canonical_name = SPANISH_UOM_MAPPING.get(uom_value_lower, uom_value)
        
        # SQL search with JSON extraction (works for both en_US and es_419)
        self.env.cr.execute("""
            SELECT id FROM uom_uom 
            WHERE name->>'en_US' ILIKE %s 
               OR name->>'es_419' ILIKE %s
            LIMIT 1
        """, (canonical_name, canonical_name))
        
        result = self.env.cr.fetchone()
        if result:
            return result[0]
        
        # Fallback to default UoM
        default_uom = self.env['uom.uom'].search([], limit=1, order='id')
        return default_uom.id if default_uom else False
```

### Module Manifest

```python
{
    'name': 'UoM Spanish Import Fix',
    'version': '19.0.1.0.0',
    'depends': ['product'],
    'data': [],
    'installable': True,
    'auto_install': False,
}
```

### Installation

```bash
# Copy module to addons directory
cp -r uom_spanish_import /path/to/odoo/addons/

# Install via command line
odoo -c /etc/odoo/odoo.conf -d <database> -i uom_spanish_import --stop-after-init

# Or install via UI: Apps → Search "uom_spanish_import" → Install
```

### Benefits of Module Approach

1. **Works with standard Odoo import** - No need for custom import wizards
2. **Reusable across installations** - Copy the module to any Odoo 19 instance
3. **Automatic application** - Fixes UoM matching for ALL product imports
4. **Maintainable** - Centralized UoM mapping in one place
5. **No core overrides** - Uses proper inheritance patterns

### Testing After Installation

1. Go to Products → Products → Import
2. Upload Excel/CSV with Spanish UoM values ("g", "Unidades", "kg", "ml")
3. Map columns (Odoo auto-detects "Unidades" → uom_id)
4. Click Import - UoMs should match correctly
5. Check logs for "Fixed UoM" messages confirming the fix worked

### Logs to Monitor

```
INFO odoo.addons.uom_spanish_import.models.uom_import_fix: Converted data: 349 rows, fields=['default_code', 'name', 'uom_id', ...]
INFO odoo.addons.uom_spanish_import.models.uom_import_fix: Fixing UoM in 349 rows, uom_id_index=2
INFO odoo.addons.uom_spanish_import.models.uom_import_fix: Row 267: Fixed UoM 'ml' -> 12
INFO odoo.addons.uom_spanish_import.models.uom_import_fix: Total UoM fixes: 81
```

If you see "Total UoM fixes: X" where X > 0, the module is working correctly.

## Critical Issue: Frontend JavaScript Validation

**Problem:** Even with backend module overrides, Odoo's **frontend JavaScript** validates Many2one fields BEFORE sending data to the backend. This causes false errors like:

```
No se encontraron registros que coincidan con el siguiente nombre en el campo Unidad:
    15 en varias filas
    12 en varias filas
    1 en varias filas
```

**Why this happens:**
1. User uploads CSV with text values ("g", "ml", "Unidades")
2. Odoo frontend sends preview request to backend
3. Backend converts text → IDs (g→15, ml→12, Unidades→1)
4. Frontend receives IDs but displays them as "names" in error message
5. User sees error BEFORE actual import runs

**Root cause:** The validation happens in `/usr/lib/python3/dist-packages/odoo/addons/base_import/static/src/import_data_column_error/import_data_column_error.xml`

## Workaround: Pre-convert CSV to Numeric IDs

The most reliable solution is to **pre-convert the CSV file** to use numeric IDs instead of text names:

### Python Script: fix_uom_csv.py

```python
#!/usr/bin/env python3
import csv
import sys

UOM_MAPPING = {
    'g': '15',
    'ml': '12',
    'Unidades': '1',
    'kg': '16',
    'L': '13',
}

def fix_uom_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        fieldnames = reader.fieldnames
        
        if 'Unidades' not in fieldnames:
            print(f"Error: Column 'Unidades' not found. Available: {fieldnames}")
            return False
        
        rows = list(reader)
    
    converted = 0
    for row in rows:
        old_value = row['Unidades'].strip() if row['Unidades'] else ''
        if old_value in UOM_MAPPING:
            row['Unidades'] = UOM_MAPPING[old_value]
            converted += 1
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Processed: {len(rows)} rows, Converted: {converted} rows")
    return True

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'products.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'products_fixed.csv'
    fix_uom_csv(input_file, output_file)
```

### Usage

```bash
python3 fix_uom_csv.py materia_prima.csv materia_prima_fixed.csv
```

Then import `materia_prima_fixed.csv` in Odoo - it will work without errors.

**Why this works:** Odoo treats numeric CSV values as Many2one **IDs** directly, bypassing name-based validation entirely.

## Module Enhancement: Override _convert_import_data

For a backend-only solution, override `_convert_import_data` to convert numeric strings to integers:

```python
def _convert_import_data(self, fields, options):
    """Convert UoM numeric strings to integers for Many2one handling."""
    data, import_fields = super()._convert_import_data(fields, options)
    
    uom_id_index = None
    for i, field in enumerate(import_fields):
        if field == 'uom_id':
            uom_id_index = i
            break
    
    if uom_id_index is None:
        return data, import_fields
    
    converted_data = []
    for row in data:
        converted_row = list(row)
        uom_value = converted_row[uom_id_index] if uom_id_index < len(row) else None
        
        # Convert numeric strings to integers
        if isinstance(uom_value, str) and uom_value.strip().isdigit():
            converted_row[uom_id_index] = int(uom_value.strip())
        
        converted_data.append(converted_row)
    
    return converted_data, import_fields
```

## Key Takeaways

1. **Frontend validation is the real blocker** - Backend fixes alone may not prevent error messages
2. **Numeric IDs bypass validation** - Converting CSV to use IDs (1, 12, 15) instead of names ("Unidades", "ml", "g") is the most reliable approach
3. **Module approach still helps** - Even if frontend shows warnings, backend ensures data integrity
4. **Best practice:** Use both approaches - pre-convert CSV AND have module as safety net

## Troubleshooting: Company Access Error

If users see "Forbidden - Access to unauthorized or invalid companies" after password change:

### Check User's Company Assignments

```sql
-- Check user's default company and allowed companies
SELECT id, login, company_id FROM res_users WHERE login = 'user@example.com';

-- Check company-user relationships
SELECT * FROM res_company_users_rel WHERE user_id = <user_id>;

-- Check company status
SELECT id, name, active FROM res_company;
```

### Fix Company Access

```sql
-- Reactivate inactive company
UPDATE res_company SET active = true WHERE id = <company_id>;

-- Add company to user's allowed list
INSERT INTO res_company_users_rel (user_id, company_id) VALUES (<user_id>, <company_id>) ON CONFLICT DO NOTHING;
```

### Common Issue

After password change, session may retain old company permissions. Solution:
1. Clear browser cookies for the Odoo domain
2. Force reload: `Ctrl + F5` (or `Cmd + Shift + R` on Mac)
3. Or use incognito/private window to test
4. Ensure user has entry in `res_company_users_rel` for their default company

## Module Enhancement: Override parse_preview

To fix UoM values in the preview (before validation), override `parse_preview`:

```python
def parse_preview(self, options, count=10):
    """Override to fix UoM values in preview data."""
    result = super().parse_preview(options, count=count)

    if result and 'data' in result and 'fields' in result:
        fields = result['fields']
        uom_id_index = None
        for i, field in enumerate(fields):
            if field == 'uom_id':
                uom_id_index = i
                break

        if uom_id_index is not None:
            fixed_data = []
            for row in result['data']:
                fixed_row = list(row)
                uom_value = fixed_row[uom_id_index] if uom_id_index < len(fixed_row) else None
                uom_id = self._find_uom_id(uom_value, required=True)
                if uom_id and uom_id != uom_value:
                    fixed_row[uom_id_index] = uom_id
                fixed_data.append(fixed_row)
            result['data'] = fixed_data

    return result
```

**Note:** This may not fully prevent frontend validation errors because Odoo's JavaScript validates Many2one fields independently. The most reliable solution remains pre-converting the CSV to numeric IDs.

## Complete Module Implementation (Odoo 19 CE)

### Full Module Structure

```
uom_spanish_import/
├── __init__.py                 # from . import models
├── __manifest__.py
└── models/
    ├── __init__.py             # from . import uom_import_fix
    └── uom_import_fix.py
```

### Key Features

1. **Override `_convert_import_data`** - Converts Spanish names to technical values BEFORE validation
2. **UoM mapping** - `Unidades` → ID 1, `g` → ID 15, `ml` → ID 12
3. **Product type mapping** - `Almacenable` → `product`, `Consumible` → `consu`, `Servicio` → `service`

### Complete uom_import_fix.py

```python
# -*- coding: utf-8 -*-
from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)

SPANISH_UOM_TO_ID = {
    'unidades': 1, 'unidad': 1, 'uds': 1, 'ud': 1, 'units': 1,
    'g': 15, 'gramo': 15, 'gramos': 15,
    'ml': 12, 'mililitro': 12, 'mililitros': 12,
    'kg': 16, 'kilogramo': 16, 'kilogramos': 16,
    'l': 13, 'litro': 13, 'litros': 13,
}

SPANISH_PRODUCT_TYPE = {
    'almacenable': 'product', 'producto almacenable': 'product', 'producto': 'product',
    'consumible': 'consu', 'consumo': 'consu',
    'servicio': 'service', 'servicios': 'service',
}

class BaseImport(models.TransientModel):
    _inherit = 'base_import.import'

    def _convert_import_data(self, fields, options):
        """Convert Spanish names to technical values before validation."""
        data, import_fields = super()._convert_import_data(fields, options)

        # Find field indices
        uom_id_index = type_index = None
        for i, field in enumerate(import_fields):
            if field == 'uom_id': uom_id_index = i
            elif field == 'type': type_index = i

        if uom_id_index is None and type_index is None:
            return data, import_fields

        converted_data = []
        for row_idx, row in enumerate(data):
            converted_row = list(row)

            # Convert UoM
            if uom_id_index is not None and uom_id_index < len(converted_row):
                uom_value = converted_row[uom_id_index]
                converted_id = self._get_uom_id(uom_value)
                if converted_id:
                    converted_row[uom_id_index] = converted_id

            # Convert product type
            if type_index is not None and type_index < len(converted_row):
                type_value = converted_row[type_index]
                converted_type = self._get_product_type(type_value)
                if converted_type:
                    converted_row[type_index] = converted_type

            converted_data.append(converted_row)

        return converted_data, import_fields

    def _get_uom_id(self, uom_value):
        """Get UoM ID from Spanish/English name."""
        if isinstance(uom_value, int): return uom_value
        if not uom_value: return None

        uom_str = str(uom_value).strip().lower()
        if uom_str.isdigit(): return int(uom_str)
        if uom_str in SPANISH_UOM_TO_ID: return SPANISH_UOM_TO_ID[uom_str]

        # Search in database
        self.env.cr.execute("""
            SELECT id FROM uom_uom
            WHERE name->>'es_419' ILIKE %s OR name->>'en_US' ILIKE %s
            LIMIT 1
        """, (uom_str, uom_str))
        result = self.env.cr.fetchone()
        return result[0] if result else None

    def _get_product_type(self, type_value):
        """Get product type technical value from Spanish name."""
        if not type_value: return None
        type_str = str(type_value).strip().lower()
        if type_str in ('product', 'consu', 'service'): return type_str
        return SPANISH_PRODUCT_TYPE.get(type_str)
```

### Critical: addons_path Configuration

The module must be in a directory listed in `addons_path`:

```ini
# /path/to/odoo.conf
addons_path = /mnt/extra-addons,/mnt/extra-addons-customize,/opt/odoo/odoo8083/addons
```

**Common issue:** Module files exist but Odoo doesn't load them because the path isn't in `addons_path`.

**Verify:** After restart, check logs for module loading:
```bash
docker compose logs web8084 | grep "uom_spanish_import"
```

If nothing appears, the path isn't configured correctly.

### Installation Steps

1. **Update addons_path** in odoo.conf
2. **Restart Odoo:** `docker compose restart web8084`
3. **Install module via UI:** Ajustes → Técnico → Módulos → Buscar "uom_spanish" → Instalar
4. **Or via command line:**
   ```bash
   odoo -c /etc/odoo/odoo.conf -d <database> -i uom_spanish_import --stop-after-init
   ```

### Testing

1. Set user language to **Spanish** (Ajustes → Usuario → Idioma)
2. Import CSV with Spanish values:
   - `type`: "Almacenable", "Consumible", "Servicio"
   - `Unidades`: "g", "ml", "Unidades", "kg"
3. Check logs for conversion messages:
   ```
   Row 0: Type 'Almacenable' -> 'product'
   Row 0: UoM 'g' -> ID 15
   ```

## Important Discovery: Odoo 19 Native Spanish Support

**Finding:** Odoo 19 CE **natively supports** Spanish UoM names when the user's interface language is set to Spanish.

**Test results:**
- User language = English → Import may fail with "No matching records found"
- User language = Spanish → Import works without module

**Why:** Odoo uses the user's language context to match translated field values during import validation.

**Implication:** The module is most useful when:
1. Users have mixed language settings (some English, some Spanish)
2. Importing CSVs with non-standard Spanish terms
3. Converting numeric IDs (15, 12, 1) to proper UoM references
4. Supporting product type names in Spanish

## Troubleshooting Checklist

1. **Module not loading:**
   - Check `addons_path` includes module directory
   - Verify module structure (`__init__.py`, `__manifest__.py`)
   - Check logs: `docker compose logs web8084 | grep -E "(uom_spanish|ERROR)"`

2. **Conversions not happening:**
   - Verify module is installed: `SELECT name, state FROM ir_module_module WHERE name = 'uom_spanish_import';`
   - Should show `state = 'installed'`
   - Check logs for `_convert_import_data` calls

3. **Frontend validation errors persist:**
   - This is expected - JavaScript validates before backend receives data
   - Module ensures backend processes correctly even if frontend shows warnings
   - Try "Import anyway" or use numeric IDs in CSV

4. **Company access errors:**
   - User's company may be inactive: `UPDATE res_company SET active = true WHERE id = <id>;`
   - Clear browser cookies and reload
