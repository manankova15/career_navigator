"""
Нормализация полей вакансии и авто-классификация по ТЗ (plans/обновленный_профиль.md).
"""

from __future__ import annotations

import re
from typing import Any

SKILL_KEYWORDS: list[tuple[str, str]] = [
    ("python", "Python"),
    ("javascript", "JavaScript"),
    (" c++ ", "C++"),
    (" sql ", "SQL"),
    (" html ", "HTML"),
    (" css ", "CSS"),
    ("mysql", "MySQL"),
    ("postgresql", "PostgreSQL"),
    ("oracle", "ORACLE"),
    (" cte ", "CTE"),
    (" ddl ", "DDL"),
    (" join ", "JOIN"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scikit-learn", "scikit-learn"),
    ("seaborn", "seaborn"),
    (" react", "React"),
    ("next.js", "Next.js"),
    ("node.js", "Node.js"),
    ("express", "Express"),
    ("selenium", "Selenium"),
    ("webpack", "Webpack"),
    ("helm", "Helm"),
    (" git ", "Git"),
    ("docker", "Docker"),
    ("kubernetes", "Kubernetes"),
    ("jenkins", "Jenkins"),
    ("openshift", "OpenShift"),
    ("terraform", "Terraform"),
    ("prometheus", "Prometheus"),
    ("linux", "Linux"),
    ("ci/cd", "CI/CD"),
    (" iac ", "IaC"),
    ("devops", "DevOps"),
    (" bgp ", "BGP"),
    (" dns ", "DNS"),
    (" http ", "HTTP"),
    (" icmp ", "ICMP"),
    (" ip ", "IP"),
    ("ipv4", "IPv4"),
    ("ipv6", "IPv6"),
    ("tcp/ip", "TCP/IP"),
    (" nat ", "NAT"),
    (" vpn ", "VPN"),
    (" osi ", "OSI"),
    (" cidr ", "CIDR"),
    (" rest ", "REST"),
    ("rest api", "REST API"),
    ("graphql", "GraphQL"),
    (" api ", "API"),
    ("ms office", "MS Office"),
    ("ms excel", "MS Excel"),
    ("ооп", "ООП"),
    (" bdd ", "BDD"),
    (" dom ", "DOM"),
    ("event loop", "Event Loop"),
    ("raii", "RAII"),
    (" stl ", "STL"),
    ("big o", "Big O"),
    ("flexbox", "Flexbox"),
    (" ssr ", "SSR"),
    ("owasp", "OWASP"),
    ("wcag", "WCAG"),
    ("web security", "Web Security"),
    ("криптография", "Криптография"),
    ("аутентификация", "Аутентификация"),
    (" ml ", "ML"),
    ("глубокое обучение", "Глубокое обучение"),
    ("нейронные сети", "Нейронные сети"),
    ("регрессия", "Регрессия"),
    ("классификация", "Классификация"),
    ("кластеризация", "Кластеризация"),
    ("ансамблевые методы", "Ансамблевые методы"),
    ("регуляризация", "Регуляризация"),
    ("transfer learning", "Transfer learning"),
    ("bias-variance tradeoff", "Bias-variance tradeoff"),
    ("a/b-тестирование", "A/B-тестирование"),
    ("линейная алгебра", "Линейная алгебра"),
    ("теория вероятностей", "Теория вероятностей"),
    ("математическая статистика", "Математическая статистика"),
    ("временные ряды", "Временные ряды"),
    (" bi ", "BI"),
    ("mocking", "Mocking"),
    ("юнит-тестирование", "Юнит-тестирование"),
    ("тест-дизайн", "Тест-дизайн"),
    ("ui-дизайн", "UI-дизайн"),
    ("ux-дизайн", "UX-дизайн"),
    ("ux-исследования", "UX-исследования"),
    ("accessibility", "Accessibility"),
    ("design systems", "Design systems"),
    ("эвристики нильсена", "Эвристики Нильсена"),
    ("прототипирование", "Прототипирование"),
    ("микросервисы", "Микросервисы"),
    ("шаблоны проектирования", "Шаблоны проектирования"),
    ("функциональное программирование", "Функциональное программирование"),
    ("динамическое программирование", "Динамическое программирование"),
    ("виртуализация", "Виртуализация"),
    (" aws ", "AWS"),
    ("message brokers", "Message brokers"),
]

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

HH_EMPLOYMENT_TO_NORM = {
    "full": "full_time",
    "part": "part_time",
    "project": "project",
    "volunteer": "volunteering",
    "probation": "internship",
}

HH_SCHEDULE_TO_NORM = {
    "fullDay": "full_day",
    "shift": "shift",
    "flexible": "flexible",
    "flyInFlyOut": "watch",
}


def _norm_text(*parts: str | None) -> str:
    return " ".join(p for p in parts if p).lower()


def extract_skills_from_text(text: str, existing: list[str]) -> list[str]:
    low = text.lower()
    found: dict[str, str] = {s.lower(): s for s in existing}
    for needle, label in SKILL_KEYWORDS:
        if needle in low and label.lower() not in found:
            found[label.lower()] = label
    return list(found.values())[:30]


def map_employment(employment_id: str | None, employment_name: str | None) -> list[str] | None:
    if employment_id and employment_id in HH_EMPLOYMENT_TO_NORM:
        return [HH_EMPLOYMENT_TO_NORM[employment_id]]
    name = (employment_name or "").lower()
    if not name:
        return None
    out: list[str] = []
    if "полная" in name:
        out.append("full_time")
    if "частич" in name:
        out.append("part_time")
    if "стажир" in name or "probation" in name:
        out.append("internship")
    if "проект" in name:
        out.append("project")
    if "волонт" in name:
        out.append("volunteering")
    if "времен" in name:
        out.append("temporary")
    if "гпх" in name or "контракт" in name:
        out.append("contract")
    return out or None


def infer_work_format(text: str) -> list[str]:
    t = text.lower()
    fm: list[str] = []
    if any(
        x in t
        for x in (
            "удален",
            "удалён",
            "remote",
            "дистанцион",
            "работа из дома",
        )
    ):
        fm.append("remote")
    if "гибрид" in t or "hybrid" in t:
        fm.append("hybrid")
    if any(
        x in t
        for x in (
            "офис",
            "на территории работодателя",
            "office",
            "работа в офисе",
        )
    ):
        fm.append("office")
    if any(x in t for x in ("разъезд", "выездн", "field")):
        fm.append("field")
    if not fm:
        return []
    priority = ["remote", "hybrid", "office", "field"]
    ordered = [p for p in priority if p in fm]
    return ordered or fm


def map_schedule(schedule_id: str | None, schedule_name: str | None) -> str | None:
    if schedule_id and schedule_id in HH_SCHEDULE_TO_NORM:
        return HH_SCHEDULE_TO_NORM[schedule_id]
    name = (schedule_name or "").lower()
    if "полн" in name and "день" in name:
        return "full_day"
    if "гибк" in name:
        return "flexible"
    if "смен" in name:
        return "shift"
    if "выходн" in name:
        return "weekend"
    if "вахт" in name:
        return "watch"
    if any(x in name for x in ("5/2", "2/2", "3/3", "сутки через")):
        return "custom"
    return None


def classify_profession_area(text: str) -> str:
    t = text.lower()
    rules: list[tuple[tuple[str, ...], str]] = [
        (
            (
                "developer",
                "software",
                "backend",
                "frontend",
                "devops",
                "разработчик",
                "программист",
                "инженер по тест",
                "qa ",
                "системный админ",
            ),
            "it",
        ),
        (
            ("analyst", "аналитик", "data scientist", "bi ", "business analyst"),
            "analytics",
        ),
        (("finance", "финанс", "казначей", "investment", "инвест"), "finance"),
        (("accountant", "бухгалтер", "бухгалтерия"), "accounting"),
        (("маркетолог", "marketing", "performance", "seo", "smm"), "marketing"),
        (("sales", "продаж", "менеджер по продаж"), "sales"),
        (("product manager", "продакт", "product owner"), "product"),
        (("project manager", "проектный менеджер", "scrum master"), "project_management"),
        (("designer", " ux", " ui", "дизайнер"), "design"),
        (("recruiter", " hr", "кадр", "персонал"), "hr"),
        (("lawyer", "юрист", "legal counsel"), "legal"),
        (("support", "поддержк", "customer support", "клиентский сервис"), "customer_support"),
        (("операци", "operations", "операционный директор"), "operations"),
        (("логист", "logistics", "supply chain"), "logistics"),
        (("администратор", "administration", "офис-менеджер"), "administration"),
        (("образован", "teacher", "преподав", "education"), "education"),
        (("медицин", "врач", "nurse", "medicine"), "medicine"),
    ]
    for needles, area in rules:
        if isinstance(needles, str):
            needles = (needles,)
        if any(n in t for n in needles):
            return area
    if ("инженер" in t or "engineer" in t) and not any(
        x in t for x in ("software", "разработчик", "developer", "программист")
    ):
        return "engineering"
    return "other"


def classify_specialization(text: str) -> str | None:
    t = text.lower()
    pairs: list[tuple[tuple[str, ...], str]] = [
        (("backend", "python developer", "java developer", "бэкенд"), "backend_developer"),
        (("frontend", "react developer", "vue developer", "фронтенд"), "frontend_developer"),
        (("fullstack", "full stack", "фулстек"), "fullstack_developer"),
        (("qa", "test engineer", "тестировщик"), "qa_engineer"),
        (("devops", "sre", "site reliability"), "devops_engineer"),
        (("data analyst", "аналитик данных"), "data_analyst"),
        (("business analyst", "бизнес-аналитик", "системный аналитик"), "business_analyst"),
        (("system analyst",), "system_analyst"),
        (("financial analyst", "финансовый аналитик"), "financial_analyst"),
        (("бухгалтер", "accountant"), "accountant"),
        (("интернет-маркетолог", "digital marketing"), "internet_marketer"),
        (("performance маркетолог", "performance marketer"), "performance_marketer"),
        (("sales manager", "менеджер по продаж"), "sales_manager"),
        (("account manager", "аккаунт-менеджер"), "account_manager"),
        (("product manager", "продакт-менеджер"), "product_manager"),
        (("project manager", "проектный менеджер"), "project_manager"),
        (("ui/ux", "ux designer", "ui designer"), "ui_ux_designer"),
        (("graphic designer", "графический дизайн"), "graphic_designer"),
        (("recruiter", "рекрутер"), "recruiter"),
        (("lawyer", "юрист"), "lawyer"),
        (("support", "поддержк", "helpdesk"), "support_specialist"),
    ]
    for needles, spec in pairs:
        if any(n in t for n in needles):
            return spec
    return None


def map_currency(raw: str | None) -> str | None:
    if not raw:
        return None
    u = raw.upper()
    if u in ("RUR", "RUB"):
        return "RUB"
    if u in ("USD", "EUR", "KZT", "UZS", "BYN", "GEL"):
        return u
    return "other"


def map_salary_gross_from_hh(salary: dict[str, Any] | None) -> str | None:
    if not salary:
        return None
    if "gross" in salary:
        return "gross" if salary.get("gross") else "net"
    return "unknown"


def infer_english_level(text: str) -> str | None:
    t = text.lower()
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


def infer_education_level(text: str) -> str | None:
    t = text.lower()
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


def enrich_hh_canonical(
    item: dict[str, Any],
    source_id: str,
    source_name: str,
) -> dict[str, Any]:
    """Расширенная нормализация одной вакансии HH (короткий объект из поиска)."""
    salary = item.get("salary") or {}
    experience = item.get("experience") or {}
    employment = item.get("employment") or {}
    schedule = item.get("schedule") or {}
    employer = item.get("employer") or {}
    area = item.get("area") or {}
    snippet = item.get("snippet") or {}
    address = item.get("address") or {}

    skills = [s["name"] for s in (item.get("key_skills") or []) if isinstance(s, dict) and s.get("name")]
    description_parts = filter(None, [snippet.get("requirement"), snippet.get("responsibility")])
    description = "\n".join(description_parts) or None

    roles_parts = [
        str(r["name"])
        for r in (item.get("professional_roles") or [])
        if isinstance(r, dict) and r.get("name")
    ]
    blob = _norm_text(item.get("name"), description, " ".join(skills), " ".join(roles_parts))
    skills = extract_skills_from_text(blob, skills)

    exp_id = experience.get("id") or ""
    experience_level = HH_EXPERIENCE_TO_LEVEL.get(exp_id)
    seniority = HH_EXPERIENCE_TO_SENIORITY.get(exp_id)

    employment_type = map_employment(employment.get("id"), employment.get("name"))
    sched_id = schedule.get("id") or ""
    if sched_id == "remote":
        schedule_type = "flexible"
    else:
        schedule_type = map_schedule(sched_id, schedule.get("name"))

    work_format = infer_work_format(blob)
    if sched_id == "remote" and "remote" not in work_format:
        work_format = ["remote", *work_format]

    profession_area = classify_profession_area(blob)
    specialization = classify_specialization(blob)

    city = (address.get("city") or area.get("name") or "").strip() or None
    country = None
    if area.get("id"):
        country = "Россия"

    industries = employer.get("industries") or []
    company_industry = None
    if industries and isinstance(industries[0], dict):
        company_industry = (industries[0].get("name") or "")[:200] or None

    published_at = None
    if item.get("published_at"):
        try:
            from datetime import datetime

            published_at = datetime.fromisoformat(str(item["published_at"]).replace("Z", "+00:00"))
        except ValueError:
            pass

    english_level = infer_english_level(blob)
    education_level = infer_education_level(blob)

    return {
        "source_id": source_id,
        "external_id": str(item["id"]),
        "title": item.get("name", "") or "",
        "company": employer.get("name", "") or "",
        "canonical_url": item.get("alternate_url", ""),
        "location": area.get("name"),
        "location_country": country,
        "location_city": city,
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "salary_currency": map_currency(salary.get("currency")) or "RUB",
        "salary_gross_type": map_salary_gross_from_hh(salary),
        "salary_period": (
            "month" if (salary.get("from") or salary.get("to")) else "unknown"
        ),
        "seniority": seniority,
        "experience_level": experience_level,
        "employment_type": employment_type,
        "work_format": work_format or [],
        "schedule_type": schedule_type,
        "description": description,
        "skills": skills,
        "status": "active",
        "published_at": published_at,
        "profession_area": profession_area,
        "specialization": specialization,
        "company_industry": company_industry,
        "source_name": source_name or "hh",
        "english_level": english_level,
        "education_level": education_level,
    }
