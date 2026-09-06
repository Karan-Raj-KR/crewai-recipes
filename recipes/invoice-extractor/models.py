"""
Invoice Extractor Recipe — models.py

Pydantic models defining the structured schema for extracted invoice data
and financial validation auditing.
"""

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """Individual line item within an invoice."""

    description: str = Field(..., description="Description or product name of the item")
    quantity: float = Field(default=1.0, description="Quantity of items purchased")
    unit_price: float = Field(default=0.0, description="Unit price per item")
    total: float = Field(
        ..., description="Line item total price (quantity * unit_price)"
    )


class InvoiceData(BaseModel):
    """Structured details extracted from an invoice document."""

    vendor_name: str = Field(..., description="Name of the issuing vendor or company")
    invoice_number: str = Field(..., description="Invoice identifier or number")
    invoice_date: str = Field(
        ..., description="Date invoice was issued (YYYY-MM-DD or as listed)"
    )
    due_date: str | None = Field(
        default=None, description="Payment due date if specified"
    )
    line_items: list[LineItem] = Field(
        default_factory=list, description="List of parsed line items"
    )
    subtotal: float = Field(
        default=0.0, description="Subtotal amount before taxes and fees"
    )
    tax: float = Field(default=0.0, description="Tax or VAT amount")
    grand_total: float = Field(..., description="Final invoice grand total amount")


class ValidationResult(BaseModel):
    """Financial audit and arithmetic validation status."""

    is_valid: bool = Field(
        ...,
        description="True if line items sum + tax equals grand total within threshold",
    )
    line_items_sum: float = Field(
        ..., description="Calculated sum of all line item totals"
    )
    calculated_grand_total: float = Field(
        ..., description="Calculated subtotal/line items sum + tax"
    )
    discrepancy: float = Field(
        default=0.0,
        description="Absolute difference between expected and calculated grand total",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of audit warning messages if discrepancies exist",
    )


class InvoiceExtractionOutput(BaseModel):
    """Combined output containing extracted invoice data and audit validation results."""

    invoice: InvoiceData
    validation: ValidationResult
