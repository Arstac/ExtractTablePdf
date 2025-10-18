# Cómo ejecutar el flujo completo

El flujo completo está implementado y listo para usar. Sigue estos pasos:

## Opción 1: Ejecutar todo automáticamente (RECOMENDADO)

```bash
python main.py
```

Este script ejecuta todo el pipeline de forma automática:
1. Extrae las secciones del PDF
2. Procesa la tabla y genera CSV/Excel
3. Crea visualizaciones de debug

## Opción 2: Ejecutar paso a paso

### Paso 1: Extraer secciones del PDF

```bash
python src/extract_section.py
```

Esto genera las secciones en `output/sections/`

### Paso 2: Procesar la tabla y generar CSV/Excel

```bash
python src/process_table.py
```

Esto:
1. Detecta automáticamente el encabezado
2. Usa la lógica de matching exacto para encontrar columnas
3. Divide cada fila en columnas
4. Extrae el texto con OCR
5. Genera:
   - `output/table_data.csv` - Datos en CSV
   - `output/table_data.xlsx` - Datos en Excel
   - `output/sections/debug_header/` - Imágenes de debug
   - `output/sections/debug_columns/` - Columnas individuales
   - `output/sections/visualizations/` - Visualizaciones

## Para probar solo la detección de columnas:

```bash
python tests/test_single_page.py
```

Esto probará solo con una página de ejemplo y generará:
- `test_single_page_result.png` - Visualización con columnas marcadas
- Verificación con valores esperados

## Archivos clave:

- `main.py` - **SCRIPT PRINCIPAL** (ejecuta todo el flujo)
- `src/extract_section.py` - Extracción de secciones del PDF
- `src/process_table.py` - Procesamiento de tabla (USA LA NUEVA LÓGICA)
- `tests/test_single_page.py` - Test rápido con un archivo
- `requirements.txt` - Dependencias

## ¿Qué hace la nueva lógica?

1. **Matching exacto** de palabras (no subcadenas)
2. **Busca todas las combinaciones** de bloques que contengan TODAS las palabras del título
3. **Detecta grupos verticales y horizontales** automáticamente
4. **Selecciona el mejor grupo** (más compacto y más a la izquierda)
5. **Excluye bloques usados** para evitar duplicados

## Estructura de salida

```
output/
├── sections/                      # Secciones extraídas del PDF
│   ├── page_X_section_Y.png      # Imágenes de cada sección
│   ├── debug/                     # Debug de detección de líneas
│   ├── debug_header/              # Debug de detección de encabezado
│   ├── debug_columns/             # Columnas individuales extraídas
│   └── visualizations/            # Visualizaciones con columnas marcadas
├── table_data.csv                 # Datos extraídos (CSV)
└── table_data.xlsx                # Datos extraídos (Excel)
```

## Troubleshooting

### Si el PDF no se encuentra:
Coloca tu PDF en `data/documento.pdf` o actualiza la ruta en `main.py`

### Si las columnas no se detectan correctamente:
1. Revisa `output/sections/debug_header/header_detection.png`
2. Verifica que el texto del encabezado sea claro
3. Ajusta los parámetros en `src/process_table.py`

### Si el OCR no funciona bien:
1. Instala los paquetes de idioma de Tesseract (catalán/español)
2. Verifica que las imágenes en `output/sections/` sean claras
3. Ajusta el DPI en `src/extract_section.py` (línea 89)

¡TODO ESTÁ LISTO PARA USAR!
