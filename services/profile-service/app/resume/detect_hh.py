"""Score-based detection of hh.ru resume printouts."""

from __future__ import annotations

import re


_POSITIVE = [
    (r"\bhh\.ru\b", 0.12),
    (r"applicant/resumes/view", 0.14),
    (r"print=true", 0.08),
    (r"(?i)\bрезюме\b", 0.06),
    (r"Резюме обновлено", 0.08),
    (r"Опыт работы", 0.1),
    (r"Ключевые навыки", 0.08),
    (r"(?i)\bНавыки\b", 0.05),
    (r"Обо мне", 0.06),
    (r"Образование", 0.07),
    (r"Знание языков", 0.06),
    (r"Гражданство", 0.05),
    (r"Специализации", 0.06),
    (r"Занятость", 0.05),
    (r"График работы", 0.05),
    (r"Контакты", 0.05),
]

_NEGATIVE_KEYWORDS = [
    r"договор\s+№",
    r"акт\s+выполненных",
    r"сч[её]т\s+на\s+оплату",
    r"справка\s+о\s+доходах",
]

_CONTRACT_LIKE = re.compile("|".join(f"(?:{p})" for p in _NEGATIVE_KEYWORDS), re.IGNORECASE)


def detect_hh_resume(normalized_text: str) -> tuple[bool, float, list[str]]:
    """
    Returns (is_hh_resume, score 0..1, warnings).
    Thresholds: >=0.75 valid, 0.45..0.75 suspicious, <0.45 not hh for autofill.
    """
    warnings: list[str] = []
    t = normalized_text or ""
    if len(t) < 200:
        warnings.append("Мало текста в документе — возможно скан без OCR.")
    score = 0.0
    for pattern, w in _POSITIVE:
        if re.search(pattern, t):
            score += w
    if _CONTRACT_LIKE.search(t):
        score -= 0.25
        warnings.append("Текст похож на договор или счёт — снижен балл.")
    if len(t) < 400:
        score -= 0.1
    score = max(0.0, min(1.0, score))
    is_hh = score >= 0.75
    if 0.45 <= score < 0.75:
        warnings.append("Файл похож на резюме hh.ru не полностью — проверьте данные вручную.")
    if score < 0.45:
        warnings.append("Низкая уверенность, что это резюме hh.ru — автозаполнение отключено.")
    return is_hh, score, warnings
