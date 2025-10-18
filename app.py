#!/usr/bin/env python3
"""
FastAPI application for PDF table extraction.

This API provides an endpoint to upload PDF files and extract table data.
Returns a list of dictionaries with the extracted criteria data.
"""

import os
import sys
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Optional
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.extract_section import PDFSectionExtractor
from src.process_table import TableProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Table Extraction API",
    description="Extract table data from PDF documents with automatic column detection and OCR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PDFProcessor:
    """Helper class to process PDFs and manage temporary files."""

    def __init__(self, temp: bool = True):
        """
        Initialize the PDF processor.

        Args:
            temp: If True, files are temporary and will be deleted after processing
        """
        self.temp = temp
        self.session_id = str(uuid.uuid4())

        if temp:
            # Create temporary directory
            self.base_dir = Path(tempfile.mkdtemp(prefix=f"pdf_extraction_{self.session_id}_"))
        else:
            # Use persistent directory
            self.base_dir = Path("output") / self.session_id
            self.base_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_path = self.base_dir / "input.pdf"
        self.sections_dir = self.base_dir / "sections"
        self.output_csv = self.base_dir / "table_data.csv"

        logger.info(f"Session {self.session_id} - temp={temp}, dir={self.base_dir}")

    def save_uploaded_file(self, file: UploadFile) -> Path:
        """Save uploaded PDF file."""
        try:
            with open(self.pdf_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            logger.info(f"Session {self.session_id} - PDF saved: {self.pdf_path}")
            return self.pdf_path
        except Exception as e:
            logger.error(f"Session {self.session_id} - Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    def extract_sections(self) -> List[str]:
        """Extract sections from PDF."""
        try:
            extractor = PDFSectionExtractor(str(self.pdf_path), str(self.sections_dir))
            saved_files = extractor.process()
            extractor.close()

            logger.info(f"Session {self.session_id} - Extracted {len(saved_files)} sections")
            return saved_files
        except Exception as e:
            logger.error(f"Session {self.session_id} - Error extracting sections: {e}")
            raise HTTPException(status_code=500, detail=f"Error extracting sections: {str(e)}")

    def process_table(self) -> pd.DataFrame:
        """Process table and extract data."""
        try:
            processor = TableProcessor(
                sections_dir=str(self.sections_dir),
                output_file=str(self.output_csv),
                generate_visualizations=False  # Disable for API
            )

            df = processor.process_all_sections(debug=False)

            if df is None or df.empty:
                raise HTTPException(status_code=404, detail="No data extracted from PDF")

            logger.info(f"Session {self.session_id} - Extracted {len(df)} rows")
            return df
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Session {self.session_id} - Error processing table: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing table: {str(e)}")

    def dataframe_to_dict_list(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert DataFrame to list of dictionaries.

        Removes internal columns (starting with _) and converts to dict.
        """
        # Remove internal columns
        df_clean = df.drop(columns=[col for col in df.columns if col.startswith('_')], errors='ignore')

        # Convert to list of dictionaries
        records = df_clean.to_dict('records')

        # Clean up NaN values
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, str):
                    record[key] = value.strip()

        return records

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp and self.base_dir.exists():
            try:
                shutil.rmtree(self.base_dir)
                logger.info(f"Session {self.session_id} - Cleaned up temporary files")
            except Exception as e:
                logger.error(f"Session {self.session_id} - Error cleaning up: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup if temp=True."""
        if self.temp:
            self.cleanup()


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "PDF Table Extraction API",
        "version": "1.0.0",
        "description": "Extract table data from PDF documents",
        "endpoints": {
            "POST /extract": "Upload PDF and extract table data",
            "GET /health": "Health check",
            "GET /docs": "Interactive API documentation",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "pdf-table-extraction",
        "version": "1.0.0"
    }


@app.post("/extract", response_model=List[Dict])
async def extract_pdf_table(
    file: UploadFile = File(..., description="PDF file to extract data from"),
    temp: bool = Query(True, description="If True, temporary files are deleted after processing")
):
    """
    Extract table data from uploaded PDF file.

    Args:
        file: PDF file to process
        temp: If True (default), temporary files are deleted after processing.
              If False, files are kept in output/{session_id}/ for debugging.

    Returns:
        List of dictionaries containing the extracted table data.
        Each dictionary represents a row with the following keys:
        - tipus_criterio: Type of criterion
        - nom_criteri: Criterion name
        - descripcio: Description
        - on_incloure: Where to include
        - doc_a_verificar_adj: Document to verify for adjudication
        - doc_a_verificar_exec: Document to verify for execution
        - condicionants: Conditions

    Raises:
        HTTPException 400: If file is not a PDF
        HTTPException 404: If no data could be extracted
        HTTPException 500: If processing error occurs
    """

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are accepted."
        )

    logger.info(f"Processing request - file={file.filename}, temp={temp}")

    # Process PDF
    with PDFProcessor(temp=temp) as processor:
        try:
            # Save uploaded file
            processor.save_uploaded_file(file)

            # Extract sections from PDF
            sections = processor.extract_sections()

            if not sections:
                raise HTTPException(
                    status_code=404,
                    detail="No sections found in PDF. Please check the PDF format."
                )

            # Process table and extract data
            df = processor.process_table()

            # Convert to list of dictionaries
            result = processor.dataframe_to_dict_list(df)

            logger.info(f"Successfully extracted {len(result)} records")

            return JSONResponse(
                content={
                    "success": True,
                    "count": len(result),
                    "data": result,
                    "session_id": processor.session_id if not temp else None
                }
            )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during processing: {str(e)}"
            )


@app.post("/extract/simple", response_model=List[Dict])
async def extract_pdf_table_simple(
    file: UploadFile = File(...),
    temp: bool = Query(True)
):
    """
    Simplified endpoint that returns only the data array (without metadata).

    Same as /extract but returns only the list of dictionaries.
    """
    response = await extract_pdf_table(file, temp)
    return response.body.get("data", [])


if __name__ == "__main__":
    import uvicorn

    # Run the app
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
