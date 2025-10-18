#!/bin/bash
#
# Quick start script for ExtractTablePdf
# This script runs the complete PDF table extraction pipeline
#

set -e  # Exit on error

echo "========================================================================"
echo "  ExtractTablePdf - Quick Start"
echo "========================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✓ Python found: $($PYTHON_CMD --version)"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found"
    echo "   Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! $PYTHON_CMD -c "import pytesseract" 2>/dev/null; then
    echo "⚠️  Dependencies not installed"
    echo "   Installing dependencies..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
    echo ""
fi

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "❌ Error: Tesseract OCR is not installed"
    echo ""
    echo "   Please install Tesseract OCR:"
    echo "   - macOS:        brew install tesseract tesseract-lang"
    echo "   - Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-cat tesseract-ocr-spa"
    echo "   - Windows:      https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
    exit 1
fi

echo "✓ Tesseract OCR found: $(tesseract --version | head -1)"
echo ""

# Check if PDF exists
if [ ! -f "data/documento.pdf" ] && [ ! -f "documento.pdf" ]; then
    echo "⚠️  PDF file not found"
    echo "   Please place your PDF file in one of these locations:"
    echo "   - data/documento.pdf (recommended)"
    echo "   - documento.pdf"
    echo ""
    read -p "Press Enter to continue anyway (for testing), or Ctrl+C to exit..."
    echo ""
fi

# Run the pipeline
echo "========================================================================"
echo "  Running the extraction pipeline..."
echo "========================================================================"
echo ""

$PYTHON_CMD main.py

# Deactivate virtual environment
deactivate

echo ""
echo "========================================================================"
echo "  Done! Check the output/ directory for results."
echo "========================================================================"
