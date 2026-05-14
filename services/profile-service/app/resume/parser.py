"""Section-based parsers for hh.ru resume text."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

_MONTH_NAME_TO_NUM = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,
}

_MONTH_TOKEN = (
    r"(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|"
    r"январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь)"
)

_PERIOD_RE = re.compile(
    rf"(?im)^\s*({_MONTH_TOKEN})\s+(\d{{4}})\s*[-–—]\s*(.+?)\s*$"
)

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")


def _iso_date(day: int, month_name: str, year: int) -> str | None:
    m = _MONTH_NAME_TO_NUM.get(month_name.lower())
    if not m:
        return None
    try:
        return datetime(year, m, day).date().isoformat()
    except ValueError:
        return None


def _parse_gender_age_birth(head: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    m = re.search(
        r"(?i)(Мужчина|Женщина)\s*,\s*(\d+)\s*лет\s*,\s*родил(?:ся|ась)\s+(\d+)\s+([а-яё]+)\s+(\d{4})",
        head,
    )
    if m:
        g = m.group(1).lower()
        out["gender"] = "male" if g.startswith("муж") else "female"
        out["age"] = int(m.group(2))
        out["birthDate"] = _iso_date(int(m.group(3)), m.group(4), int(m.group(5)))
    return out


def _parse_location_line(head: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for line in head.split("\n"):
        line = line.strip()
        if not line or len(line) > 300:
            continue
        if "готов" in line.lower() or "переезд" in line.lower() or "командиров" in line.lower():
            parts = [p.strip() for p in line.split(",")]
            if parts:
                out["city"] = parts[0]
            for p in parts[1:]:
                pl = p.lower()
                if "готов" in pl or "переезд" in pl or "командиров" in pl:
                    continue
                if re.match(r"(?i)^м\.\s*", p) or "проспект" in pl:
                    out["metro"] = re.sub(r"(?i)^м\.\s*", "", p).strip()
                    break
            low = line.lower()
            if "не готов к переезду" in low:
                out["relocationReadiness"] = "not_ready"
            elif "готов к переезду" in low or "готова к переезду" in low:
                out["relocationReadiness"] = "ready"
            elif "хочу переехать" in low:
                out["relocationReadiness"] = "interested"
            else:
                out["relocationReadiness"] = out.get("relocationReadiness") or "unknown"
            if "не готов к командировкам" in low or "не готова к командировкам" in low:
                out["businessTripReadiness"] = "not_ready"
            elif "готов к командировкам" in low or "готова к командировкам" in low:
                out["businessTripReadiness"] = "ready"
            else:
                out["businessTripReadiness"] = out.get("businessTripReadiness") or "unknown"
            break
    return out


def _head_text(full: str, sections: dict[str, str]) -> str:
    idx = full.find("Контакты")
    if idx == -1:
        idx = min(len(full), 6000)
    return full[:idx]


def parse_header_and_personal(full_text: str, sections: dict[str, str]) -> dict[str, Any]:
    head = _head_text(full_text, sections)
    profile: dict[str, Any] = {
        "fullName": "",
        "firstName": "",
        "lastName": "",
        "middleName": "",
    }
    lines = [ln.strip() for ln in head.split("\n") if ln.strip()]
    for i, line in enumerate(lines[:25]):
        if re.match(r"(?i)^резюме\s*$", line):
            if i + 1 < len(lines) and len(lines[i + 1]) > 3:
                profile["fullName"] = lines[i + 1].strip()
            break
    if not profile["fullName"]:
        for line in lines[:12]:
            if 5 < len(line) < 120 and not re.search(
                r"(?i)мужчина|женщина|лет|hh\.ru|http", line
            ):
                profile["fullName"] = line
                break
    parts = profile["fullName"].split()
    if len(parts) >= 2:
        profile["lastName"] = parts[0]
        profile["firstName"] = parts[1]
        profile["middleName"] = " ".join(parts[2:]) if len(parts) > 2 else ""
    profile.update(_parse_gender_age_birth(head))
    profile.update(_parse_location_line(head))
    return profile


def parse_contacts(block: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "phone": "",
        "phoneVerified": False,
        "email": "",
        "preferredContactMethod": "",
    }
    if not block:
        return out
    phones = _PHONE_RE.findall(block.replace("\n", " "))
    if phones:
        out["phone"] = phones[0].strip()
    em = _EMAIL_RE.search(block)
    if em:
        out["email"] = em.group(0)
    if re.search(r"телефон\s+подтвержд", block, re.I):
        out["phoneVerified"] = True
    if re.search(r"предпочитаемый\s+способ\s+связи", block, re.I):
        ctx = block.lower()
        if out["email"] and "email" in ctx:
            out["preferredContactMethod"] = "email"
        elif out["phone"] and "телефон" in ctx:
            out["preferredContactMethod"] = "phone"
    return out


def _parse_salary_line(text: str) -> dict[str, Any]:
    job: dict[str, Any] = {
        "salaryAmount": None,
        "salaryFrom": None,
        "salaryTo": None,
        "salaryCurrency": "RUB",
        "salaryNetType": "unknown",
    }
    m = re.search(
        r"(?:от\s+)?([\d\s]{3,})\s*(?:[–-]\s*([\d\s]{3,}))?\s*(?:₽|руб\.?)",
        text,
        re.I,
    )
    if m:
        a = int(re.sub(r"\D", "", m.group(1)))
        job["salaryAmount"] = a
        job["salaryFrom"] = a
        if m.group(2):
            b = int(re.sub(r"\D", "", m.group(2)))
            job["salaryTo"] = b
            job["salaryAmount"] = a
    if re.search(r"на\s+рук", text, re.I):
        job["salaryNetType"] = "net"
    elif re.search(r"до\s+вычета\s+налог", text, re.I):
        job["salaryNetType"] = "gross"
    return job


def parse_desired_job(full_text: str, sections: dict[str, str]) -> dict[str, Any]:
    head = _head_text(full_text, sections)
    job: dict[str, Any] = {
        "desiredPosition": "",
        "resumeTitleRaw": "",
        "specializations": [],
        "employmentTypes": [],
        "workSchedules": [],
    }
    job.update(_parse_salary_line(head))
    lines = [ln.strip() for ln in head.split("\n") if ln.strip()]
    for i, line in enumerate(lines):
        if re.match(r"(?i)^резюме\s*$", line) and i + 2 < len(lines):
            job["resumeTitleRaw"] = lines[i + 1]
            pos = lines[i + 2]
            if not re.search(r"(?i)мужчина|женщина", pos):
                job["desiredPosition"] = pos
            break
    if sections.get("specializations"):
        job["specializations"] = _bullet_lines(sections["specializations"])
    if sections.get("employment"):
        job["employmentTypes"] = _bullet_lines(sections["employment"])
    if sections.get("work_schedule"):
        job["workSchedules"] = _bullet_lines(sections["work_schedule"])
    return job


def _bullet_lines(block: str) -> list[str]:
    items: list[str] = []
    for raw in re.split(r"[\n•·]+", block):
        s = raw.strip(" \t-—•\u2022")
        if s and len(s) < 200:
            items.append(s)
    return items


def _parse_month_year_to_iso(month_name: str, year: int) -> str | None:
    m = _MONTH_NAME_TO_NUM.get(month_name.lower().strip())
    if not m:
        return None
    try:
        return datetime(year, m, 1).date().isoformat()
    except ValueError:
        return None


def _parse_period_end(end_part: str) -> tuple[str | None, bool]:
    """Return (end_date_iso, is_current)."""
    s = end_part.strip()
    if re.search(r"по\s+настоящ", s, re.I):
        return None, True
    m = re.match(rf"(?i)^\s*({_MONTH_TOKEN})\s+(\d{{4}})", s)
    if m:
        return _parse_month_year_to_iso(m.group(1), int(m.group(2))), False
    return None, False


def parse_experience(block: str) -> list[dict[str, Any]]:
    if not block.strip():
        return []
    lines = [ln.rstrip() for ln in block.split("\n")]
    experiences: list[dict[str, Any]] = []
    period_line_idx: list[int] = []

    for idx, line in enumerate(lines):
        if _PERIOD_RE.match(line.strip()):
            period_line_idx.append(idx)

    if not period_line_idx:
        return experiences

    for pi, start_idx in enumerate(period_line_idx):
        end_idx = period_line_idx[pi + 1] if pi + 1 < len(period_line_idx) else len(lines)
        chunk_lines = lines[start_idx:end_idx]
        if not chunk_lines:
            continue
        period_line = chunk_lines[0].strip()
        pm = _PERIOD_RE.match(period_line)
        if not pm:
            continue
        start_month = pm.group(1)
        y1 = int(pm.group(2))
        start_date = _parse_month_year_to_iso(start_month, y1)
        rest = pm.group(3)
        end_date, is_current = _parse_period_end(rest)
        pre = lines[max(0, start_idx - 3) : start_idx]
        company = ""
        for cand in reversed(pre):
            c = cand.strip()
            if not c or _PERIOD_RE.match(c):
                continue
            if len(c) > 120:
                continue
            company = c
            break
        title = ""
        description_lines: list[str] = []
        mode = "meta"
        for ln in chunk_lines[1:]:
            s = ln.strip()
            if not s:
                description_lines.append("")
                continue
            if mode == "meta":
                if re.match(r"(?i)https?://", s) or "информационн" in s.lower():
                    pass
                elif len(s) < 120 and not title and not re.match(r"(?i)https?://", s):
                    title = s
                    mode = "desc"
                else:
                    description_lines.append(s)
                    mode = "desc"
            else:
                description_lines.append(s)
        experiences.append(
            {
                "companyName": company,
                "companyLocation": "",
                "companySite": "",
                "industry": "",
                "position": title,
                "startDate": start_date,
                "endDate": end_date,
                "isCurrent": is_current,
                "durationText": period_line,
                "description": "\n".join(x for x in description_lines if x).strip(),
            }
        )
    return experiences


# Phrases that look like skill names but actually contain inner spaces.
# Used to glue tokens back together when splitting an ambiguous space-separated
# skills list ("Навыки" subblock from hh.ru PDF). Lowercase keys; longer phrases
# must precede shorter ones that are prefixes of them.
_KNOWN_MULTIWORD_SKILLS: tuple[str, ...] = (
    "ms project",
    "ms excel",
    "ms word",
    "ms office",
    "google docs",
    "google sheets",
    "google analytics",
    "ms power bi",
    "power bi",
    "power point",
    "powerpoint",
    "adobe photoshop",
    "adobe illustrator",
    "adobe premiere",
    "after effects",
    "1c",
    "1с",
    "rest api",
    "soap api",
    "graphql api",
    "data science",
    "data analysis",
    "data engineering",
    "machine learning",
    "deep learning",
    "computer vision",
    "natural language processing",
    "nlp",
    "ci/cd",
    "ci cd",
    "github actions",
    "gitlab ci",
    "amazon web services",
    "google cloud",
    "google cloud platform",
    "ведение переговоров",
    "деловое общение",
    "деловая переписка",
    "деловая корреспонденция",
    "грамотная речь",
    "грамотная письменная речь",
    "грамотная устная речь",
    "управление проектами",
    "управление командой",
    "управление персоналом",
    "управление продуктом",
    "управление временем",
    "тайм-менеджмент",
    "проектный менеджмент",
    "продуктовый менеджмент",
    "пользователь пк",
    "уверенный пользователь пк",
    "опытный пользователь пк",
    "работа в команде",
    "командная работа",
    "работа с большим объемом информации",
    "работа с большим объёмом информации",
    "поиск информации в интернете",
    "поиск информации",
    "анализ данных",
    "анализ информации",
    "сбор данных",
    "сбор и анализ информации",
    "обработка данных",
    "визуализация данных",
    "статистический анализ",
    "машинное обучение",
    "глубокое обучение",
    "компьютерное зрение",
    "обработка естественного языка",
    "большие данные",
    "интеллектуальный анализ данных",
    "искусственный интеллект",
    "разработка по",
    "разработка программного обеспечения",
    "тестирование по",
    "ручное тестирование",
    "автоматизированное тестирование",
    "функциональное тестирование",
    "нагрузочное тестирование",
    "frontend разработка",
    "backend разработка",
    "веб-разработка",
    "веб разработка",
    "разработка веб-приложений",
    "разработка мобильных приложений",
    "мобильная разработка",
    "продуктовая аналитика",
    "бизнес анализ",
    "бизнес-анализ",
    "финансовый анализ",
    "финансовая отчетность",
    "финансовая отчётность",
    "бухгалтерский учет",
    "бухгалтерский учёт",
    "налоговый учет",
    "налоговый учёт",
    "управленческий учет",
    "управленческий учёт",
    "клиентский сервис",
    "клиентоориентированность",
    "холодные звонки",
    "активные продажи",
    "b2b продажи",
    "b2c продажи",
    "прямые продажи",
    "техническая поддержка",
    "пользовательская поддержка",
    "ведение документации",
    "написание документации",
    "техническая документация",
    "проектная документация",
    "контроль качества",
    "обеспечение качества",
    "стрессоустойчивость",
    "критическое мышление",
    "аналитическое мышление",
    "системное мышление",
    "английский язык",
    "немецкий язык",
    "французский язык",
    "испанский язык",
    "китайский язык",
    "русский язык",
)


def _split_skill_tokens(line: str) -> list[str]:
    """
    Split an ambiguous space-separated hh.ru skills line into individual skills.

    The "Навыки" subblock of hh.ru PDF can contain skills separated by single
    spaces while individual skills may themselves contain spaces (e.g.
    "MS Excel", "Машинное обучение", "ведение переговоров"). Splitting only on
    whitespace would shred multi-word skills; gluing on whitespace would merge
    everything. We therefore use two heuristics:

      1. Recognise known multi-word skill phrases verbatim.
      2. Treat a capital letter at the start of a new token (Latin OR Cyrillic)
         as the most likely beginning of the next skill.

    Tokens that don't trigger a new skill are appended to the current one.
    """
    raw = re.sub(r"\s+", " ", line.strip())
    if not raw:
        return []

    # First: peel off known multi-word skill phrases greedily.
    found: list[str] = []
    remaining = raw
    used_intervals: list[tuple[int, int]] = []

    low = remaining.lower()
    # Sort known phrases by length desc so longer ones win.
    for phrase in sorted(_KNOWN_MULTIWORD_SKILLS, key=len, reverse=True):
        start = 0
        while True:
            idx = low.find(phrase, start)
            if idx < 0:
                break
            end = idx + len(phrase)
            # Must be on word boundaries.
            left_ok = idx == 0 or not low[idx - 1].isalnum()
            right_ok = end >= len(low) or not low[end].isalnum()
            # And must not overlap an already-used interval.
            overlap = any(not (end <= s or idx >= e) for s, e in used_intervals)
            if left_ok and right_ok and not overlap:
                used_intervals.append((idx, end))
                found.append(remaining[idx:end])
                start = end
            else:
                start = idx + 1

    # Now build a list of (position, text, is_known) for every chunk.
    used_intervals.sort()
    chunks: list[tuple[int, str, bool]] = []
    cursor = 0
    for s, e in used_intervals:
        if cursor < s:
            chunks.append((cursor, remaining[cursor:s], False))
        chunks.append((s, remaining[s:e], True))
        cursor = e
    if cursor < len(remaining):
        chunks.append((cursor, remaining[cursor:], False))

    # Now split the unknown chunks by capital-letter transitions.
    results: list[str] = []
    for _pos, text, is_known in chunks:
        text = text.strip()
        if not text:
            continue
        if is_known:
            results.append(text)
            continue
        # Split on capital letter boundaries: a token starts at the beginning
        # or after a space when the first letter is upper-case.
        tokens = text.split(" ")
        current: list[str] = []
        for tok in tokens:
            if not tok:
                continue
            starts_new = False
            first = tok[0]
            if first.isupper() and current:
                # Capital letter while we have an accumulator => new skill,
                # unless previous accumulator ends with a separator-y char
                # (parenthesis, slash, dash). Also don't break tiny known
                # connectives like "и", "or", "and" — but those won't be
                # uppercase, so this naive rule is okay.
                starts_new = True
            elif first.isdigit() and current:
                # A number-led token usually starts a new skill ("1С").
                starts_new = True
            if starts_new:
                results.append(" ".join(current).strip())
                current = [tok]
            else:
                current.append(tok)
        if current:
            results.append(" ".join(current).strip())

    return [r for r in results if r]


def parse_skills(block: str, levels_block: str) -> tuple[list[str], list[dict[str, str]]]:
    skills: list[str] = []
    skill_levels: list[dict[str, str]] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        s = name.strip(" \t-—–•·\u2022")
        if not (1 < len(s) < 80):
            return
        key = s.lower()
        if key in seen:
            return
        seen.add(key)
        skills.append(s)

    # 1) "Уровни владения навыками" is the authoritative source — each skill is
    #    on its own line. Use it whenever present.
    level_map = {
        "продвинут": "advanced",
        "средн": "intermediate",
        "базов": "basic",
        "не указан": "unknown",
    }
    if levels_block:
        current = "unknown"
        for line in levels_block.split("\n"):
            ln = line.strip()
            low = ln.lower()
            matched = False
            for ru, code in level_map.items():
                if ru in low and "уров" in low:
                    current = code
                    matched = True
                    break
            if matched:
                continue
            if ln and not ln.lower().startswith("уровень") and len(ln) < 100:
                skill_levels.append({"skill": ln, "level": current})
                _add(ln)

    # 2) "Навыки" subblock — fall back to splitting if the levels block was
    #    missing or sparse. Try newlines / commas / bullets / multi-space first,
    #    and only invoke the space-and-capital heuristic for "single line of
    #    many skills glued together".
    text = (block or "").strip()
    if text:
        # First pass: obvious delimiters.
        primary_parts = [p.strip() for p in re.split(r"[\n,;•·]|(?:\s{2,})", text) if p.strip()]
        for part in primary_parts:
            # If this fragment is itself a long line with many words and no
            # delimiters, it is probably an hh.ru space-glued list. Try
            # heuristic splitting.
            word_count = len(part.split())
            if word_count >= 4 and len(part) > 30:
                for sub in _split_skill_tokens(part):
                    _add(sub)
            else:
                _add(part)

    return skills, skill_levels


def parse_education(block: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not block.strip():
        return out
    chunks = re.split(r"\n{2,}", block.strip())
    for ch in chunks:
        lines = [x.strip() for x in ch.split("\n") if x.strip()]
        if not lines:
            continue
        year = None
        for ln in lines:
            ym = re.search(r"\b(19|20)\d{2}\b", ln)
            if ym:
                year = int(ym.group(0))
                break
        out.append(
            {
                "level": "",
                "institution": lines[0][:200],
                "endYear": year,
                "faculty": "",
                "speciality": lines[-1][:200] if len(lines) > 1 else "",
            }
        )
    return out


def parse_courses(block: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not block.strip():
        return items
    for ch in re.split(r"\n{2,}", block.strip()):
        lines = [x.strip() for x in ch.split("\n") if x.strip()]
        if not lines:
            continue
        y = None
        for ln in lines:
            m = re.search(r"\b(19|20)\d{2}\b", ln)
            if m:
                y = int(m.group(0))
        items.append(
            {"title": lines[0][:200], "organization": lines[1] if len(lines) > 1 else "", "year": y, "description": ""}
        )
    return items


def _normalize_lang_level(level_raw: str) -> str:
    lr = level_raw.lower().strip()
    if "родн" in lr or "native" in lr:
        return "native"
    m = re.match(r"^([abc][12])\b", lr)
    if m:
        return m.group(1)
    return lr


def _looks_like_lang_level(text: str) -> bool:
    t = text.strip().lower()
    if not t or len(t) > 80:
        return False
    if re.search(r"\b[abc][12]\b", t):
        return True
    if "родн" in t or "native" in t:
        return True
    keywords = (
        "свободн", "уровень", "разговорн", "технич", "базов",
        "начальн", "средн", "продвинут", "fluent", "beginner",
        "intermediate", "advanced", "elementary", "upper",
    )
    return any(k in t for k in keywords)


def parse_languages(block: str) -> list[dict[str, Any]]:
    res: list[dict[str, Any]] = []
    if not block.strip():
        return res
    lines = [ln.strip() for ln in block.split("\n")]
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
        if "—" in line or "-" in line:
            if "—" in line:
                name, level = line.split("—", 1)
            else:
                name, level = line.split("-", 1)
            name, level = name.strip(), level.strip()
            if name and level:
                res.append(
                    {
                        "name": name,
                        "levelRaw": level,
                        "levelNormalized": _normalize_lang_level(level),
                    }
                )
            i += 1
            continue
        # Try two-line pattern: "<Language>\n<Level>"
        if i + 1 < len(lines) and lines[i + 1] and _looks_like_lang_level(lines[i + 1]):
            name = line
            level = lines[i + 1]
            if 1 < len(name) < 60 and not _looks_like_lang_level(name):
                res.append(
                    {
                        "name": name,
                        "levelRaw": level,
                        "levelNormalized": _normalize_lang_level(level),
                    }
                )
                i += 2
                continue
        i += 1
    return res


def parse_citizenship_block(block: str) -> dict[str, Any]:
    out: dict[str, Any] = {"citizenship": "", "workPermit": "", "commuteTimePreference": ""}
    if not block:
        return out
    m = re.search(r"Гражданство\s*:\s*(.+)", block, re.I)
    if m:
        out["citizenship"] = m.group(1).split("\n")[0].strip()
    m = re.search(r"Разрешение\s+на\s+работу\s*:\s*(.+)", block, re.I)
    if m:
        out["workPermit"] = m.group(1).split("\n")[0].strip()
    m = re.search(r"времени\s+в\s+пути[^\n:]*:\s*(.+)", block, re.I)
    if m:
        out["commuteTimePreference"] = m.group(1).strip()
    return out


def parse_resume_updated(full_text: str) -> str:
    m = re.search(r"Резюме обновлено\s*[:\s]*([^\n]+)", full_text, re.I)
    return m.group(1).strip() if m else ""


def _strip_languages_subblock(skills_block: str) -> str:
    """Удаляет внутренний подблок «Знание языков» из текста секции «Навыки».

    В резюме с hh.ru блок «Навыки» содержит два подблока: «Знание языков»
    (1-й) и «Навыки» (2-й). Если splitter секций не отделил их (например,
    из-за вариаций заголовка), убираем подблок языков вручную: всё, что
    идёт от строки-заголовка «Знание языков» до следующего заголовка
    подблока «Навыки» или до конца блока — выкидываем.
    """
    if not skills_block:
        return skills_block
    lines = skills_block.split("\n")
    out: list[str] = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        low = stripped.lower()
        if re.fullmatch(r"знание\s+языков\s*:?", low):
            skipping = True
            continue
        if skipping:
            # Заходим во второй подблок «Навыки» — снова собираем содержимое.
            if re.fullmatch(r"навыки\s*:?", low):
                skipping = False
                continue
            continue
        out.append(line)
    return "\n".join(out)


def build_parsed_document(
    normalized_text: str, sections: dict[str, str], is_hh_resume: bool, confidence: float
) -> dict[str, Any]:
    full = normalized_text
    profile = parse_header_and_personal(full, sections)
    profile.update(parse_contacts(sections.get("contacts", "")))
    profile.update(parse_citizenship_block(sections.get("citizenship", "")))
    job = parse_desired_job(full, sections)
    # Из подблока «Навыки» исключаем вложенный «Знание языков»,
    # чтобы языки не попадали в список навыков.
    raw_skills_block = _strip_languages_subblock(sections.get("skills", ""))
    skills_text = "\n".join(
        filter(
            None,
            [
                raw_skills_block,
                sections.get("skills_key", ""),
            ],
        )
    )
    skills, skill_levels = parse_skills(skills_text, sections.get("skill_levels", ""))
    # Фильтрация по канонической базе навыков (case-insensitive).
    from .skills_base import filter_skills_against_base, normalized_skill_set
    base = normalized_skill_set()
    skills = filter_skills_against_base(skills, base)
    skill_levels = [sl for sl in skill_levels if (sl.get("skill") or "").strip().lower() in base]
    exp = parse_experience(sections.get("experience", ""))
    edu_blocks = "\n\n".join(
        filter(None, [sections.get("education", ""), sections.get("education_higher", "")])
    )
    education = parse_education(edu_blocks)
    courses = parse_courses(sections.get("courses", ""))
    languages = parse_languages(sections.get("languages", ""))
    about_me = sections.get("about", "").strip()
    add_info = sections.get("additional_info", "").strip()
    warnings: list[str] = []
    if confidence < 0.75:
        warnings.append("Проверьте распознанные данные — уверенность ниже порога авто-применения.")
    return {
        "isHhResume": is_hh_resume,
        "confidence": round(confidence, 4),
        "profile": profile,
        "job": job,
        "experience": exp,
        "skills": skills,
        "skillLevels": skill_levels,
        "education": education,
        "courses": courses,
        "languages": languages,
        "aboutMe": about_me,
        "additionalInfo": add_info,
        "resumeUpdatedAt": parse_resume_updated(full),
        "warnings": warnings,
        "rawSectionsDetected": sorted(set(sections.keys())),
    }


def build_field_confidence(parsed: dict[str, Any], file_confidence: float) -> dict[str, Any]:
    """Nested dict of field path -> 0..1 heuristic confidence."""
    base = max(0.35, min(0.95, file_confidence))

    def leaf(v: Any) -> float:
        if v is None or v == "" or v == []:
            return 0.0
        return base

    prof = parsed.get("profile") or {}
    fc: dict[str, Any] = {
        "profile": {k: leaf(v) for k, v in prof.items()},
        "job": {k: leaf(v) for k, v in (parsed.get("job") or {}).items()},
        "aboutMe": leaf(parsed.get("aboutMe")),
        "additionalInfo": leaf(parsed.get("additionalInfo")),
        "experience": [leaf(e.get("companyName")) * 0.9 for e in (parsed.get("experience") or [])],
        "education": [leaf(e.get("institution")) * 0.85 for e in (parsed.get("education") or [])],
        "skills": [leaf(s) * 0.8 for s in (parsed.get("skills") or [])],
    }
    return fc
