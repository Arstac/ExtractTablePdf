# Visualizaciones de Columnas

## Descripción

El script `process_table.py` ahora incluye una funcionalidad opcional para generar imágenes de visualización que muestran cómo se dividen las columnas en cada fila de la tabla.

## Cómo Activar/Desactivar

### Método 1: Modificar process_table.py directamente

En la función `main()` del archivo `process_table.py`, cambia el parámetro `generate_visualizations`:

```python
def main():
    processor = TableProcessor(
        sections_dir="output_sections",
        output_file="table_data.csv",
        generate_visualizations=True  # True = ACTIVAR, False = DESACTIVAR
    )

    df = processor.process_all_sections(debug=True)
```

### Método 2: Usar desde código Python

```python
from process_table import TableProcessor

# CON visualizaciones
processor = TableProcessor(
    sections_dir="output_sections",
    output_file="table_data.csv",
    generate_visualizations=True  # ← Activar
)

# SIN visualizaciones (más rápido)
processor = TableProcessor(
    sections_dir="output_sections",
    output_file="table_data.csv",
    generate_visualizations=False  # ← Desactivar
)

df = processor.process_all_sections(debug=False)
```

## Tipos de Imágenes Generadas

Cuando `generate_visualizations=True`, se generan **2 imágenes por cada fila procesada**:

### 1. Imagen con Overlay (`*_columns_overlay.png`)
- Rectángulos de colores semi-transparentes sobre cada columna
- Útil para ver claramente la división de columnas
- Con etiquetas del nombre de cada columna

### 2. Imagen con Bordes (`*_columns_borders.png`)
- Solo los bordes de las columnas (sin relleno)
- Más fácil de leer el texto original
- Con etiquetas del nombre de cada columna

## Colores de Columnas

Cada columna se identifica con un color diferente:

1. **tipus_criterio** - Verde
2. **nom_criteri** - Azul
3. **descripcio** - Rojo
4. **on_incloure** - Cyan
5. **doc_a_verificar_adj** - Magenta
6. **doc_a_verificar_exec** - Amarillo
7. **condicionants** - Rosa

## Ubicación de las Imágenes

Las imágenes se guardan en:

```
output_sections/
└── visualizations/
    ├── page_6_section_3_columns_overlay.png
    ├── page_6_section_3_columns_borders.png
    ├── page_6_section_4_columns_overlay.png
    ├── page_6_section_4_columns_borders.png
    └── ... (2 imágenes por cada sección procesada)
```

## Ejemplo de Uso

Ver el archivo `example_usage.py` para ejemplos completos de uso.

```bash
# Ejecutar ejemplo con visualizaciones
python example_usage.py
```

## Impacto en el Rendimiento

- **Con visualizaciones**: El proceso tarda aproximadamente un 20-30% más
- **Sin visualizaciones**: Proceso más rápido

**Recomendación**: Activar solo cuando necesites verificar la detección de columnas. Para procesamiento masivo o en producción, desactivar.

## Casos de Uso

### ✓ Cuándo activar visualizaciones:

- Primera vez que procesas un nuevo tipo de documento
- Verificar que la detección de columnas es correcta
- Debugging de problemas de OCR
- Documentación del proceso

### ✓ Cuándo desactivar visualizaciones:

- Procesamiento en batch de muchos documentos
- Cuando ya verificaste que funciona correctamente
- En entornos de producción automatizados
- Para ahorrar espacio en disco

## Solución de Problemas

### Las columnas no se ven bien alineadas

1. Verificar que el encabezado fue detectado correctamente
2. Revisar las imágenes en `output_sections/debug_header/`
3. Ajustar el valor `HEADER_Y_MAX` en `detect_header_columns()` si es necesario

### No se generan las imágenes

1. Verificar que `generate_visualizations=True`
2. Comprobar permisos de escritura en `output_sections/visualizations/`
3. Verificar que OpenCV está instalado correctamente: `pip install opencv-python`
