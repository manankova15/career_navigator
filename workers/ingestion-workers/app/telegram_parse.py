"""Парсинг сообщений TG в поля вакансии (синхронизировано с scripts/seed_telegram_vacancies.py)."""
from __future__ import annotations

import re
# Паттерны для поиска зарплаты: "100 000 – 150 000 ₽", "от 80к", "up to $5000" и т.п.
_SALARY_PATTERNS = [
    # "100 000 – 200 000 ₽" / "100 000 - 200 000 руб"
    re.compile(
        r"(?P<from>\d[\d\s]{2,8}\d)\s*[-–—]\s*(?P<to>\d[\d\s]{2,8}\d)\s*"
        r"(?P<currency>[₽$€]|руб(?:лей)?|rub|usd|eur)",
        re.IGNORECASE,
    ),
    # "от 150 000 ₽" / "от 150к"
    re.compile(
        r"от\s+(?P<from>\d[\d\s]*\d?к?)\s*(?P<currency>[₽$€]|руб(?:лей)?|rub|usd|eur)?",
        re.IGNORECASE,
    ),
    # "до 200 000 ₽"
    re.compile(
        r"до\s+(?P<to>\d[\d\s]*\d?к?)\s*(?P<currency>[₽$€]|руб(?:лей)?|rub|usd|eur)?",
        re.IGNORECASE,
    ),
    # "150 000 ₽"  (одиночная сумма со знаком валюты)
    re.compile(
        r"(?P<from>\d[\d\s]{3,8})\s*(?P<currency>[₽$€])",
        re.IGNORECASE,
    ),
]

_CURRENCY_MAP = {
    "₽": "RUB", "руб": "RUB", "рублей": "RUB", "rub": "RUB",
    "$": "USD", "usd": "USD",
    "€": "EUR", "eur": "EUR",
}

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


def _strip_markdown_links(text: str) -> str:
    """Replace [text](url) with just 'text'."""
    return _MD_LINK_PATTERN.sub(r"\1", text)


def _clean_number(s: str) -> int | None:
    """Убираем пробелы и 'к', переводим в число."""
    if s is None:
        return None
    s = s.replace(" ", "").replace("\u00a0", "")
    if s.endswith("к") or s.endswith("k"):
        try:
            return int(float(s[:-1]) * 1000)
        except ValueError:
            return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_salary(text: str) -> tuple[int | None, int | None, str]:
    for pat in _SALARY_PATTERNS:
        m = pat.search(text)
        if m:
            gd = m.groupdict()
            salary_from = _clean_number(gd.get("from"))
            salary_to   = _clean_number(gd.get("to"))
            raw_cur     = (gd.get("currency") or "").strip().lower()
            currency    = _CURRENCY_MAP.get(raw_cur, "RUB")
            if salary_from or salary_to:
                return salary_from, salary_to, currency
    return None, None, "RUB"


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
            company = _strip_markdown_links(company).strip()
            return company or None
    return None


def extract_title(text: str) -> str:
    """Берём первую непустую строку как заголовок вакансии."""
    for line in text.strip().splitlines():
        clean = re.sub(r"[^\w\s\-\+\./,()А-Яа-яёЁ]", "", line).strip()
        if len(clean) > 5:
            return clean[:300]
    # Fallback: первые 80 символов первой строки
    first_line = text.strip().splitlines()[0] if text.strip() else "Вакансия"
    return first_line[:300]


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
    salary_from, salary_to, currency = parse_salary(text)
    seniority  = parse_seniority(text)
    skills     = parse_skills(text)
    # Кнопка «Откликнуться на источнике» ведёт на пост в Telegram; ссылки из текста (hh.ru и т.д.) остаются в description.
    canonical_url = f"https://t.me/{channel}/{msg_id}"

    published_at = date.isoformat() if date else None

    return {
        "source_id":       source_uuid,
        "external_id":     f"tg_{channel}_{msg_id}",
        "title":           title,
        "company":         company or "Не указано",
        "canonical_url":   canonical_url,
        "location":        location,
        "salary_from":     salary_from,
        "salary_to":       salary_to,
        "salary_currency": currency,
        "seniority":       seniority,
        "employment_type": None,
        "description":     text[:4000],
        "skills":          skills,
        "status":          "active",
        "published_at":    published_at,
    }
