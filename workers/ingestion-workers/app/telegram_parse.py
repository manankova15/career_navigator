"""Парсинг сообщений TG в поля вакансии (синхронизировано с scripts/seed_telegram_vacancies.py)."""
from __future__ import annotations

import re

from .salary_parser import parse_salary as _parse_salary_full

_SENIORITY_MAP = [
    ("intern",  ["стажёр", "стажер", "intern", "trainee"]),
    ("junior",  ["junior", "джун", "джуниор", "начинающий"]),
    ("middle",  ["middle", "мидл", "миддл"]),
    ("senior",  ["senior", "сеньор", "ведущий"]),
    ("lead",    ["lead", "лид", "principal", "staff", "архитектор", "руководитель"]),
]

# Типичные IT-навыки для обнаружения в тексте
_SKILL_KEYWORDS = [
    "Python", "SQL", "Excel", "Power BI", "Tableau", "R",
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
    "PostgreSQL", "MySQL", "ClickHouse", "Redshift", "BigQuery",
    "Spark", "Hadoop", "Airflow", "dbt", "Kafka",
    "Machine Learning", "Deep Learning", "NLP",
    "TensorFlow", "PyTorch", "scikit-learn", "Catboost", "XGBoost",
    "Git", "Docker", "Kubernetes", "Linux",
    "A/B тесты", "A/B testing", "статистика", "statistics",
    "Google Analytics", "Amplitude", "Mixpanel",
    "JIRA", "Confluence", "Notion",
    "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "Java", "Kotlin", "Go", "Golang", "C++", "C#", ".NET",
    "Swift", "iOS", "Android",
    "REST", "API", "GraphQL",
    "AWS", "GCP", "Azure",
    "Looker", "Superset", "Metabase",
]

_LOCATION_PATTERNS = [
    re.compile(r"(?:локация|место работы|город|офис)[:\s]+([^\n,;]{3,40})", re.IGNORECASE),
    re.compile(r"📍\s*([^\n,;]{3,40})"),
    re.compile(r"🗺\s*([^\n,;]{3,40})"),
    re.compile(r"(?:москва|санкт-петербург|спб|питер|новосибирск|екатеринбург|казань|удалённо|remote|дистанционно)", re.IGNORECASE),
]

_COMPANY_PATTERNS = [
    re.compile(r"(?:компания|работодатель|company)[:\s]+([^\n]{3,100})", re.IGNORECASE),
    re.compile(r"🏢\s*([^\n]{3,100})"),
    re.compile(r"🏦\s*([^\n]{3,100})"),
    re.compile(r"(?:ООО|ОАО|ЗАО|АО|ИП)\s+[«\"]?([^\n»\"]{3,80})"),
]

# Markdown link pattern: [text](url)
_MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)", re.IGNORECASE)

# Markdown emphasis patterns (Telegram uses __text__ for bold and *text* / _text_ for italic).
_MD_EMPHASIS_PATTERNS = [
    re.compile(r"\*\*(.+?)\*\*", re.DOTALL),
    re.compile(r"__(.+?)__", re.DOTALL),
    re.compile(r"~~(.+?)~~", re.DOTALL),
]

# Lead-in tokens we explicitly drop from the cleaned title (left over after
# removing the surrounding underscores, e.g. "__tldr ... __").
_TITLE_LEAD_TOKENS = ("tldr", "tl;dr", "tl dr")


def _strip_markdown_links(text: str) -> str:
    """Replace [text](url) with just 'text'."""
    return _MD_LINK_PATTERN.sub(r"\1", text)


def _strip_markdown_emphasis(text: str) -> str:
    """Strip Telegram Markdown emphasis markers (**bold**, __bold__, ~~strike~~)."""
    out = text
    for _ in range(2):
        for pat in _MD_EMPHASIS_PATTERNS:
            out = pat.sub(r"\1", out)
    return out


def _clean_title(raw: str) -> str:
    """Final clean-up for vacancy titles parsed from TG posts."""
    s = _strip_markdown_emphasis(raw)
    s = s.strip().strip("_*-—–·• \t")
    low = s.lower()
    for token in _TITLE_LEAD_TOKENS:
        if low.startswith(token):
            s = s[len(token):].lstrip(" :—-·•_*")
            break
    return s.strip()


def parse_salary(text: str) -> tuple[
    int | None, int | None, str, str | None, str, int | None, int | None
]:
    """
    Парсит зарплату через salary_parser.parse_salary, возвращает кортеж:
      (salary_from, salary_to, salary_currency, salary_gross_type,
       salary_period, salary_from_rub, salary_to_rub)
    Все суммы — в исходной валюте, приведённые к месяцу. Период всегда 'month'.
    Если зарплата не распознана, возвращает None во всех числовых полях.
    """
    info = _parse_salary_full(text)
    if info is None:
        return None, None, "RUB", None, "month", None, None
    return (
        info.salary_from,
        info.salary_to,
        info.salary_currency,
        info.salary_gross_type,
        info.salary_period,
        info.salary_from_rub,
        info.salary_to_rub,
    )


def parse_seniority(text: str) -> str | None:
    """Возвращает все найденные уровни через запятую (например 'middle, senior')."""
    lower = text.lower()
    found = []
    for level, keywords in _SENIORITY_MAP:
        if any(k in lower for k in keywords) and level not in found:
            found.append(level)
    return ", ".join(found) if found else None


def parse_skills(text: str) -> list[str]:
    found = []
    for skill in _SKILL_KEYWORDS:
        if re.search(re.escape(skill), text, re.IGNORECASE):
            found.append(skill)
    return found[:20]


def parse_location(text: str) -> str | None:
    for pat in _LOCATION_PATTERNS:
        m = pat.search(text)
        if m:
            loc = m.group(1).strip() if m.lastindex else m.group(0).strip()
            return loc[:100]
    return None


def parse_company(text: str) -> str | None:
    for pat in _COMPANY_PATTERNS:
        m = pat.search(text)
        if m:
            company = m.group(1).strip()[:200]
            # Strip Markdown link format [Company Name](url) → Company Name
            company = _strip_markdown_links(company)
            # And drop emphasis markers like __Company__ → Company.
            company = _strip_markdown_emphasis(company).strip().strip("_*")
            return company or None
    return None


def extract_title(text: str) -> str:
    """Берём первую непустую строку как заголовок вакансии."""
    # First strip Markdown emphasis on the entire text so __tldr ...__ becomes
    # a plain line and the regex below doesn't preserve underscores.
    cleaned_text = _strip_markdown_emphasis(text)
    for line in cleaned_text.strip().splitlines():
        clean = re.sub(r"[^\w\s\-\+\./,()А-Яа-яёЁ]", "", line).strip()
        clean = _clean_title(clean)
        if len(clean) > 5:
            return clean[:300]
    # Fallback: первые 80 символов первой строки
    first_line = cleaned_text.strip().splitlines()[0] if cleaned_text.strip() else "Вакансия"
    return _clean_title(first_line)[:300] or "Вакансия"


def is_vacancy_message(text: str) -> bool:
    """Грубая проверка — похоже ли сообщение на вакансию."""
    if not text or len(text) < 50:
        return False
    lower = text.lower()
    vacancy_markers = [
        "вакансия", "ищем", "требуется", "нужен", "нужна", "открыта позиция",
        "job", "vacancy", "hiring", "analyst", "аналитик", "разработчик",
        "developer", "engineer", "инженер", "менеджер", "manager",
        "опыт", "зарплата", "salary", "обязанности", "требования",
        "откликнуться", "резюме", "cv", "hh.ru", "t.me", "career",
    ]
    return sum(1 for m in vacancy_markers if m in lower) >= 2


def contains_multiple_vacancies(text: str) -> bool:
    """Определяет, что в одном посте перечислено несколько вакансий (такие посты пропускаем)."""
    if not text or len(text) < 100:
        return False
    # Нумерованные блоки вакансий: "1. ... 2. ... 3. ..." или "Вакансия 1 / 2 / 3"
    numbered_vacancy = re.compile(
        r"(?:^|\n)\s*(?:\d+[.)]\s*|ваканси[яи]\s*\d+|#\d+)\s*[:\-]?\s*"
        r".{20,200}(?:ваканси|ищем|требуется|нужен|нужна|hiring|job)",
        re.IGNORECASE | re.MULTILINE,
    )
    if len(numbered_vacancy.findall(text)) >= 2:
        return True
    # Несколько явных заголовков "Вакансия:" или "Ищем:" в разных местах (разделены переносами)
    parts = re.split(r"\n\s*\n", text)
    vacancy_headers = [
        p.strip()
        for p in parts
        if re.search(r"^(ваканси[яи]|ищем|требуется|открыта позиция)\s*[:\-]", p[:80], re.IGNORECASE)
    ]
    if len(vacancy_headers) >= 2:
        return True
    # Маркеры "• Вакансия" или "— Вакансия" повторяются 2+ раз
    bullet_vacancy = re.compile(r"(?:^|\n)\s*[•\-*]\s*(?:ваканси|ищем|требуется)", re.IGNORECASE | re.MULTILINE)
    if len(bullet_vacancy.findall(text)) >= 2:
        return True
    return False


def parse_message(msg_id: int, text: str, date, channel: str, source_uuid: str) -> dict | None:
    """Парсим одно сообщение в структуру вакансии. channel — юзернейм канала без @."""
    if not is_vacancy_message(text):
        return None
    if contains_multiple_vacancies(text):
        return None

    title      = extract_title(text)
    company    = parse_company(text)
    location   = parse_location(text)
    (
        salary_from,
        salary_to,
        currency,
        gross_type,
        period,
        salary_from_rub,
        salary_to_rub,
    ) = parse_salary(text)
    seniority  = parse_seniority(text)
    skills     = parse_skills(text)
    # Кнопка «Откликнуться на источнике» ведёт на пост в Telegram; ссылки из текста (hh.ru и т.д.) остаются в description.
    canonical_url = f"https://t.me/{channel}/{msg_id}"

    published_at = date.isoformat() if date else None

    return {
        "source_id":         source_uuid,
        "external_id":       f"tg_{channel}_{msg_id}",
        "title":             title,
        "company":           company or "Не указано",
        "canonical_url":     canonical_url,
        "location":          location,
        "salary_from":       salary_from,
        "salary_to":         salary_to,
        "salary_currency":   currency,
        "salary_period":     period,
        "salary_gross_type": gross_type,
        "salary_from_rub":   salary_from_rub,
        "salary_to_rub":     salary_to_rub,
        "seniority":         seniority,
        "employment_type":   None,
        "description":       text[:4000],
        "skills":            skills,
        "status":            "active",
        "published_at":      published_at,
    }
