"""Extract text from PDF: text layer first, then PyMuPDF, then OCR fallback."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _extract_pypdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        parts.append(t)
    return "\n".join(parts)


def _extract_pymupdf(path: Path) -> str:
    import fitz

    doc = fitz.open(str(path))
    try:
        parts: list[str] = []
        for i in range(len(doc)):
            parts.append(doc.load_page(i).get_text("text") or "")
        return "\n".join(parts)
    finally:
        doc.close()


def _ocr_pdf(path: Path, max_pages: int = 8) -> str:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except Exception as e:
        logger.warning("OCR dependencies unavailable: %s", e)
        return ""

    try:
        images = convert_from_path(str(path), first_page=1, last_page=max_pages, dpi=200)
    except Exception as e:
        logger.warning("pdf2image failed: %s", e)
        return ""

    parts: list[str] = []
    for img in images:
        try:
            parts.append(pytesseract.image_to_string(img, lang="rus+eng") or "")
        except Exception as e:
            logger.warning("tesseract failed: %s", e)
    return "\n".join(parts)


def extract_text_from_pdf(path: Path) -> tuple[str, str]:
    """Return (raw_text, extraction_method): method is pypdf | pymupdf | ocr | merged."""
    raw = _extract_pypdf(path).strip()
    method = "pypdf"
    if len(raw) < 120:
        alt = _extract_pymupdf(path).strip()
        if len(alt) > len(raw):
            raw = alt
            method = "pymupdf"
    if len(raw) < 120:
        ocr = _ocr_pdf(path).strip()
        if len(ocr) > len(raw):
            raw = ocr
            method = "ocr"
        elif ocr and method != "pypdf":
            raw = (raw + "\n" + ocr).strip()
            method = "merged"
    return raw, method
