# API Documentation

FastAPI application for extracting table data from PDF documents.

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the API Server

```bash
# Option 1: Using the script directly
python app.py

# Option 2: Using uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### `GET /`
Root endpoint with API information.

**Response:**
```json
{
  "name": "PDF Table Extraction API",
  "version": "1.0.0",
  "description": "Extract table data from PDF documents",
  "endpoints": {
    "POST /extract": "Upload PDF and extract table data",
    "GET /health": "Health check",
    "GET /docs": "Interactive API documentation"
  }
}
```

---

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "pdf-table-extraction",
  "version": "1.0.0"
}
```

---

### `POST /extract`
Extract table data from uploaded PDF file.

**Parameters:**
- `file` (multipart/form-data, required): PDF file to process
- `temp` (query, optional, default=true): If true, temporary files are deleted after processing

**Request Example (curl):**
```bash
# With temporary files (default)
curl -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"

# Keep files for debugging
curl -X POST "http://localhost:8000/extract?temp=false" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"
```

**Request Example (Python):**
```python
import requests

url = "http://localhost:8000/extract"

with open("documento.pdf", "rb") as f:
    files = {"file": ("documento.pdf", f, "application/pdf")}
    params = {"temp": True}

    response = requests.post(url, files=files, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"Extracted {data['count']} records")

        for record in data['data']:
            print(record)
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
```

**Request Example (JavaScript/Fetch):**
```javascript
const formData = new FormData();
const fileInput = document.querySelector('input[type="file"]');
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/extract?temp=true', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log(`Extracted ${data.count} records`);
    console.log(data.data);
  })
  .catch(error => console.error('Error:', error));
```

**Success Response (200):**
```json
{
  "success": true,
  "count": 15,
  "data": [
    {
      "tipus_criterio": "Obligatori",
      "nom_criteri": "Utilització de vehicles elèctrics",
      "descripcio": "Els vehicles utilitzats han de ser 100% elèctrics...",
      "on_incloure": "Clàusules administratives",
      "doc_a_verificar_adj": "Declaració responsable",
      "doc_a_verificar_exec": "Factures i albarans",
      "condicionants": "Aplicable a tots els vehicles"
    },
    {
      "tipus_criterio": "Opcional",
      "nom_criteri": "Certificació ambiental ISO 14001",
      "descripcio": "L'empresa disposa de certificació ISO 14001...",
      "on_incloure": "Criteris d'adjudicació",
      "doc_a_verificar_adj": "Certificat vigent ISO 14001",
      "doc_a_verificar_exec": null,
      "condicionants": null
    }
  ],
  "session_id": null
}
```

**Response Fields:**
- `success`: Boolean indicating if extraction was successful
- `count`: Number of records extracted
- `data`: Array of extracted records (each record is a dictionary)
- `session_id`: UUID of the session (only if `temp=false`)

**Record Fields:**
Each record in the `data` array contains:
- `tipus_criterio`: Type of criterion (e.g., "Obligatori", "Opcional")
- `nom_criteri`: Name of the criterion
- `descripcio`: Description of the criterion
- `on_incloure`: Where to include it
- `doc_a_verificar_adj`: Document to verify for adjudication
- `doc_a_verificar_exec`: Document to verify for execution
- `condicionants`: Conditions or constraints

**Error Responses:**

**400 Bad Request** - Invalid file type:
```json
{
  "detail": "Invalid file type. Only PDF files are accepted."
}
```

**404 Not Found** - No data extracted:
```json
{
  "detail": "No data extracted from PDF"
}
```

**500 Internal Server Error** - Processing error:
```json
{
  "detail": "Error processing table: [error message]"
}
```

---

### `POST /extract/simple`
Simplified endpoint that returns only the data array.

**Parameters:**
Same as `/extract`

**Response:**
Returns only the array of dictionaries (without metadata):
```json
[
  {
    "tipus_criterio": "Obligatori",
    "nom_criteri": "Utilització de vehicles elèctrics",
    ...
  },
  {
    "tipus_criterio": "Opcional",
    "nom_criteri": "Certificació ambiental ISO 14001",
    ...
  }
]
```

---

## Temporary Files Management

### `temp=true` (Default)
- Files are stored in a temporary directory
- All files are **automatically deleted** after the response is sent
- Use this for production to avoid disk space issues

### `temp=false` (Debug Mode)
- Files are stored in `output/{session_id}/`
- Files are **NOT deleted** after processing
- Useful for debugging or inspecting intermediate results
- You can examine:
  - `output/{session_id}/input.pdf` - Original PDF
  - `output/{session_id}/sections/` - Extracted section images
  - `output/{session_id}/table_data.csv` - Extracted data

**Example with debugging:**
```bash
curl -X POST "http://localhost:8000/extract?temp=false" \
  -F "file=@documento.pdf" | jq .

# Check the session_id in the response
# Then inspect the files:
ls -la output/{session_id}/
```

---

## Testing the API

### Test with curl

```bash
# 1. Upload a PDF
curl -X POST "http://localhost:8000/extract" \
  -F "file=@data/documento.pdf" \
  | jq .

# 2. Save response to file
curl -X POST "http://localhost:8000/extract" \
  -F "file=@data/documento.pdf" \
  -o response.json

# 3. Keep files for debugging
curl -X POST "http://localhost:8000/extract?temp=false" \
  -F "file=@data/documento.pdf" \
  | jq .
```

### Test with Python

Create a file `test_api.py`:

```python
import requests
import json

def test_extract_pdf():
    url = "http://localhost:8000/extract"

    # Test with temporary files
    with open("data/documento.pdf", "rb") as f:
        files = {"file": f}
        params = {"temp": True}

        response = requests.post(url, files=files, params=params)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Records extracted: {data['count']}")
            print(f"\nFirst record:")
            print(json.dumps(data['data'][0], indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.json()}")

if __name__ == "__main__":
    test_extract_pdf()
```

Run it:
```bash
python test_api.py
```

---

## Production Deployment

### Using Gunicorn (Recommended for production)

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-cat \
    tesseract-ocr-spa \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t pdf-extraction-api .
docker run -p 8000:8000 pdf-extraction-api
```

---

## Performance Considerations

- **Processing time**: Depends on PDF size and number of pages (typically 10-30 seconds per PDF)
- **Memory usage**: ~500MB per concurrent request
- **Disk usage**: If `temp=false`, ~50MB per PDF
- **Concurrency**: Recommended max 4 workers for CPU-intensive OCR tasks

---

## Troubleshooting

### API won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Tesseract is installed: `tesseract --version`
- Check port 8000 is not in use: `lsof -i :8000`

### PDF processing fails
- Ensure PDF is valid and not corrupted
- Check PDF contains the expected table structure
- Try with `temp=false` to inspect intermediate files

### Poor extraction quality
- Verify Tesseract language packs are installed (cat+spa)
- Check section images in `output/{session_id}/sections/`
- Adjust parameters in `src/process_table.py` if needed

---

## API Client Examples

### Python Client Class

```python
import requests
from typing import List, Dict, Optional

class PDFExtractionClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def extract(self, pdf_path: str, temp: bool = True) -> List[Dict]:
        """Extract table data from PDF."""
        url = f"{self.base_url}/extract"

        with open(pdf_path, "rb") as f:
            files = {"file": f}
            params = {"temp": temp}
            response = requests.post(url, files=files, params=params)

        response.raise_for_status()
        return response.json()["data"]

    def health_check(self) -> Dict:
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# Usage
client = PDFExtractionClient()
data = client.extract("documento.pdf")
print(f"Extracted {len(data)} records")
```

---

## License

This API is part of the ExtractTablePdf project.
