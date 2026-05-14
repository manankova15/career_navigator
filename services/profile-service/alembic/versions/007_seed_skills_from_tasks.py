"""Seed curated skills from tasks (final list).

Revision ID: 007
Revises: 006
Create Date: 2026-05-28
"""

from alembic import op


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


NEW_SKILLS: tuple[str, ...] = (
    "JavaScript",
    "C++",
    "CTE",
    "DDL",
    "JOIN",
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
    "Docker",
    "Kubernetes",
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


def upgrade() -> None:
    for name in NEW_SKILLS:
        normalized = name.strip().lower()
        op.execute(
            "INSERT INTO skills (id, name, normalized_name) "
            f"VALUES (gen_random_uuid(), '{name.replace(chr(39), chr(39) * 2)}', "
            f"'{normalized.replace(chr(39), chr(39) * 2)}') "
            "ON CONFLICT (normalized_name) DO NOTHING"
        )


def downgrade() -> None:
    for name in NEW_SKILLS:
        normalized = name.strip().lower().replace("'", "''")
        op.execute(
            f"DELETE FROM skills WHERE normalized_name = '{normalized}' "
            "AND NOT EXISTS (SELECT 1 FROM profile_skills ps WHERE ps.skill_id = skills.id)"
        )
