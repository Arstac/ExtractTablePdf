#!/usr/bin/env python3
"""
Main script to run the complete PDF table extraction pipeline.

This script executes the full workflow:
1. Extract sections from PDF (extract_section.py)
2. Process table and generate CSV/Excel (process_table.py)
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.extract_section import PDFSectionExtractor
from src.process_table import TableProcessor


def main():
    print("="*70)
    print(" PDF TABLE EXTRACTION - FULL PIPELINE")
    print("="*70)
    print()

    # Configuration
    pdf_path = "data/documento.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = "documento.pdf"

    sections_output_dir = "output/sections"
    table_output_file = "output/table_data.csv"

    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF not found")
        print(f"   Please place your PDF in one of these locations:")
        print(f"   - data/documento.pdf")
        print(f"   - documento.pdf (project root)")
        return 1

    print(f"📄 PDF found: {pdf_path}")
    print()

    # =========================================================================
    # STEP 1: Extract sections from PDF
    # =========================================================================
    print("="*70)
    print("STEP 1: EXTRACTING SECTIONS FROM PDF")
    print("="*70)
    print()

    try:
        extractor = PDFSectionExtractor(pdf_path, sections_output_dir)
        saved_files = extractor.process()
        extractor.close()

        print()
        print(f"✓ Step 1 completed: {len(saved_files)} sections extracted")
        print(f"  Output directory: {sections_output_dir}/")
        print()

    except Exception as e:
        print(f"\n❌ Error in Step 1: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # =========================================================================
    # STEP 2: Process table and generate CSV/Excel
    # =========================================================================
    print("="*70)
    print("STEP 2: PROCESSING TABLE AND GENERATING OUTPUT")
    print("="*70)
    print()

    try:
        processor = TableProcessor(
            sections_dir=sections_output_dir,
            output_file=table_output_file,
            generate_visualizations=True
        )

        df = processor.process_all_sections(debug=True)

        if df is not None:
            print()
            print(f"✓ Step 2 completed: {len(df)} rows extracted")
            print()
            print("📊 Output files generated:")
            print(f"   - {table_output_file}")
            print(f"   - {table_output_file.replace('.csv', '.xlsx')}")
            print()
            print("🔍 Debug files generated:")
            print(f"   - {sections_output_dir}/debug_header/")
            print(f"   - {sections_output_dir}/debug_columns/")
            print(f"   - {sections_output_dir}/visualizations/")
            print()

            # Show preview
            print("="*70)
            print("DATA PREVIEW (first 3 rows)")
            print("="*70)
            print()
            print(df.head(3).to_string())
            print()
            print(f"Total rows: {len(df)}")
            print()

        else:
            print("\n⚠️  Warning: No data was extracted")
            return 1

    except Exception as e:
        print(f"\n❌ Error in Step 2: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # =========================================================================
    # SUCCESS
    # =========================================================================
    print("="*70)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY")
    print("="*70)
    print()
    print("Next steps:")
    print("  - Review the extracted data in output/table_data.xlsx")
    print("  - Check visualizations in output/sections/visualizations/")
    print("  - Verify column detection in output/sections/debug_header/")
    print()

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
