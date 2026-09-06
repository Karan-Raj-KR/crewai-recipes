"""
Invoice Extractor Recipe — main.py

Edit-and-run sample entry point.
Run directly with: python main.py
"""

import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402
from parser import extract_text_from_pdf_or_image  # noqa: E402

SAMPLE_INVOICE_TEXT = """
INVOICE #INV-2026-0891
Vendor: Apex Cloud Technologies LLC
Date: 2026-08-15
Due Date: 2026-09-15

BILL TO:
Acme Enterprise Inc
100 Innovation Way, Suite 400
San Francisco, CA 94105

DESCRIPTION                         QTY    UNIT PRICE     TOTAL
---------------------------------------------------------------
Cloud Server Hosting (Monthly)       2      $450.00      $900.00
Database Optimization Consultation  5      $150.00      $750.00
SSL Certificate Security Add-on      1       $50.00       $50.00

SUBTOTAL: $1700.00
TAX (8%): $136.00
GRAND TOTAL: $1836.00
"""


def main() -> None:
    """Run the invoice extractor on sample invoice text or fixture file."""
    print("🤖 Running Invoice Extractor & Auditor Crew...\n")

    # Check if sample PDF fixture exists, otherwise use string
    fixture_pdf = (
        Path(__file__).parent / "tests" / "fixtures" / "sample_invoice_digital.pdf"
    )
    if fixture_pdf.exists():
        print(f"📄 Parsing invoice fixture: {fixture_pdf.name}")
        invoice_text, method = extract_text_from_pdf_or_image(fixture_pdf)
        print(f"   Extraction Method: {method}\n")
    else:
        print("📝 Using sample text invoice...\n")
        invoice_text = SAMPLE_INVOICE_TEXT

    crew = build_crew(invoice_text=invoice_text)
    result = crew.kickoff()

    print("\n✅ Extraction and Financial Audit Completed!\n")
    try:
        parsed_json = json.loads(str(result))
        print(json.dumps(parsed_json, indent=2))
    except (json.JSONDecodeError, TypeError):
        print(result)


if __name__ == "__main__":
    main()
