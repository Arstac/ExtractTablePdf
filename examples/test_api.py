#!/usr/bin/env python3
"""
Example script to test the PDF extraction API.

Make sure the API is running before executing this script:
    python app.py
"""

import requests
import json
import sys
from pathlib import Path


class PDFExtractionClient:
    """Simple client for the PDF extraction API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def health_check(self):
        """Check if the API is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API health check failed: {e}")
            return None

    def extract_pdf(self, pdf_path: str, temp: bool = True):
        """
        Extract table data from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            temp: If True, temporary files are deleted after processing

        Returns:
            Dictionary with extraction results
        """
        url = f"{self.base_url}/extract"

        # Check if file exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        print(f"📤 Uploading PDF: {pdf_path}")
        print(f"   temp={temp}")

        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (Path(pdf_path).name, f, "application/pdf")}
                params = {"temp": temp}

                response = requests.post(url, files=files, params=params, timeout=300)
                response.raise_for_status()

                return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Detail: {error_detail}")
                except:
                    print(f"   Response: {e.response.text}")
            return None


def main():
    """Main test function."""
    print("="*70)
    print("PDF Extraction API - Test Script")
    print("="*70)
    print()

    # Initialize client
    client = PDFExtractionClient()

    # 1. Health check
    print("1️⃣  Checking API health...")
    health = client.health_check()

    if health:
        print(f"   ✓ API is {health['status']}")
        print(f"   Service: {health['service']} v{health['version']}")
        print()
    else:
        print("   ❌ API is not available")
        print("   Make sure the API is running: python app.py")
        sys.exit(1)

    # 2. Extract PDF
    print("2️⃣  Extracting PDF data...")

    # Determine PDF path
    pdf_path = "data/documento.pdf"
    if not Path(pdf_path).exists():
        pdf_path = "documento.pdf"
        if not Path(pdf_path).exists():
            print(f"   ❌ PDF not found: {pdf_path}")
            print("   Please place a PDF file in data/documento.pdf")
            sys.exit(1)

    # Extract with temp=True (default)
    result = client.extract_pdf(pdf_path, temp=True)

    if result and result.get("success"):
        print(f"   ✓ Extraction successful!")
        print(f"   Records extracted: {result['count']}")
        print()

        # 3. Display results
        print("3️⃣  Sample data (first 3 records):")
        print("-" * 70)

        for i, record in enumerate(result["data"][:3], 1):
            print(f"\nRecord {i}:")
            print(f"  Tipus: {record.get('tipus_criterio', 'N/A')}")
            print(f"  Nom: {record.get('nom_criteri', 'N/A')}")
            print(f"  Descripció: {record.get('descripcio', 'N/A')[:80]}...")
            print(f"  On incloure: {record.get('on_incloure', 'N/A')}")

        print()
        print("-" * 70)
        print(f"\nTotal records: {result['count']}")

        # 4. Save to file
        output_file = "api_test_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Full results saved to: {output_file}")

    else:
        print("   ❌ Extraction failed")

    print()
    print("="*70)
    print("Test completed!")
    print("="*70)


if __name__ == "__main__":
    main()
