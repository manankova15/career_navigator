"""Tests for PDF text extraction (mocked IO)."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.resume.extract_pdf import _extract_pypdf, _ocr_pdf, extract_text_from_pdf


def test_extract_pypdf_page_exception_returns_empty_string(tmp_path: Path):
    pdf = tmp_path / "t.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    mock_page = MagicMock()
    mock_page.extract_text.side_effect = RuntimeError("bad page")
    reader = MagicMock()
    reader.pages = [mock_page]

    with patch("pypdf.PdfReader", return_value=reader):
        text = _extract_pypdf(pdf)
    assert text == ""


class _FakeFitzDoc:
    def __init__(self, page_texts: list[str]):
        self._page_texts = page_texts

    def __len__(self) -> int:
        return len(self._page_texts)

    def load_page(self, i: int):
        page = MagicMock()
        page.get_text = lambda _mode: self._page_texts[i]
        return page

    def close(self) -> None:
        pass


def test_extract_text_prefers_pymupdf_when_pypdf_short(tmp_path: Path):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "short"
    reader = MagicMock()
    reader.pages = [mock_page]

    fake_doc = _FakeFitzDoc(["x" * 150])

    with patch("pypdf.PdfReader", return_value=reader):
        with patch("fitz.open", return_value=fake_doc):
            text, method = extract_text_from_pdf(pdf)
    assert method == "pymupdf"
    assert len(text) >= 120


def test_extract_text_ocr_fallback_when_both_short(tmp_path: Path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    reader = MagicMock()
    reader.pages = [mock_page]

    fake_doc = _FakeFitzDoc([""])

    with patch("pypdf.PdfReader", return_value=reader):
        with patch("fitz.open", return_value=fake_doc):
            with patch("app.resume.extract_pdf._ocr_pdf", return_value="ocr " * 40):
                text, method = extract_text_from_pdf(pdf)
    assert method == "ocr"
    assert len(text.strip()) >= 120


def test_extract_merged_when_ocr_supplements_pymupdf(tmp_path: Path):
    pdf = tmp_path / "m.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    reader = MagicMock()
    reader.pages = [mock_page]

    # pymupdf text long enough to stay primary, OCR shorter but non-empty → merged branch
    fake_doc = _FakeFitzDoc(["y" * 100])

    with patch("pypdf.PdfReader", return_value=reader):
        with patch("fitz.open", return_value=fake_doc):
            with patch("app.resume.extract_pdf._ocr_pdf", return_value="z" * 30):
                text, method = extract_text_from_pdf(pdf)
    assert method == "merged"
    assert "y" in text and "z" in text


def test_ocr_pdf_convert_from_path_failure(tmp_path: Path, monkeypatch):
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    pi = types.ModuleType("pdf2image")

    def _fail(*_a, **_k):
        raise RuntimeError("no poppler")

    pi.convert_from_path = _fail
    monkeypatch.setitem(sys.modules, "pdf2image", pi)
    pt = types.ModuleType("pytesseract")
    monkeypatch.setitem(sys.modules, "pytesseract", pt)

    assert _ocr_pdf(pdf) == ""


def test_ocr_pdf_success_path(tmp_path: Path, monkeypatch):
    import sys
    from types import ModuleType

    pdf = tmp_path / "ok.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    pi = ModuleType("pdf2image")
    pi.convert_from_path = lambda *_a, **_k: [object(), object()]
    pt = ModuleType("pytesseract")
    pt.image_to_string = lambda *_a, **_k: "word " * 20
    monkeypatch.setitem(sys.modules, "pdf2image", pi)
    monkeypatch.setitem(sys.modules, "pytesseract", pt)

    from app.resume.extract_pdf import _ocr_pdf

    text = _ocr_pdf(pdf)
    assert len(text) > 30


def test_ocr_pdf_tesseract_failure_per_image(tmp_path: Path, monkeypatch):
    pdf = tmp_path / "p2.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    pi = types.ModuleType("pdf2image")
    img = object()
    pi.convert_from_path = lambda **_k: [img, img]
    monkeypatch.setitem(sys.modules, "pdf2image", pi)
    pt = types.ModuleType("pytesseract")

    def boom(*_a, **_k):
        raise RuntimeError("tess")

    pt.image_to_string = boom
    monkeypatch.setitem(sys.modules, "pytesseract", pt)

    assert _ocr_pdf(pdf) == ""
