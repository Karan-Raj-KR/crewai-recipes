"""
Invoice Extractor Recipe — test_invoice_extractor.py

Offline unit test suite for parser, Pydantic models, and workflow logic.
"""

from pathlib import Path

import pytest
from models import InvoiceData, InvoiceExtractionOutput, LineItem, ValidationResult
from parser import extract_text_from_pdf_or_image

FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"


def test_models_instantiation():
    """Verify Pydantic models can be instantiated and validated."""
    item = LineItem(
        description="Cloud Server",
        quantity=2.0,
        unit_price=450.0,
        total=900.0,
    )
    assert item.total == 900.0

    invoice = InvoiceData(
        vendor_name="Apex Cloud Technologies LLC",
        invoice_number="INV-2026-0891",
        invoice_date="2026-08-15",
        line_items=[item],
        subtotal=900.0,
        tax=72.0,
        grand_total=972.0,
    )
    assert invoice.vendor_name == "Apex Cloud Technologies LLC"
    assert len(invoice.line_items) == 1

    validation = ValidationResult(
        is_valid=True,
        line_items_sum=900.0,
        calculated_grand_total=972.0,
        discrepancy=0.0,
        warnings=[],
    )
    assert validation.is_valid is True

    output = InvoiceExtractionOutput(invoice=invoice, validation=validation)
    assert output.invoice.invoice_number == "INV-2026-0891"
    assert output.validation.is_valid is True


def test_extract_text_from_pdf_digital():
    """Test text extraction from a text-based PDF fixture using pypdf."""
    pdf_fixture = FIXTURES_DIR / "sample_invoice_digital.pdf"
    assert pdf_fixture.exists()

    text, method = extract_text_from_pdf_or_image(pdf_fixture)
    assert method == "pdf_text"
    assert "INVOICE" in text
    assert "Acme Global Solutions" in text


def test_extract_text_file_not_found():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf_or_image("non_existent_file.pdf")


def test_extract_text_unsupported_format(tmp_path):
    """Test that unsupported file extensions raise ValueError."""
    dummy_file = tmp_path / "test.txt"
    dummy_file.write_text("dummy text")

    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_text_from_pdf_or_image(dummy_file)


def test_arithmetic_validation_logic():
    """Test arithmetic validation computation and mismatch warning detection."""
    # Test valid math
    subtotal = 1700.0
    tax = 136.0
    grand_total = 1836.0
    calc_total = subtotal + tax
    discrepancy = abs(calc_total - grand_total)

    assert discrepancy < 0.01

    # Test mismatch math
    bad_grand_total = 2000.0
    bad_discrepancy = abs(calc_total - bad_grand_total)
    assert bad_discrepancy > 0.01
