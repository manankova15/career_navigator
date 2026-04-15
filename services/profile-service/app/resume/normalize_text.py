"""Normalize resume text: strip noise, keep section boundaries."""

from __future__ import annotations

import re


_PAGE_NUM = re.compile(r"(?:^|\n)\s*\d+\s*/\s*\d+\s*(?:\n|$)", re.MULTILINE)
_HH_PRINT_URL = re.compile(
    r"https?://[^\s]*hh\.ru[^\s]*print[^\s]*", re.IGNORECASE
)
_MULTISPACE = re.compile(r"[ \t]{2,}")
_MULTI_NL = re.compile(r"\n{3,}")


def normalize_resume_text(raw: str) -> str:
    if not raw:
        return ""
    t = raw.replace("\r\n", "\n").replace("\r", "\n")
    t = _HH_PRINT_URL.sub("", t)
    t = _PAGE_NUM.sub("\n", t)
    lines = []
    for line in t.split("\n"):
        line = line.strip()
        if not line:
            lines.append("")
            continue
        if re.fullmatch(r"\d+\s*/\s*\d+", line):
            continue
        lines.append(line)
    t = "\n".join(lines)
    t = _MULTISPACE.sub(" ", t)
    t = _MULTI_NL.sub("\n\n", t)
    return t.strip()
