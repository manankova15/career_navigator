#!/usr/bin/env python3
"""
Backfill классификационных полей у канонических вакансий.

Старые сидеры (`seed_hh_vacancies.py`, `seed_telegram_vacancies.py`) и ранние
версии нормализатора заливали в БД только базовые поля и оставляли пустыми
`profession_area`, `specialization`, `location_city`, `location_country`,
`work_format`, `employment_type`, `schedule_type`, `experience_level`,
`seniority`, `english_level`, `education_level`. Из-за этого фильтры в поиске
вакансий ничего не находят.

Скрипт проходит по `canonical_vacancies` и заполняет недостающие поля на
основе уже сохранённых `title`, `description`, `location`, `skills`. Запуск
безопасный и идемпотентный: уже заполненные значения не перезаписываются.

Запуск (из корня проекта, при работающих сервисах):

    python scripts/backfill_classification.py

Можно ограничить выборку только устаревшими записями:

    python scripts/backfill_classification.py --only-empty

По умолчанию работает в режиме `--only-empty`. Чтобы пересчитать всё
(в т. ч. перезаписать неверно классифицированное), используйте `--all`.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import String

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from salary_parser import (  # noqa: E402
    compute_rub_amounts,
    normalize_period_to_month,
    parse_salary,
)


def _load_env() -> None:
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


# ── Классификаторы (синхронизированы с workers/ingestion-workers/app/vacancy_norm.py)


HH_EXPERIENCE_TO_LEVEL = {
    "noExperience": "no_experience",
    "between1And3": "1_3_years",
    "between3And6": "3_6_years",
    "moreThan6": "6_plus_years",
}

HH_EXPERIENCE_TO_SENIORITY = {
    "noExperience": "intern",
    "between1And3": "junior",
    "between3And6": "middle",
    "moreThan6": "senior",
}


def classify_profession_area(text_blob: str, title: str | None = None) -> str | None:
    """
    Возвращает категорию (`profession_area`) по тексту вакансии.

    Сначала пытаемся определить по title — он самый точный сигнал. Если из title
    ничего не извлекли, ищем по всему тексту (title + description + skills + …).
    """
    rules: list[tuple[tuple[str, ...], str]] = [
        (
            (
                "developer",
                "software",
                "backend",
                "frontend",
                "fullstack",
                "full stack",
                "devops",
                "разработчик",
                "программист",
                "инженер по тест",
                "qa ",
                " qa",
                "тестировщик",
                "системный админ",
                "sre",
                "site reliability",
                "data engineer",
                "ml engineer",
                "machine learning engineer",
            ),
            "it",
        ),
        (
            (
                "analyst",
                "аналитик",
                "data scientist",
                "bi ",
                " bi",
                "business analyst",
                "product analyst",
                "data analyst",
            ),
            "analytics",
        ),
        (("finance", "финанс", "казначей", "investment", "инвест", "treasury"), "finance"),
        (("accountant", "бухгалтер", "бухгалтерия"), "accounting"),
        (("маркетолог", "marketing", "performance", "seo", "smm", "growth"), "marketing"),
        (("sales", "продаж", "менеджер по продаж", "account executive"), "sales"),
        (("product manager", "продакт", "product owner", "продуктовый менеджер"), "product"),
        (
            ("project manager", "проектный менеджер", "scrum master", "delivery manager"),
            "project_management",
        ),
        (("designer", " ux", " ui", "дизайнер", "иллюстратор"), "design"),
        (("recruiter", " hr", "кадр", "персонал", "hrbp", "talent"), "hr"),
        (("lawyer", "юрист", "legal counsel", "юридический"), "legal"),
        (("support", "поддержк", "customer support", "клиентский сервис", "helpdesk"), "customer_support"),
        (("операци", "operations", "операционный директор", "coo"), "operations"),
        (("логист", "logistics", "supply chain"), "logistics"),
        (("администратор", "administration", "офис-менеджер"), "administration"),
        (("образован", "teacher", "преподав", "education", "tutor", "учитель"), "education"),
        (("медицин", "врач", "nurse", "medicine", "медсестр"), "medicine"),
    ]

    def _match(text: str) -> str | None:
        for needles, area in rules:
            if any(n in text for n in needles):
                return area
        if ("инженер" in text or "engineer" in text) and not any(
            x in text for x in ("software", "разработчик", "developer", "программист")
        ):
            return "engineering"
        return None

    title_low = (title or "").lower()
    if title_low:
        title_match = _match(title_low)
        if title_match:
            return title_match
    blob_low = (text_blob or "").lower()
    if not blob_low:
        return None
    return _match(blob_low) or "other"


def classify_specialization(text_blob: str, title: str | None = None) -> str | None:
    """
    Определяет специализацию (`specialization`) для вакансии.

    Чтобы не путать backend/frontend/fullstack по описаниям, в которых
    упоминаются оба слова, сначала проверяем title. Если из title ничего не
    извлеклось — переходим к полному тексту. Внутри списка более узкие правила
    (fullstack, frontend) идут раньше backend, чтобы корректно классифицировать
    смешанные описания.
    """
    pairs: list[tuple[tuple[str, ...], str]] = [
        (("fullstack", "full stack", "full-stack", "фулстек", "фулстак"), "fullstack_developer"),
        (("frontend", "front end", "front-end", "react developer", "vue developer", "фронтенд", "фронт-енд"), "frontend_developer"),
        (("backend", "back end", "back-end", "python developer", "java developer", "бэкенд", "backend developer"), "backend_developer"),
        (("qa", "test engineer", "тестировщик"), "qa_engineer"),
        (("devops", "sre", "site reliability"), "devops_engineer"),
        (("data analyst", "аналитик данных"), "data_analyst"),
        (
            ("business analyst", "бизнес-аналитик", "системный аналитик"),
            "business_analyst",
        ),
        (("system analyst",), "system_analyst"),
        (("financial analyst", "финансовый аналитик"), "financial_analyst"),
        (("бухгалтер", "accountant"), "accountant"),
        (("интернет-маркетолог", "digital marketing"), "internet_marketer"),
        (("performance маркетолог", "performance marketer"), "performance_marketer"),
        (("sales manager", "менеджер по продаж"), "sales_manager"),
        (("account manager", "аккаунт-менеджер"), "account_manager"),
        (("product manager", "продакт-менеджер", "продуктовый менеджер"), "product_manager"),
        (("project manager", "проектный менеджер"), "project_manager"),
        (("ui/ux", "ux designer", "ui designer"), "ui_ux_designer"),
        (("graphic designer", "графический дизайн"), "graphic_designer"),
        (("recruiter", "рекрутер"), "recruiter"),
        (("lawyer", "юрист"), "lawyer"),
        (("support", "поддержк", "helpdesk"), "support_specialist"),
    ]

    def _match(text: str) -> str | None:
        for needles, spec in pairs:
            if any(n in text for n in needles):
                return spec
        return None

    title_low = (title or "").lower()
    if title_low:
        title_match = _match(title_low)
        if title_match:
            return title_match
    blob_low = (text_blob or "").lower()
    if not blob_low:
        return None
    return _match(blob_low)


def infer_work_format(text_blob: str) -> list[str]:
    t = (text_blob or "").lower()
    if not t:
        return []
    fm: list[str] = []
    if any(x in t for x in ("удален", "удалён", "remote", "дистанцион", "работа из дома")):
        fm.append("remote")
    if "гибрид" in t or "hybrid" in t:
        fm.append("hybrid")
    if any(x in t for x in ("офис", "на территории работодателя", "office", "работа в офисе")):
        fm.append("office")
    if any(x in t for x in ("разъезд", "выездн", "field")):
        fm.append("field")
    if not fm:
        return []
    priority = ["remote", "hybrid", "office", "field"]
    ordered = [p for p in priority if p in fm]
    return ordered or fm


def infer_schedule_type(text_blob: str) -> str | None:
    t = (text_blob or "").lower()
    if not t:
        return None
    if "вахт" in t:
        return "watch"
    if "по выходным" in t or ("выходн" in t and "график" in t):
        return "weekend"
    if "сменн" in t or "смен ный" in t or "shift" in t:
        return "shift"
    if "гибк" in t or "flexible" in t:
        return "flexible"
    if "полный день" in t or "полная занятость" in t or "full day" in t:
        return "full_day"
    if any(x in t for x in ("5/2", "2/2", "3/3", "сутки через")):
        return "custom"
    return None


def infer_employment_type(text_blob: str) -> list[str] | None:
    t = (text_blob or "").lower()
    if not t:
        return None
    out: list[str] = []
    if "полная занятость" in t or "full-time" in t or "full time" in t:
        out.append("full_time")
    if "частичная занятость" in t or "part-time" in t or "part time" in t:
        out.append("part_time")
    if "стажир" in t or "internship" in t or "trainee" in t:
        out.append("internship")
    if "проектная работа" in t or "проектная занятость" in t:
        out.append("project")
    if "волонт" in t or "volunteer" in t:
        out.append("volunteering")
    if "временная работа" in t or "temporary" in t:
        out.append("temporary")
    if "гпх" in t or "по контракту" in t or "contract" in t:
        out.append("contract")
    return out or None


def infer_experience_level(text_blob: str, seniority: str | None) -> str | None:
    t = (text_blob or "").lower()
    if "без опыта" in t or "no experience" in t:
        return "no_experience"
    if re.search(r"опыт\s+от\s*1\D", t) or "1-3 год" in t or "от 1 до 3" in t:
        return "1_3_years"
    if re.search(r"опыт\s+от\s*3\D", t) or "3-6 лет" in t or "от 3 до 6" in t:
        return "3_6_years"
    if "от 6 лет" in t or "более 6" in t or "6+" in t:
        return "6_plus_years"
    seniority_map = {
        "intern": "no_experience",
        "trainee": "no_experience",
        "junior": "1_3_years",
        "middle": "3_6_years",
        "senior": "6_plus_years",
        "lead": "6_plus_years",
        "principal": "6_plus_years",
    }
    if seniority:
        for level in (s.strip().lower() for s in seniority.split(",")):
            if level in seniority_map:
                return seniority_map[level]
    return None


def infer_seniority(text_blob: str) -> str | None:
    t = (text_blob or "").lower()
    found: list[str] = []
    rules = [
        ("intern", ("стажёр", "стажер", "intern", "trainee")),
        ("junior", ("junior", "джун", "джуниор", "начинающий")),
        ("middle", ("middle", "мидл", "миддл")),
        ("senior", ("senior", "сеньор", "ведущий")),
        ("lead", ("lead", "лид", "principal", "staff", "архитектор", "руководитель")),
    ]
    for level, kws in rules:
        if any(k in t for k in kws) and level not in found:
            found.append(level)
    return ", ".join(found) if found else None


def infer_english_level(text_blob: str) -> str | None:
    t = (text_blob or "").lower()
    if "английск" in t and ("не треб" in t or "не нужен" in t or "не обязател" in t):
        return "not_required"
    for level in ("c2", "c1", "b2", "b1", "a2", "a1"):
        if re.search(rf"\b{level}\b", t, re.I):
            return level
    if "upper-intermediate" in t or "upper intermediate" in t:
        return "b2"
    if "intermediate" in t:
        return "b1"
    if "advanced" in t or "fluent" in t:
        return "c1"
    return None


def infer_education_level(text_blob: str) -> str | None:
    t = (text_blob or "").lower()
    if "образован" in t and ("не треб" in t or "не важн" in t):
        return "not_required"
    if "магистр" in t or "master" in t:
        return "master"
    if "бакалавр" in t or "bachelor" in t:
        return "bachelor"
    if "среднее специальное" in t or "колледж" in t:
        return "specialized_secondary"
    if "высшее образование" in t or "высшее" in t:
        return "higher"
    if "среднее образование" in t or re.search(r"\bсреднее\b", t):
        return "secondary"
    return None


# ── Локация ──

_REMOTE_LOCATION_TOKENS = {
    "remote",
    "удалённо",
    "удаленно",
    "удалённая",
    "удаленная",
    "дистанционно",
    "дистанционная",
    "anywhere",
    "worldwide",
}

_RUSSIAN_CITIES = {
    "москва",
    "санкт-петербург",
    "спб",
    "питер",
    "новосибирск",
    "екатеринбург",
    "казань",
    "нижний новгород",
    "челябинск",
    "самара",
    "омск",
    "ростов-на-дону",
    "уфа",
    "красноярск",
    "пермь",
    "воронеж",
    "волгоград",
    "краснодар",
    "саратов",
    "тюмень",
    "тольятти",
    "ижевск",
    "барнаул",
    "ульяновск",
    "иркутск",
    "хабаровск",
    "ярославль",
    "владивосток",
    "махачкала",
    "томск",
    "оренбург",
    "кемерово",
    "новокузнецк",
    "рязань",
    "астрахань",
    "набережные челны",
    "пенза",
    "липецк",
    "тула",
    "киров",
    "чебоксары",
    "калининград",
    "брянск",
    "курск",
    "иваново",
    "магнитогорск",
    "тверь",
    "ставрополь",
    "симферополь",
    "белгород",
    "архангельск",
    "владимир",
    "сочи",
    "курган",
}

_COUNTRY_HINTS: list[tuple[str, str]] = [
    ("россия", "Россия"),
    ("russia", "Россия"),
    ("беларус", "Беларусь"),
    ("belarus", "Беларусь"),
    ("украин", "Украина"),
    ("ukraine", "Украина"),
    ("казахстан", "Казахстан"),
    ("kazakhstan", "Казахстан"),
    ("узбекистан", "Узбекистан"),
    ("кипр", "Кипр"),
    ("cyprus", "Кипр"),
    ("польша", "Польша"),
    ("poland", "Польша"),
    ("грузи", "Грузия"),
    ("georgia", "Грузия"),
    ("армени", "Армения"),
    ("armenia", "Армения"),
    ("сербия", "Сербия"),
    ("serbia", "Сербия"),
    ("турция", "Турция"),
    ("turkey", "Турция"),
    ("израиль", "Израиль"),
    ("israel", "Израиль"),
    ("эстония", "Эстония"),
    ("estonia", "Эстония"),
    ("латвия", "Латвия"),
    ("latvia", "Латвия"),
    ("литва", "Литва"),
    ("lithuania", "Литва"),
    ("uae", "ОАЭ"),
    ("оаэ", "ОАЭ"),
    ("dubai", "ОАЭ"),
    ("дубай", "ОАЭ"),
    ("usa", "США"),
    ("united states", "США"),
    ("сша", "США"),
    ("germany", "Германия"),
    ("германия", "Германия"),
]


def split_location(location: str | None) -> tuple[str | None, str | None]:
    """Возвращает (city, country) на основе текста location.

    Простая эвристика: убираем хэштеги/маркеры, нормализуем разделители,
    ищем известные города и страны."""
    if not location:
        return None, None
    raw = location.strip()
    if not raw:
        return None, None

    cleaned = re.sub(r"[#@]", "", raw).strip()
    low = cleaned.lower()

    if any(token in low for token in _REMOTE_LOCATION_TOKENS):
        # Удалёнка — отдельной локации нет.
        return None, None

    parts = [p.strip() for p in re.split(r"[,/|;]| - | – ", cleaned) if p.strip()]
    parts_low = [p.lower() for p in parts]

    city: str | None = None
    country: str | None = None

    for token, country_label in _COUNTRY_HINTS:
        if any(token in p for p in parts_low):
            country = country_label
            break

    for part_idx, part_low in enumerate(parts_low):
        for known_city in _RUSSIAN_CITIES:
            if known_city == part_low or known_city in part_low.split():
                city = parts[part_idx].title()
                if not country:
                    country = "Россия"
                break
        if city:
            break

    if city is None and parts:
        head = parts[0]
        head_low = head.lower()
        # «Город (область)» — взять левую часть как город
        if 2 <= len(head) <= 60 and not any(
            t in head_low for t in _REMOTE_LOCATION_TOKENS
        ):
            city = head.title()

    return city, country


# ── DB пайплайн ──


def _recompute_salary_for_row(row) -> dict | None:
    """Пересчёт salary_*: новый parse_salary при подозрительной валюте/мусоре; иначе месяц + RUB; None если без изменений"""
    text_blob = " ".join(p for p in (row.title, row.description) if p)

    parsed = parse_salary(text_blob)

    if parsed is not None:
        return {
            "id": row.id,
            "salary_from": parsed.salary_from,
            "salary_to": parsed.salary_to,
            "salary_currency": parsed.salary_currency,
            "salary_period": parsed.salary_period,
            "salary_gross_type": parsed.salary_gross_type or row.salary_gross_type,
            "salary_from_rub": parsed.salary_from_rub,
            "salary_to_rub": parsed.salary_to_rub,
        }

    # Парсер из текста ничего не выудил — приводим к месяцу/RUB существующие
    # значения (если они есть).
    if row.salary_from is None and row.salary_to is None:
        return None

    sf, st, period = normalize_period_to_month(
        row.salary_from, row.salary_to, row.salary_period
    )
    sf_rub, st_rub = compute_rub_amounts(sf, st, row.salary_currency or "RUB")

    return {
        "id": row.id,
        "salary_from": sf,
        "salary_to": st,
        "salary_currency": row.salary_currency or "RUB",
        "salary_period": period or "month",
        "salary_gross_type": row.salary_gross_type,
        "salary_from_rub": sf_rub,
        "salary_to_rub": st_rub,
    }


def _run_salary_recompute(engine, batch_size: int) -> int:
    """Бэкфилл всех зарплатных полей по новой логике."""
    select_sql = text(
        """
        SELECT id, title, description, salary_from, salary_to, salary_currency,
               salary_period, salary_gross_type
        FROM canonical_vacancies
        ORDER BY created_at DESC
        """
    )

    update_sql = text(
        """
        UPDATE canonical_vacancies SET
            salary_from = :salary_from,
            salary_to = :salary_to,
            salary_currency = :salary_currency,
            salary_period = :salary_period,
            salary_gross_type = :salary_gross_type,
            salary_from_rub = :salary_from_rub,
            salary_to_rub = :salary_to_rub,
            updated_at = now()
        WHERE id = :id
        """
    )

    started = time.time()
    updated = scanned = 0

    with engine.connect() as read_conn, engine.connect() as write_conn:
        result = read_conn.execution_options(stream_results=True).execute(select_sql)
        batch: list[dict] = []
        for row in result:
            scanned += 1
            payload = _recompute_salary_for_row(row)
            if payload is None:
                continue
            batch.append(payload)
            if len(batch) >= batch_size:
                write_conn.execute(update_sql, batch)
                write_conn.commit()
                updated += len(batch)
                print(f"[salary] processed {scanned} / updated {updated}")
                batch.clear()
        if batch:
            write_conn.execute(update_sql, batch)
            write_conn.commit()
            updated += len(batch)

    elapsed = time.time() - started
    print(
        f"[salary] done: scanned={scanned} updated={updated} took={elapsed:.1f}s"
    )
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill canonical vacancies classification")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--only-empty",
        action="store_true",
        help="Заполнять только NULL поля (по умолчанию)",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        help="Перезаписывать все поля заново (даже уже заполненные)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Размер пачки для коммита",
    )
    parser.add_argument(
        "--recompute-salary",
        action="store_true",
        help=(
            "Пересчитать зарплатные поля у всех вакансий через новый парсер "
            "(переразобрать текст, привести к месяцу, посчитать RUB-эквивалент). "
            "Полезно после миграции 003 и при подозрении на ошибки парсинга."
        ),
    )
    parser.add_argument(
        "--only-salary",
        action="store_true",
        help="Запустить только пересчёт зарплат, без классификации.",
    )
    args = parser.parse_args()

    overwrite = bool(args.all)

    _load_env()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Локальный порт вне docker-compose
        db_url = (
            "postgresql://"
            f"{os.getenv('POSTGRES_USER', 'career_navigator')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'change_me')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'career_navigator')}"
        )

    print(f"[backfill] connecting to: {db_url.split('@')[-1]}")
    engine = create_engine(db_url, future=True)

    if args.recompute_salary or args.only_salary:
        _run_salary_recompute(engine, args.batch_size)
        if args.only_salary:
            return 0

    select_sql = text(
        """
        SELECT id, title, company, description, location,
               profession_area, specialization, location_city, location_country,
               work_format, employment_type, schedule_type, experience_level,
               seniority, english_level, education_level, skills
        FROM canonical_vacancies
        ORDER BY created_at DESC
        """
    )

    update_sql = text(
        """
        UPDATE canonical_vacancies SET
            profession_area = :profession_area,
            specialization = :specialization,
            location_city = :location_city,
            location_country = :location_country,
            work_format = :work_format,
            employment_type = :employment_type,
            schedule_type = :schedule_type,
            experience_level = :experience_level,
            seniority = :seniority,
            english_level = :english_level,
            education_level = :education_level,
            updated_at = now()
        WHERE id = :id
        """
    ).bindparams(
        bindparam("work_format", type_=ARRAY(String)),
        bindparam("employment_type", type_=ARRAY(String)),
    )

    started = time.time()
    updated = scanned = 0

    # Читаем и пишем в разных соединениях, чтобы стрим выборки не мешал коммитам.
    with engine.connect() as read_conn, engine.connect() as write_conn:
        result = read_conn.execution_options(stream_results=True).execute(select_sql)
        batch: list[dict] = []

        for row in result:
            scanned += 1
            skills_text = " ".join(row.skills or [])
            blob_parts = [row.title, row.company, row.description, row.location, skills_text]
            blob = " ".join(p for p in blob_parts if p)

            new_pa = (
                classify_profession_area(blob, row.title)
                if (overwrite or not row.profession_area)
                else row.profession_area
            )
            new_spec = (
                classify_specialization(blob, row.title)
                if (overwrite or not row.specialization)
                else row.specialization
            )
            new_seniority = (
                infer_seniority(blob)
                if (overwrite or not row.seniority)
                else row.seniority
            )
            new_exp = (
                infer_experience_level(blob, new_seniority)
                if (overwrite or not row.experience_level)
                else row.experience_level
            )
            new_wf = (
                infer_work_format(blob)
                if (overwrite or not (row.work_format or []))
                else list(row.work_format or [])
            )
            new_emp = (
                infer_employment_type(blob)
                if (overwrite or not (row.employment_type or []))
                else list(row.employment_type or [])
            )
            new_sched = (
                infer_schedule_type(blob)
                if (overwrite or not row.schedule_type)
                else row.schedule_type
            )
            new_eng = (
                infer_english_level(blob)
                if (overwrite or not row.english_level)
                else row.english_level
            )
            new_edu = (
                infer_education_level(blob)
                if (overwrite or not row.education_level)
                else row.education_level
            )

            need_city = overwrite or not row.location_city
            need_country = overwrite or not row.location_country
            if need_city or need_country:
                city_guess, country_guess = split_location(row.location)
                new_city = city_guess if need_city else row.location_city
                new_country = country_guess if need_country else row.location_country
            else:
                new_city = row.location_city
                new_country = row.location_country

            batch.append(
                {
                    "id": row.id,
                    "profession_area": new_pa,
                    "specialization": new_spec,
                    "location_city": new_city,
                    "location_country": new_country,
                    "work_format": new_wf or [],
                    "employment_type": new_emp,
                    "schedule_type": new_sched,
                    "experience_level": new_exp,
                    "seniority": new_seniority,
                    "english_level": new_eng,
                    "education_level": new_edu,
                }
            )

            if len(batch) >= args.batch_size:
                write_conn.execute(update_sql, batch)
                write_conn.commit()
                updated += len(batch)
                print(f"[backfill] processed {scanned} / updated {updated}")
                batch.clear()

        if batch:
            write_conn.execute(update_sql, batch)
            write_conn.commit()
            updated += len(batch)

    elapsed = time.time() - started
    print(
        f"[backfill] done: scanned={scanned} updated={updated} "
        f"mode={'overwrite' if overwrite else 'only-empty'} took={elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
