# Changelog

## [1.1.0] - 2025-10-18

### REST API con FastAPI

#### Added
- **app.py**: REST API con FastAPI para integración fácil
  - Endpoint `POST /extract` para subir PDF y obtener datos en JSON
  - Endpoint `POST /extract/simple` que devuelve solo el array de datos
  - Endpoint `GET /health` para health check
  - Parámetro `temp` para gestión automática de archivos temporales
  - Documentación interactiva automática (Swagger UI y ReDoc)
  - Logging completo de operaciones
  - Manejo robusto de errores con HTTP status codes apropiados
  - CORS middleware configurado
- **docs/API.md**: Documentación completa de la API REST
  - Ejemplos con curl, Python y JavaScript
  - Guía de despliegue en producción
  - Configuración de Docker
  - Cliente Python de ejemplo
- **examples/test_api.py**: Script de prueba para la API
  - Health check automático
  - Carga y procesamiento de PDF
  - Guardado de resultados en JSON
- **requirements.txt**: Actualizadas dependencias con FastAPI
  - `fastapi==0.104.1`
  - `uvicorn[standard]==0.24.0`
  - `python-multipart==0.0.6`

#### Changed
- **README.md**: Añadida sección de Quick Start con la API REST
- Estructura del proyecto actualizada para incluir `app.py`

#### Features
- **Gestión de archivos temporales**:
  - `temp=true`: Los archivos se borran automáticamente después de procesar
  - `temp=false`: Los archivos se guardan en `output/{session_id}/` para debugging
- **Respuesta JSON estructurada**:
  - `success`: Indicador de éxito
  - `count`: Número de registros extraídos
  - `data`: Array de diccionarios con los datos
  - `session_id`: UUID de la sesión (solo si temp=false)
- **Validaciones**:
  - Validación de tipo de archivo (solo PDF)
  - Validación de datos extraídos
  - Manejo de errores con mensajes claros

---

## [1.0.0] - 2025-10-18

### Reestructuración Profesional del Proyecto

#### Added
- **main.py**: Script principal que ejecuta todo el pipeline automáticamente
- **src/**: Carpeta con código fuente principal
  - `extract_section.py`: Extracción de secciones del PDF
  - `process_table.py`: Procesamiento de tabla y OCR
  - `__init__.py`: Inicialización del paquete
- **tests/**: Carpeta con scripts de testing
  - `test_column_detection.py`: Test completo de detección de columnas
  - `test_single_page.py`: Test rápido con una página
- **tools/**: Carpeta con herramientas de debug
  - `debug_colors.py`: Debug de detección de colores
  - `debug_single_file.py`: Debug de un archivo específico
  - `visualize_columns.py`: Visualización de columnas
- **examples/**: Carpeta con ejemplos de uso
  - `example_usage.py`: Ejemplo de uso de las clases
- **data/**: Carpeta para archivos PDF de entrada
- **output/**: Carpeta para resultados generados
- **docs/**: Carpeta con documentación
  - `RUN_FULL_PROCESS.md`: Guía de ejecución actualizada
  - `USAGE.md`: Guía de uso
  - `VISUALIZACIONES.md`: Guía de visualizaciones
- **.gitignore**: Archivo mejorado con exclusiones apropiadas
- **CHANGELOG.md**: Este archivo

#### Changed
- Rutas de salida actualizadas:
  - `output_sections/` → `output/sections/`
  - `table_data.csv` → `output/table_data.csv`
  - `table_data.xlsx` → `output/table_data.xlsx`
- README.md completamente reescrito con:
  - Estructura de proyecto clara
  - Instrucciones de instalación detalladas
  - Guías de uso paso a paso
  - Sección de troubleshooting
  - Documentación de la arquitectura
- Documentación actualizada en `docs/RUN_FULL_PROCESS.md`

#### Improved
- Organización del código en carpetas lógicas
- Separación clara entre código fuente, tests, herramientas y ejemplos
- Mejor gestión de rutas (busca PDF en `data/` primero)
- Mensajes de error más informativos
- Estructura profesional compatible con mejores prácticas de Python

#### Migration Guide

Si tenías el proyecto antiguo:

1. **Ejecutar scripts principales:**
   - Antes: `python extract_section.py`
   - Ahora: `python src/extract_section.py` o `python main.py`

2. **Ubicación del PDF:**
   - Antes: Raíz del proyecto
   - Ahora: `data/documento.pdf` (o raíz como fallback)

3. **Archivos de salida:**
   - Antes: `output_sections/`, `table_data.csv`
   - Ahora: `output/sections/`, `output/table_data.csv`

4. **Tests:**
   - Antes: Raíz del proyecto
   - Ahora: `tests/`

5. **Debug tools:**
   - Antes: Raíz del proyecto
   - Ahora: `tools/`

### Technical Details

#### Project Structure
```
ExtractTablePdf/
├── main.py                 # Main entry point
├── src/                    # Source code
├── tests/                  # Test scripts
├── tools/                  # Debug utilities
├── examples/               # Example scripts
├── docs/                   # Documentation
├── data/                   # Input data
└── output/                 # Generated output
```

#### Benefits of New Structure
- **Modularidad**: Código organizado por función
- **Escalabilidad**: Fácil añadir nuevas funcionalidades
- **Mantenibilidad**: Código fuente separado de tests y herramientas
- **Profesionalismo**: Sigue convenciones de proyectos Python
- **Compatibilidad**: Compatible con empaquetado futuro (pip, setuptools)

---

## [0.9.0] - Versión anterior

### Features (versión sin reestructurar)
- Extracción de secciones del PDF
- Detección automática de columnas
- Procesamiento OCR con Tesseract
- Exportación a CSV y Excel
- Visualizaciones de debug
- Fusión de filas de continuación
- Detección de encabezados repetidos
