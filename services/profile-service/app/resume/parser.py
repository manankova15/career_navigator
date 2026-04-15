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


def parse_skills(block: str, levels_block: str) -> tuple[list[str], list[dict[str, str]]]:
    skills: list[str] = []
    skill_levels: list[dict[str, str]] = []
    text = (block or "").replace("\n", " ")
    if text:
        for part in re.split(r"[,;•·]|(?:\s{2,})", text):
            s = part.strip()
            if 1 < len(s) < 80:
                skills.append(s)
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
                if ln not in skills:
                    skills.append(ln)
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


def parse_languages(block: str) -> list[dict[str, Any]]:
    res: list[dict[str, Any]] = []
    if not block.strip():
        return res
    for line in block.split("\n"):
        line = line.strip()
        if not line or "—" not in line and "-" not in line:
            continue
        if "—" in line:
            name, level = line.split("—", 1)
        else:
            name, level = line.split("-", 1)
        name, level = name.strip(), level.strip()
        lr = level.lower()
        norm = lr
        if "родн" in lr:
            norm = "native"
        elif re.match(r"^[abc][12]$", lr):
            norm = lr
        res.append({"name": name, "levelRaw": level, "levelNormalized": norm})
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


def build_parsed_document(
    normalized_text: str, sections: dict[str, str], is_hh_resume: bool, confidence: float
) -> dict[str, Any]:
    full = normalized_text
    profile = parse_header_and_personal(full, sections)
    profile.update(parse_contacts(sections.get("contacts", "")))
    profile.update(parse_citizenship_block(sections.get("citizenship", "")))
    job = parse_desired_job(full, sections)
    skills_text = "\n".join(
        filter(
            None,
            [
                sections.get("skills", ""),
                sections.get("skills_key", ""),
            ],
        )
    )
    skills, skill_levels = parse_skills(skills_text, sections.get("skill_levels", ""))
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
