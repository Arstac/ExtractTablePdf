# PDF Table Extractor API - Guía de Uso

API profesional para extraer tablas de PDFs multipágina con encabezados y pies de página usando Camelot.

## Características

- ✅ Extracción de tablas de PDFs multipágina
- ✅ Manejo de encabezados y pies de página repetidos
- ✅ Soporte para tablas con líneas (lattice) y sin líneas (stream)
- ✅ Recorte de márgenes para eliminar encabezados/pies
- ✅ Filtrado por calidad de extracción
- ✅ Exportación a JSON, CSV y Excel
- ✅ Reporte de calidad de tablas detectadas

## Instalación

### 1. Instalar dependencias del sistema

**macOS:**
```bash
brew install ghostscript
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk ghostscript
```

### 2. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

## Iniciar el servidor

```bash
python main.py
```

O usando uvicorn directamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## Endpoints

### 1. GET `/` - Información de la API
```bash
curl http://localhost:8000/
```

### 2. GET `/health` - Estado de la API
```bash
curl http://localhost:8000/health
```

### 3. POST `/extract` - Extraer tablas de PDF

Extrae tablas de un PDF y las devuelve en el formato especificado.

**Parámetros:**
- `file`: Archivo PDF (required)
- `pages`: Páginas a procesar - default: 'all' (ej: '1-10', '1,4-10,20-end')
- `flavor`: Método de extracción - default: 'lattice'
  - `lattice`: Para tablas con líneas divisorias visibles
  - `stream`: Para tablas basadas en espacios en blanco
- `min_accuracy`: Precisión mínima 0-100 - default: 80.0
- `output_format`: Formato de salida - default: 'json'
  - `json`: Retorna JSON con los datos
  - `csv`: Descarga archivo CSV
  - `excel`: Descarga archivo Excel

**Ejemplos:**

```bash
# Extraer todas las páginas en formato JSON
curl -X POST "http://localhost:8000/extract?output_format=json" \
  -F "file=@documento.pdf"

# Extraer páginas 1-5 en formato CSV
curl -X POST "http://localhost:8000/extract?pages=1-5&output_format=csv" \
  -F "file=@documento.pdf" \
  -o tablas.csv

# Extraer con método stream (tablas sin líneas)
curl -X POST "http://localhost:8000/extract?flavor=stream&output_format=excel" \
  -F "file=@documento.pdf" \
  -o tablas.xlsx

# Extraer con precisión mínima del 90%
curl -X POST "http://localhost:8000/extract?min_accuracy=90.0" \
  -F "file=@documento.pdf"
```

**Respuesta JSON:**
```json
{
  "success": true,
  "rows": 150,
  "columns": 5,
  "data": [
    {
      "columna1": "valor1",
      "columna2": "valor2",
      ...
    },
    ...
  ]
}
```

### 4. POST `/extract-with-crop` - Extraer con recorte de márgenes

Recorta los márgenes del PDF (para eliminar encabezados/pies) antes de extraer tablas.

**Parámetros adicionales:**
- `top_margin`: Margen superior en puntos - default: 50
- `bottom_margin`: Margen inferior en puntos - default: 50
- `left_margin`: Margen izquierdo en puntos - default: 30
- `right_margin`: Margen derecho en puntos - default: 30

**Ejemplo:**

```bash
# Recortar 60 puntos arriba/abajo, 40 izquierda/derecha
curl -X POST "http://localhost:8000/extract-with-crop?top_margin=60&bottom_margin=60&left_margin=40&right_margin=40" \
  -F "file=@documento.pdf"
```

**Respuesta JSON:**
```json
{
  "success": true,
  "rows": 150,
  "columns": 5,
  "margins_applied": {
    "top": 60,
    "bottom": 60,
    "left": 40,
    "right": 40
  },
  "data": [...]
}
```

### 5. POST `/quality-report` - Reporte de calidad

Genera un reporte de calidad de todas las tablas detectadas sin extraer los datos.

**Ejemplo:**

```bash
curl -X POST "http://localhost:8000/quality-report?pages=all&flavor=lattice" \
  -F "file=@documento.pdf"
```

**Respuesta:**
```json
{
  "success": true,
  "total_tables": 3,
  "tables": [
    {
      "table_number": 1,
      "page": 1,
      "accuracy": 95.5,
      "whitespace": 15.2,
      "shape": [50, 5],
      "rows": 50,
      "columns": 5
    },
    {
      "table_number": 2,
      "page": 2,
      "accuracy": 88.3,
      "whitespace": 20.1,
      "shape": [45, 4],
      "rows": 45,
      "columns": 4
    },
    ...
  ]
}
```

## Uso desde Python

```python
import requests

# Extraer tablas
with open('documento.pdf', 'rb') as f:
    files = {'file': f}
    params = {
        'pages': '1-10',
        'flavor': 'lattice',
        'min_accuracy': 85.0,
        'output_format': 'json'
    }
    response = requests.post('http://localhost:8000/extract', files=files, params=params)
    data = response.json()
    print(f"Se extrajeron {data['rows']} filas")

# Obtener reporte de calidad
with open('documento.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/quality-report', files=files)
    report = response.json()
    for table in report['tables']:
        print(f"Tabla {table['table_number']}: {table['accuracy']}% precisión")
```

## Tips de uso

### 1. Elegir el método correcto (flavor)

- **lattice**: Usar cuando las tablas tienen líneas/bordes visibles
  - Más preciso y rápido
  - Recomendado como primera opción

- **stream**: Usar cuando las tablas solo tienen espacios en blanco
  - Para tablas sin bordes
  - Puede requerir ajuste de parámetros

### 2. Ajustar la precisión mínima

- `min_accuracy=80`: Balance entre calidad y cantidad de tablas
- `min_accuracy=90`: Solo tablas de alta calidad
- `min_accuracy=70`: Incluir más tablas, menor calidad garantizada

### 3. Recortar márgenes

Si los encabezados/pies interfieren con la extracción:
- Usar `/extract-with-crop`
- Ajustar márgenes hasta obtener buenos resultados
- 1 punto = 1/72 de pulgada (~0.35mm)

### 4. Especificar páginas

```
'all'          # Todas las páginas
'1'            # Solo página 1
'1-5'          # Páginas 1 a 5
'1,3,5'        # Páginas 1, 3 y 5
'1-10,15,20'   # Combinación
'1-10,20-end'  # Hasta el final
```

## Solución de problemas

### Error: "No se encontraron tablas"

1. Verificar que el PDF contenga tablas visibles
2. Probar con `flavor=stream` si usaste `lattice`
3. Reducir `min_accuracy`
4. Usar `/quality-report` para ver qué se detecta

### Tablas mal extraídas

1. Usar `/extract-with-crop` para eliminar encabezados/pies
2. Ajustar los márgenes gradualmente
3. Verificar la calidad con `/quality-report`

### Error de instalación de Ghostscript

Camelot requiere Ghostscript instalado en el sistema:
- macOS: `brew install ghostscript`
- Ubuntu: `sudo apt-get install ghostscript`

## Estructura del proyecto

```
ExtractTablePdf/
├── main.py              # API FastAPI
├── pdf_extractor.py     # Funciones de extracción
├── requirements.txt     # Dependencias
├── USAGE.md            # Esta guía
└── README.md           # Conversación original
```

## Tecnologías utilizadas

- **FastAPI**: Framework web moderno y rápido
- **Camelot**: Biblioteca especializada en extracción de tablas PDF
- **Pandas**: Manipulación de datos tabulares
- **PyPDF2**: Manipulación de archivos PDF
- **OpenCV**: Procesamiento de imágenes (requerido por Camelot)
