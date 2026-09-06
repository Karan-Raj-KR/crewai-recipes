"""
Invoice Extractor Recipe — run.py

CLI entry point for running the invoice extractor recipe.

Usage:
    python run.py --file tests/fixtures/sample_invoice_digital.pdf
    python run.py --file scanned_invoice.jpg --pretty
    python run.py --text "Invoice #101 Vendor: Acme Corp Total: $150.00" --json-out output.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402
from parser import extract_text_from_pdf_or_image  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_env() -> None:
    """Preflight environment check for required API key."""
    api_key = os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("❌ Error: Missing API key.", file=sys.stderr)
        print(
            "   Please set LLM_API_KEY or NVIDIA_API_KEY in your .env file or environment.",
            file=sys.stderr,
        )
        print("   Get a free key at https://build.nvidia.com", file=sys.stderr)
        sys.exit(1)


def format_pretty_markdown(result_str: str) -> str:
    """Format JSON or dictionary result into clean markdown summary."""
    try:
        data = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        return f"# Invoice Extraction Result\n\n{result_str}"

    inv = data.get("invoice", {})
    val = data.get("validation", {})

    lines = [
        f"# Invoice Extraction Summary — {inv.get('invoice_number', 'N/A')}",
        "",
        f"**Vendor:** {inv.get('vendor_name', 'N/A')}",
        f"**Invoice Date:** {inv.get('invoice_date', 'N/A')}",
        f"**Due Date:** {inv.get('due_date', 'N/A') or 'N/A'}",
        "",
        "### Line Items",
        "| Description | Qty | Unit Price | Line Total |",
        "| :--- | :---: | :---: | :---: |",
    ]

    for item in inv.get("line_items", []):
        desc = item.get("description", "")
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0.0)
        tot = item.get("total", 0.0)
        lines.append(f"| {desc} | {qty} | ${price:.2f} | ${tot:.2f} |")

    lines.extend(
        [
            "",
            f"**Subtotal:** ${inv.get('subtotal', 0.0):.2f}",
            f"**Tax / VAT:** ${inv.get('tax', 0.0):.2f}",
            f"**Grand Total:** ${inv.get('grand_total', 0.0):.2f}",
            "",
            "### Audit & Validation Status",
            f"- **Valid Math:** {'✅ Yes' if val.get('is_valid') else '⚠️ Arithmetic Mismatch Detected'}",
            f"- **Line Items Sum:** ${val.get('line_items_sum', 0.0):.2f}",
            f"- **Calculated Grand Total:** ${val.get('calculated_grand_total', 0.0):.2f}",
            f"- **Discrepancy:** ${val.get('discrepancy', 0.0):.2f}",
        ]
    )

    warnings = val.get("warnings", [])
    if warnings:
        lines.append("\n**Warnings / Audit Alerts:**")
        for w in warnings:
            lines.append(f"- ⚠️ {w}")

    return "\n".join(lines)


def main() -> None:
    """Parse CLI arguments and run the invoice extractor crew."""
    check_env()

    parser = argparse.ArgumentParser(
        description="Extract structured JSON and audit invoice details from PDF/images using CrewAI"
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="Path to PDF or image invoice file",
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        default=None,
        help="Raw invoice text string",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print pretty-printed markdown output instead of raw JSON",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Save output JSON to specified file path",
    )

    args = parser.parse_args()

    invoice_text = args.text
    if not invoice_text and args.file:
        invoice_text, method_used = extract_text_from_pdf_or_image(args.file)
        logger.info("Extracted invoice text via '%s' method.", method_used)
    elif not invoice_text:
        # Default fallback sample fixture for zero-argument invocation
        default_sample = (
            Path(__file__).parent / "tests" / "fixtures" / "sample_invoice.txt"
        )
        if default_sample.exists():
            invoice_text = default_sample.read_text(encoding="utf-8")
            logger.info(
                "No file or text provided; using default sample fixture: %s",
                default_sample.name,
            )
        else:
            print(
                '❌ Error: Please specify --file <path> or --text "..."',
                file=sys.stderr,
            )
            sys.exit(1)

    print("🚀 Initializing Invoice Extractor & Auditor Crew...\n", file=sys.stderr)
    crew = build_crew(invoice_text=invoice_text)
    result = crew.kickoff()
    output_str = str(result)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(output_str, encoding="utf-8")
        print(f"\n💾 Saved result to {out_path.resolve()}", file=sys.stderr)

    if args.pretty:
        print("\n" + format_pretty_markdown(output_str))
    else:
        print(output_str)

    sys.exit(0)


if __name__ == "__main__":
    main()
