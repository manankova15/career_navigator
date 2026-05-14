"""Канонический список навыков, к которому фильтруются навыки из резюме.

При импорте резюме мы достаём все навыки из файла, но в профиль попадают
только те, которые присутствуют в этом списке (или в таблице ``skills`` в БД,
куда этот список засеян миграцией 006). Сравнение регистронезависимое.
"""

from __future__ import annotations

# Названия навыков в том виде, в каком они должны храниться/отображаться.
CANONICAL_SKILLS: tuple[str, ...] = (
    "Python",
    "JavaScript",
    "C++",
    "SQL",
    "HTML",
    "CSS",
    "MySQL",
    "PostgreSQL",
    "ORACLE",
    "CTE",
    "DDL",
    "JOIN",
    "pandas",
    "numpy",
    "scikit-learn",
    "seaborn",
    "React",
    "Next.js",
    "Node.js",
    "Express",
    "Selenium",
    "Webpack",
    "Helm",
    "Git",
    "Docker",
    "Kubernetes",
    "Jenkins",
    "OpenShift",
    "Terraform",
    "Prometheus",
    "Linux",
    "CI/CD",
    "IaC",
    "DevOps",
    "BGP",
    "DNS",
    "HTTP",
    "ICMP",
    "IP",
    "IPv4",
    "IPv6",
    "TCP/IP",
    "NAT",
    "VPN",
    "OSI",
    "CIDR",
    "REST",
    "REST API",
    "GraphQL",
    "API",
    "MS Office",
    "MS Excel",
    "ООП",
    "BDD",
    "DOM",
    "Event Loop",
    "RAII",
    "STL",
    "Big O",
    "Flexbox",
    "SSR",
    "OWASP",
    "WCAG",
    "Web Security",
    "Криптография",
    "Аутентификация",
    "ML",
    "Глубокое обучение",
    "Нейронные сети",
    "Регрессия",
    "Классификация",
    "Кластеризация",
    "Ансамблевые методы",
    "Регуляризация",
    "Transfer learning",
    "Bias-variance tradeoff",
    "A/B-тестирование",
    "Линейная алгебра",
    "Теория вероятностей",
    "Математическая статистика",
    "Временные ряды",
    "BI",
    "Mocking",
    "Юнит-тестирование",
    "Тест-дизайн",
    "UI-дизайн",
    "UX-дизайн",
    "UX-исследования",
    "Accessibility",
    "Design systems",
    "Эвристики Нильсена",
    "Прототипирование",
    "Микросервисы",
    "Шаблоны проектирования",
    "Функциональное программирование",
    "Динамическое программирование",
    "Виртуализация",
    "AWS",
    "Message brokers",
)


def normalized_skill_set() -> set[str]:
    """Возвращает множество нормализованных (lower-case, trimmed) имён навыков."""
    return {s.strip().lower() for s in CANONICAL_SKILLS}


def filter_skills_against_base(skills: list[str], base: set[str] | None = None) -> list[str]:
    """Оставляет только те навыки, имена которых (без учёта регистра) есть в базе.

    Если ``base`` не передан — используется ``normalized_skill_set()``.
    Возвращает список с сохранением порядка и без дубликатов.
    """
    base_set = base if base is not None else normalized_skill_set()
    seen: set[str] = set()
    out: list[str] = []
    for raw in skills:
        if not raw:
            continue
        key = raw.strip().lower()
        if key in seen:
            continue
        if key in base_set:
            seen.add(key)
            out.append(raw.strip())
    return out
