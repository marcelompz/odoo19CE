# Auditoría del Módulo `product_mass_import`

He analizado el código fuente de tu módulo `product_mass_import` (específicamente `product_batch_import.py` y `product_mass_import_wizard.py`). Aunque la lógica funcional es correcta y cubre muy bien el flujo de trabajo deseado, existen áreas críticas de mejora, especialmente en **Rendimiento** y **Compatibilidad**.

## 1. Problemas Críticos de Rendimiento (N+1 Queries)

El problema más importante del módulo es cómo se crean los productos y cómo se buscan las categorías. Actualmente, el código procesa los registros **uno por uno dentro de un bucle `for`**. Esto se conoce como el problema de consultas N+1 y causará que el sistema se congele o lance errores de "Time Out" si intentas importar miles de productos.

**Dónde ocurre:**
```python
# En action_confirm y action_confirm_import:
for preview in valid_products:
    category = self.env['product.category'].search([('name', '=', preview.categ_name)], limit=1) # Consulta SQL por iteración
    product = self.env['product.product'].create(product_vals) # Inserción SQL por iteración
```

**Solución Recomendada (Batching):**
En Odoo, las operaciones deben hacerse en bloque (batch).
1. **Precargar Categorías:** En lugar de hacer un `search` por cada fila, haz un único `search` antes del bucle y guarda los resultados en un diccionario de Python.
2. **Creación Masiva:** Acumula todos los diccionarios `product_vals` en una lista, y al final del bucle ejecuta un único `self.env['product.product'].create(lista_de_valores)`.
3. **Inventario Masivo:** Lo mismo aplica para la creación de los `stock.quant`. Crea todos los quants en un solo `.create()` y luego aplícalos.

## 2. Rendimiento en el Análisis del Excel (Vista Previa)

En la función `action_parse_excel`, al leer el archivo fila por fila, el código hace lo siguiente para validar los códigos de barras:
```python
if barcode:
    existing = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
```
Si tu Excel tiene 10,000 filas, esto disparará **10,000 consultas a la base de datos** solo para mostrar la vista previa, haciendo la carga muy lenta.

**Solución Recomendada:**
Extrae todos los códigos de barras del archivo Excel en un paso previo, haz una sola consulta SQL para obtener los que ya existen en Odoo, y luego haz la comparación en memoria:
```python
excel_barcodes = [str(row[3]).strip() for row in rows if len(row) > 3 and row[3]]
existing_barcodes = self.env['product.product'].search([('barcode', 'in', excel_barcodes)]).mapped('barcode')
```

## 3. Compatibilidad con Odoo 18 / 19 (Tipos de Producto)

En las versiones recientes de Odoo (18 y 19), la estructura del campo `type` (Almacenable, Consumible, Servicio) ha sufrido modificaciones importantes. El valor `'product'` para productos almacenables fue reemplazado a favor de usar un campo booleano `is_storable = True` y dejando `type` para consumibles y servicios.

Asegúrate de revisar cómo está definida la estructura de `product.template` en tu entorno específico de Odoo 19 para evitar que los productos importados queden configurados incorrectamente como "Consumibles" por defecto debido a un mapeo inválido en:
```python
'type': preview.product_type,
```

## 4. Redundancia de Dependencias

En `product_mass_import_wizard.py` utilizas un bloque `try-except` para importar `openpyxl`, y lanzas un `UserError` si no existe. 
Sin embargo, en tu `__manifest__.py` ya declaraste `'external_dependencies': {'python': ['openpyxl']}`. 
Esto hace que el `try-except` sea innecesario, porque Odoo **nunca** permitirá instalar o arrancar el módulo si `openpyxl` no está instalado a nivel de servidor. Puedes simplificar el código eliminando esas comprobaciones manuales.

## 5. Falta de Validación de Duplicados Internos

El validador de códigos de barras revisa si el código ya existe en la base de datos de Odoo, pero **no revisa si hay duplicados dentro del mismo archivo Excel**. Si el Excel tiene dos filas con el mismo código de barras, ambas pasarán como válidas en la vista previa, pero fallarán abruptamente al momento de la creación. Se debe agregar un chequeo contra una lista en memoria de códigos ya leídos en el mismo archivo.

---
**Conclusión:**
El módulo está muy bien estructurado a nivel de usabilidad y vistas, pero su rendimiento actual es de "prototipo". Para que sea un módulo **robusto de importación masiva** (Mass Import), es imperativo refactorizar los bucles para utilizar técnicas de carga en memoria e inserciones SQL en lote (Batch Processing).
