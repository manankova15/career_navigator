"""End-to-end: extract PDF → normalize → detect → sections → parse."""

from __future__ import annotations

from pathlib import Path

from .detect_hh import detect_hh_resume
from .extract_pdf import extract_text_from_pdf
from .normalize_text import normalize_resume_text
from .parser import build_field_confidence, build_parsed_document
from .sections import raw_sections_detected, split_into_sections


def run_resume_pipeline(pdf_path: Path) -> dict:
    """
    Returns dict with keys:
      raw_text, normalized_text, extraction_method,
      is_hh_resume, confidence, warnings (combined),
      parsed (document per TZ), field_confidence, sections_detected
    """
    raw_text, extraction_method = extract_text_from_pdf(pdf_path)
    normalized = normalize_resume_text(raw_text)
    is_hh, confidence, det_warnings = detect_hh_resume(normalized)
    sections = split_into_sections(normalized)
    parsed = build_parsed_document(normalized, sections, is_hh, confidence)
    parsed["warnings"] = list({*parsed.get("warnings", []), *det_warnings})
    fc = build_field_confidence(parsed, confidence)
    return {
        "raw_text": raw_text,
        "normalized_text": normalized,
        "extraction_method": extraction_method,
        "is_hh_resume": is_hh,
        "confidence": confidence,
        "warnings": parsed["warnings"],
        "parsed": parsed,
        "field_confidence": fc,
        "sections_detected": raw_sections_detected(sections),
    }
