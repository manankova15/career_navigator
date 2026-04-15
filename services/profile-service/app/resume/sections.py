"""Split normalized resume text into sections by known hh.ru headings."""

from __future__ import annotations

import re
from typing import Iterable

# Order matters for overlapping names: longer / more specific first
SECTION_ALIASES: list[tuple[str, str]] = [
    ("Повышение квалификации, курсы", "courses"),
    ("Ключевые навыки", "skills_key"),
    ("Уровни владения навыками", "skill_levels"),
    ("Высшее образование", "education_higher"),
    ("Опыт работы", "experience"),
    ("Дополнительные сведения", "additional_info"),
    ("Дополнительная информация", "additional_info"),
    ("Знание языков", "languages"),
    ("Гражданство, время в пути до работы", "citizenship"),
    ("Гражданство", "citizenship"),
    ("Специализации", "specializations"),
    ("График работы", "work_schedule"),
    ("Занятость", "employment"),
    ("Сопроводительное письмо", "ignore"),
    ("Комментарии к резюме", "ignore"),
    ("История общения с кандидатом", "ignore"),
    ("Образование", "education"),
    ("Навыки", "skills"),
    ("Обо мне", "about"),
    ("Контакты", "contacts"),
]


def _heading_pattern(title: str) -> re.Pattern[str]:
    escaped = re.escape(title)
    return re.compile(rf"(?m)^\s*{escaped}\s*:?\s*$", re.IGNORECASE)


def split_into_sections(normalized_text: str) -> dict[str, str]:
    text = normalized_text or ""
    markers: list[tuple[int, str, str]] = []
    for title, key in SECTION_ALIASES:
        for m in _heading_pattern(title).finditer(text):
            markers.append((m.start(), m.end(), key))
    markers.sort(key=lambda x: x[0])
    # de-duplicate overlapping: keep first occurrence per key at distinct positions
    used_keys: set[str] = set()
    filtered: list[tuple[int, int, str]] = []
    for start, end, key in markers:
        if key == "ignore":
            continue
        if any(start >= s and start < e for s, e, _ in filtered):
            continue
        filtered.append((start, end, key))
    filtered.sort(key=lambda x: x[0])
    sections: dict[str, str] = {}
    for i, (start, end, key) in enumerate(filtered):
        body_start = end
        body_end = filtered[i + 1][0] if i + 1 < len(filtered) else len(text)
        chunk = text[body_start:body_end].strip()
        if key in sections:
            sections[key] = sections[key] + "\n\n" + chunk
        else:
            sections[key] = chunk
    return sections


def raw_sections_detected(sections: dict[str, str]) -> list[str]:
    return sorted(sections.keys())
