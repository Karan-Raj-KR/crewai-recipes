"""
Invoice Extractor Recipe — parser.py

Handles PDF text extraction with automatic OCR fallback for scanned PDFs and image files.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def extract_text_from_pdf_or_image(file_path: str | Path) -> tuple[str, str]:
    """Extract raw text from a PDF or image invoice file.

    Tries text extraction via pypdf first for digital PDFs.
    If extracted text is empty or sparse (< 20 characters), or if the input is an image file,
    falls back to OCR via pdf2image and pytesseract.

    Args:
        file_path: Path to the PDF or image invoice file.

    Returns:
        A tuple of (extracted_text, method_used) where method_used is "pdf_text" or "ocr".

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If file type is unsupported or no text could be extracted.
        RuntimeError: If OCR is required but system OCR tools (tesseract/poppler) are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Invoice file not found at: {path}")

    suffix = path.suffix.lower()

    # 1. Try text extraction for PDFs
    if suffix == ".pdf":
        try:
            import pypdf

            reader = pypdf.PdfReader(str(path))
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            combined_text = "\n".join(pages_text).strip()
            if len(combined_text) >= 20:
                logger.info(
                    "Successfully extracted text from digital PDF: %s", path.name
                )
                return combined_text, "pdf_text"
            else:
                logger.info(
                    "PDF text empty or sparse (%d chars); trying OCR fallback...",
                    len(combined_text),
                )
        except ImportError:
            logger.warning("pypdf is not installed; trying OCR fallback...")
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "Error reading PDF with pypdf (%s); trying OCR fallback...", err
            )

    # 2. OCR fallback for scanned PDFs or images
    logger.info("Using OCR fallback for scanned PDF/image: %s", path.name)

    try:
        import pytesseract
        from PIL import Image
    except ImportError as err:
        raise RuntimeError(
            "OCR dependencies (pytesseract, Pillow) are required for scanned PDFs and images.\n"
            "  Run: pip install pytesseract pdf2image Pillow"
        ) from err

    ocr_pages_text = []

    if suffix in IMAGE_EXTENSIONS:
        try:
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            if text and text.strip():
                ocr_pages_text.append(text.strip())
        except Exception as err:
            raise RuntimeError(
                f"Tesseract OCR failed to process image '{path.name}'.\n"
                "Ensure Tesseract binary is installed system-wide:\n"
                "  macOS: brew install tesseract\n"
                "  Ubuntu/Debian: apt-get install tesseract-ocr\n"
                f"Details: {err}"
            ) from err

    elif suffix == ".pdf":
        try:
            import pdf2image

            images = pdf2image.convert_from_path(str(path))
            for img in images:
                text = pytesseract.image_to_string(img)
                if text and text.strip():
                    ocr_pages_text.append(text.strip())
        except ImportError as err:
            raise RuntimeError(
                "pdf2image is required to extract images from scanned PDFs.\n"
                "  Run: pip install pdf2image"
            ) from err
        except Exception as err:
            raise RuntimeError(
                f"Failed to perform OCR on PDF '{path.name}'.\n"
                "Ensure Tesseract and Poppler binaries are installed system-wide:\n"
                "  macOS: brew install tesseract poppler\n"
                "  Ubuntu/Debian: apt-get install tesseract-ocr poppler-utils\n"
                f"Details: {err}"
            ) from err
    else:
        raise ValueError(
            f"Unsupported file format '{suffix}'. Supported formats: .pdf, {', '.join(sorted(IMAGE_EXTENSIONS))}"
        )

    final_text = "\n".join(ocr_pages_text).strip()
    if not final_text:
        raise ValueError(
            f"Unable to extract text from '{path.name}'. The document may be blank, unreadable, or corrupted."
        )

    return final_text, "ocr"
