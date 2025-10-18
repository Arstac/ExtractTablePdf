# Cómo ejecutar el flujo completo

El flujo completo ya está implementado y listo para usar. Sigue estos pasos:

## Paso 1: Extraer secciones del PDF

```bash
python extract_section.py
```

Esto genera las secciones en `output_sections/`

## Paso 2: Procesar la tabla y generar CSV/Excel

```bash
python process_table.py
```

Esto:
1. Detecta automáticamente el encabezado
2. Usa la nueva lógica de matching exacto para encontrar columnas
3. Divide cada fila en columnas
4. Extrae el texto con OCR
5. Genera:
   - `table_data.csv` - Datos en CSV
   - `table_data.xlsx` - Datos en Excel
   - `output_sections/debug_header/` - Imágenes de debug
   - `output_sections/debug_columns/` - Columnas individuales

## Para probar solo la detección de columnas:

```bash
python test_single_page.py
```

Esto probará solo con `page_7_section_2.png` y generará:
- `test_single_page_result.png` - Visualización con columnas marcadas
- Verificación con valores esperados

## Archivos clave:

- `process_table.py` - Script principal (**USA LA NUEVA LÓGICA**)
- `extract_section.py` - Extracción de secciones del PDF
- `test_single_page.py` - Test rápido con un archivo
- `requirements.txt` - Dependencias

## ¿Qué hace la nueva lógica?

1. **Matching exacto** de palabras (no subcadenas)
2. **Busca todas las combinaciones** de bloques que contengan TODAS las palabras del título
3. **Detecta grupos verticales y horizontales** automáticamente
4. **Selecciona el mejor grupo** (más compacto y más a la izquierda)
5. **Excluye bloques usados** para evitar duplicados

¡TODO ESTÁ LISTO PARA USAR!
