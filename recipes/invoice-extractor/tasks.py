"""
Invoice Extractor Recipe — tasks.py

Defines the extraction and validation tasks for processing raw invoice text.
"""

from crewai import Agent, Task
from models import InvoiceData, InvoiceExtractionOutput


def build_tasks(
    extractor_agent: Agent,
    validator_agent: Agent,
    invoice_text: str,
) -> list[Task]:
    """Build and return the workflow tasks.

    Args:
        extractor_agent: Agent responsible for structured data extraction.
        validator_agent: Agent responsible for financial arithmetic audit.
        invoice_text: Raw text of the invoice document.

    Returns:
        List containing the extraction task and validation task.
    """
    extraction_task = Task(
        description=(
            "Analyze the following raw invoice text and extract all structured data:\n\n"
            "```\n"
            f"{invoice_text}\n"
            "```\n\n"
            "Extract the following fields carefully:\n"
            "- vendor_name: Name of the vendor or issuing company\n"
            "- invoice_number: Invoice number or code\n"
            "- invoice_date: Date issued (YYYY-MM-DD or as written)\n"
            "- due_date: Payment due date if present\n"
            "- line_items: List of items, each with description, quantity, unit_price, total\n"
            "- subtotal: Subtotal amount\n"
            "- tax: Tax / VAT amount\n"
            "- grand_total: Grand total amount"
        ),
        expected_output=(
            "Structured invoice details matching the InvoiceData schema including "
            "vendor, invoice number, dates, all line items, subtotal, tax, and grand total."
        ),
        agent=extractor_agent,
        output_pydantic=InvoiceData,
    )

    validation_task = Task(
        description=(
            "Review the extracted invoice data from the previous task.\n\n"
            "Audit the financial calculations:\n"
            "1. Calculate the sum of all line item totals: sum(item.total for item in line_items).\n"
            "2. Verify if quantity * unit_price == item.total for each line item.\n"
            "3. Calculate calculated_grand_total = subtotal (or line_items_sum) + tax.\n"
            "4. Compare calculated_grand_total against extracted grand_total.\n"
            "5. Set is_valid to True if discrepancy is within 0.05, else False.\n"
            "6. Populate warnings list with any arithmetic mismatches or missing fields.\n\n"
            "Return the complete InvoiceExtractionOutput containing both the invoice data and the validation result."
        ),
        expected_output=(
            "Validated JSON output containing the extracted invoice data alongside "
            "the financial validation result, discrepancy calculation, and audit warnings."
        ),
        agent=validator_agent,
        output_pydantic=InvoiceExtractionOutput,
    )

    return [extraction_task, validation_task]
