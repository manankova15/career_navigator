"""
Сопоставление свободного текста (`target_role`, `headline`, `target_industry`)
с каноническими `profession_area` / `specialization`, как в
``scripts/backfill_classification.py``.

Дублируем правила здесь, а не импортируем из scripts/, потому что
recommendation-service собирается отдельным Docker-образом без доступа к
scripts/. Логика правил и значения категорий **идентичны** seed-скриптам.
"""

from __future__ import annotations

from typing import Iterable

# (substrings, area_code)
_AREA_RULES: list[tuple[tuple[str, ...], str]] = [
    (
        (
            "developer", "software", "backend", "frontend", "fullstack", "full stack",
            "devops", "разработчик", "программист", "инженер по тест", "qa ", " qa",
            "тестировщик", "системный админ", "sre", "site reliability",
            "data engineer", "ml engineer", "machine learning engineer",
        ),
        "it",
    ),
    (
        (
            "analyst", "аналитик", "data scientist", "bi ", " bi",
            "business analyst", "product analyst", "data analyst",
        ),
        "analytics",
    ),
    (("finance", "финанс", "казначей", "investment", "инвест", "treasury"), "finance"),
    (("accountant", "бухгалтер", "бухгалтерия"), "accounting"),
    (("маркетолог", "marketing", "performance", "seo", "smm", "growth"), "marketing"),
    (("sales", "продаж", "менеджер по продаж", "account executive"), "sales"),
    (("product manager", "продакт", "product owner", "продуктовый менеджер"), "product"),
    (("project manager", "проектный менеджер", "scrum master", "delivery manager"), "project_management"),
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

# Маппинг ключевых слов общей индустрии → канонический profession_area.
# Используется как мягкий fallback, если по target_role ничего не извлеклось.
_INDUSTRY_FALLBACK: dict[str, str] = {
    "it": "it",
    "айти": "it",
    "технологии": "it",
    "tech": "it",
    "финансы": "finance",
    "fintech": "finance",
    "банк": "finance",
    "маркетинг": "marketing",
    "реклама": "marketing",
    "образование": "education",
    "медицина": "medicine",
    "ритейл": "sales",
    "розница": "sales",
    "юр": "legal",
    "право": "legal",
    "hr": "hr",
    "рекрут": "hr",
    "логистика": "logistics",
    "консалтинг": "operations",
    "data": "analytics",
    "аналитика": "analytics",
}

# (substrings, specialization_code)
_SPEC_RULES: list[tuple[tuple[str, ...], str]] = [
    (("fullstack", "full stack", "full-stack", "фулстек", "фулстак"), "fullstack_developer"),
    (("frontend", "front end", "front-end", "react developer", "vue developer", "фронтенд", "фронт-енд"), "frontend_developer"),
    (("backend", "back end", "back-end", "python developer", "java developer", "бэкенд", "backend developer"), "backend_developer"),
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
    (("product manager", "продакт-менеджер", "продуктовый менеджер"), "product_manager"),
    (("project manager", "проектный менеджер"), "project_manager"),
    (("ui/ux", "ux designer", "ui designer"), "ui_ux_designer"),
    (("graphic designer", "графический дизайн"), "graphic_designer"),
    (("recruiter", "рекрутер"), "recruiter"),
    (("lawyer", "юрист"), "lawyer"),
    (("support", "поддержк", "helpdesk"), "support_specialist"),
]


def _scan(text: str, rules: list[tuple[tuple[str, ...], str]]) -> str | None:
    for needles, code in rules:
        if any(n in text for n in needles):
            return code
    return None


def classify_category(text: str | None) -> str | None:
    if not text:
        return None
    low = text.lower()
    direct = _scan(low, _AREA_RULES)
    if direct:
        return direct
    if ("инженер" in low or "engineer" in low) and not any(
        x in low for x in ("software", "разработчик", "developer", "программист")
    ):
        return "engineering"
    for kw, area in _INDUSTRY_FALLBACK.items():
        if kw in low:
            return area
    return None


def classify_specialization(text: str | None) -> str | None:
    if not text:
        return None
    return _scan(text.lower(), _SPEC_RULES)


def derive_categories(*texts: str | None) -> list[str]:
    out: list[str] = []
    for t in texts:
        cat = classify_category(t)
        if cat and cat not in out:
            out.append(cat)
    return out


def derive_specializations(*texts: str | None) -> list[str]:
    out: list[str] = []
    for t in texts:
        spec = classify_specialization(t)
        if spec and spec not in out:
            out.append(spec)
    return out


def collect_classification_hints(extras: Iterable[str | None]) -> tuple[list[str], list[str]]:
    """Удобный одношаговый вызов для orchestrator: возвращает
    ``(categories, specializations)`` по списку текстов."""
    cats: list[str] = []
    specs: list[str] = []
    for t in extras:
        c = classify_category(t)
        if c and c not in cats:
            cats.append(c)
        s = classify_specialization(t)
        if s and s not in specs:
            specs.append(s)
    return cats, specs
