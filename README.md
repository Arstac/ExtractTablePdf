# ExtractTablePdf

Professional PDF table extraction tool with multi-page support, automatic column detection, and OCR processing.

## Features

- Extract tables from multi-page PDFs
- Automatic header and footer removal
- Smart column detection using OCR
- Handle empty cells and continuation rows
- Export to CSV and Excel formats
- Visual debugging and verification tools

## Project Structure

```
ExtractTablePdf/
├── main.py                 # Main entry point (run this!)
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── src/                   # Source code
│   ├── __init__.py
│   ├── extract_section.py # PDF section extraction
│   └── process_table.py   # Table processing and OCR
│
├── data/                  # Input data
│   └── documento.pdf      # Your PDF file goes here
│
├── output/                # Generated output
│   ├── sections/          # Extracted images
│   ├── table_data.csv     # Extracted data (CSV)
│   └── table_data.xlsx    # Extracted data (Excel)
│
├── docs/                  # Documentation
│   ├── RUN_FULL_PROCESS.md
│   ├── USAGE.md
│   └── VISUALIZACIONES.md
│
├── tests/                 # Test scripts
│   ├── test_column_detection.py
│   └── test_single_page.py
│
├── tools/                 # Debug and utility scripts
│   ├── debug_colors.py
│   ├── debug_single_file.py
│   └── visualize_columns.py
│
└── examples/              # Example scripts
    └── example_usage.py
```

## Installation

1. Clone or download this repository

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (required for text extraction):

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # For Catalan/Spanish support
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-cat tesseract-ocr-spa
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

## Quick Start

1. Place your PDF file in the `data/` directory:
```bash
cp your_document.pdf data/documento.pdf
```

2. Run the complete pipeline:
```bash
python main.py
```

That's it! The script will:
- Extract sections from the PDF
- Detect table columns automatically
- Extract text using OCR
- Generate CSV and Excel files in `output/`

## Manual Execution (Step by Step)

If you want to run each step separately:

### Step 1: Extract sections from PDF
```bash
python src/extract_section.py
```

This generates section images in `output/sections/`

### Step 2: Process table and generate output
```bash
python src/process_table.py
```

This processes the sections and generates:
- `output/table_data.csv` - Data in CSV format
- `output/table_data.xlsx` - Data in Excel format
- Debug images in `output/sections/debug_*/`

## Configuration

### Custom PDF Path

Edit [main.py](main.py:24-26) or [src/extract_section.py](src/extract_section.py:332-334):

```python
pdf_path = "data/your_custom_file.pdf"
```

### Output Directories

Edit [main.py](main.py:27-28):

```python
sections_output_dir = "output/sections"
table_output_file = "output/table_data.csv"
```

### Disable Visualizations

Edit [main.py](main.py:76) or [src/process_table.py](src/process_table.py:972):

```python
processor = TableProcessor(
    sections_dir="output/sections",
    output_file="output/table_data.csv",
    generate_visualizations=False  # Set to False
)
```

## Testing

### Test column detection on a single page:
```bash
python tests/test_single_page.py
```

### Test with full dataset:
```bash
python tests/test_column_detection.py
```

## Debug Tools

### Visualize column detection:
```bash
python tools/visualize_columns.py
```

### Debug color detection:
```bash
python tools/debug_colors.py
```

### Debug single file:
```bash
python tools/debug_single_file.py
```

## Output Files

After running the pipeline, you'll find:

### Main Output
- `output/table_data.csv` - Extracted table data (CSV format)
- `output/table_data.xlsx` - Extracted table data (Excel format)

### Debug Output
- `output/sections/` - Extracted section images
- `output/sections/debug/` - Original images and line detection
- `output/sections/debug_header/` - Header detection visualization
- `output/sections/debug_columns/` - Individual column images
- `output/sections/visualizations/` - Column overlay visualizations

## How It Works

### 1. Section Extraction ([src/extract_section.py](src/extract_section.py))
- Locates the target section in the PDF (e.g., section 6.1)
- Removes headers and footers
- Detects horizontal blue lines that divide content
- Splits pages into individual row images

### 2. Table Processing ([src/process_table.py](src/process_table.py))
- Finds the header row automatically
- Detects column positions using exact word matching
- Divides each row image into columns
- Extracts text using Tesseract OCR (Catalan + Spanish)
- Merges continuation rows
- Exports to CSV and Excel

## Column Detection Algorithm

The tool uses a sophisticated multi-word matching algorithm:

1. **Exact Word Matching**: Matches complete words, not substrings
2. **Combination Search**: Finds all possible combinations of OCR blocks
3. **Vertical/Horizontal Detection**: Identifies if titles are stacked or inline
4. **Best Group Selection**: Chooses the most compact and leftmost group
5. **No Duplicates**: Prevents reusing OCR blocks for multiple columns

## Troubleshooting

### "PDF not found" error
Place your PDF in `data/documento.pdf` or update the path in `main.py`

### Poor OCR quality
- Ensure Tesseract is installed with Catalan/Spanish language support
- Check that section images in `output/sections/` are clear
- Adjust DPI in extract_section.py (line 89): `mat = fitz.Matrix(2, 2)`

### Columns not detected correctly
- Check `output/sections/debug_header/header_detection.png`
- Verify header text is clear in the first section
- Adjust column matching tolerance in process_table.py

### Empty or incorrect data
- Check `output/sections/visualizations/` to verify column boundaries
- Review `output/sections/debug_columns/` for individual column images
- Ensure images are not too small or too large

## Requirements

- Python 3.8+
- PyMuPDF (fitz) 1.23.8
- Pillow 10.1.0
- OpenCV 4.8.1.78
- pytesseract 0.3.10
- pandas 2.1.3
- openpyxl 3.1.2
- Tesseract OCR (system dependency)

## License

This project is provided as-is for PDF table extraction purposes.

## Contributing

This is a specialized tool for extracting tables from specific PDF formats.
For questions or issues, please refer to the documentation in the `docs/` directory.

## Version

1.0.0 - Professional restructured version
