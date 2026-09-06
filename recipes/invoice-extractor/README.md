# 📄 Invoice Extractor Recipe (PDF / Image → Structured Line-Item JSON)

A multi-agent CrewAI workflow that converts PDF and image invoices into validated, structured JSON line items with automated financial arithmetic auditing.

Powered by **CrewAI** and **NVIDIA NIM** (Llama 3.1 8B by default).

---

## 💡 What & Why

Extracting structured data from PDF invoices and scanned receipts is one of the most critical automated LLM workflows in financial operations. Standard text-only recipes fail when processing scanned documents or images.

This recipe demonstrates the **OCR-then-agent** pattern:
1. **Pre-crew text extraction (`parser.py`)**: Uses `pypdf` to extract text from digital PDFs. If text is sparse or missing, or if an image (`.png`, `.jpg`, `.tiff`) is provided, automatically falls back to OCR via `pdf2image` + `pytesseract`.
2. **Extractor Agent (`agents.py`)**: Extracts vendor metadata, invoice number, dates, line items (description, quantity, unit price, total), tax, subtotal, and grand total into a typed Pydantic model (`InvoiceData`).
3. **Validator Agent (`agents.py`)**: Performs financial cross-checks (`quantity * unit_price == total`, `subtotal + tax == grand_total`). Flags any math mismatches or discrepancies as warnings without crashing the execution.

---

## ⚡ Quickstart

```bash
# 1. Navigate to recipe directory
cd recipes/invoice-extractor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env and set: LLM_API_KEY=nvapi-...

# 4. Run with a digital PDF invoice
python run.py --file tests/fixtures/sample_invoice_digital.pdf

# 5. Run with pretty markdown output
python run.py --file tests/fixtures/sample_invoice_digital.pdf --pretty
```

---

## 🛠 System Prerequisites for OCR

- **Digital PDFs** work out-of-the-box using `pypdf` with no extra system dependencies.
- **Scanned PDFs & Image files (`.png`, `.jpg`, `.jpeg`, `.tiff`)** use OCR fallback and require system-wide installation of Tesseract OCR and Poppler:

### macOS
```bash
brew install tesseract poppler
```

### Ubuntu / Debian
```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils
```

### Windows
Download and install [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki) and [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/), then add them to your System PATH.

---

## 🚀 CLI Usage

```bash
# Extract from a PDF file (stdout prints JSON)
python run.py --file /path/to/invoice.pdf

# Extract from a scanned image with pretty markdown output
python run.py --file /path/to/receipt.jpg --pretty

# Save validated JSON output to file
python run.py --file invoice.pdf --json-out extracted_invoice.json

# Pass raw invoice text directly
python run.py --text "INVOICE #101 Vendor: Acme Qty: 2 Price: 50 Total: 100 Grand Total: 100"
```

---

## 📋 Sample Output

```json
{
  "invoice": {
    "vendor_name": "Apex Cloud Technologies LLC",
    "invoice_number": "INV-2026-0891",
    "invoice_date": "2026-08-15",
    "due_date": "2026-09-15",
    "line_items": [
      {
        "description": "Cloud Server Hosting (Monthly)",
        "quantity": 2.0,
        "unit_price": 450.0,
        "total": 900.0
      },
      {
        "description": "Database Optimization Consultation",
        "quantity": 5.0,
        "unit_price": 150.0,
        "total": 750.0
      },
      {
        "description": "SSL Certificate Security Add-on",
        "quantity": 1.0,
        "unit_price": 50.0,
        "total": 50.0
      }
    ],
    "subtotal": 1700.0,
    "tax": 136.0,
    "grand_total": 1836.0
  },
  "validation": {
    "is_valid": true,
    "line_items_sum": 1700.0,
    "calculated_grand_total": 1836.0,
    "discrepancy": 0.0,
    "warnings": []
  }
}
```

---

## 📐 Architecture

```
PDF / Image File ──► parser.py (pypdf / OCR fallback) ──► Raw Invoice Text
                                                              │
                                                              ▼
                                                   Extractor Agent (agents.py)
                                                              │
                                                              ▼ (InvoiceData)
                                                   Validator Agent (agents.py)
                                                              │
                                                              ▼
                                                 InvoiceExtractionOutput (JSON)
```
