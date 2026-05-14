#!/usr/bin/env python3
"""
Seed script: deletes all existing assessments and creates tests
from career_nagigator/tasks.txt (350 questions → ~31 assessments, max 10 questions each).

Run from the project root:
    python scripts/seed_assessments.py

Requires: psycopg2-binary or sqlalchemy + psycopg2
"""
from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path

# ── DB connection ────────────────────────────────────────────────────────────
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://career_navigator:secret123@localhost:5432/career_navigator",
)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("ERROR: sqlalchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# ── Parse tasks.txt ──────────────────────────────────────────────────────────

TASKS_FILE = Path(__file__).parent.parent / "tasks.txt"


def parse_tasks(path: Path) -> list[dict]:
    """Parse tasks.txt into a list of question dicts."""
    content = path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in content.split("---") if b.strip()]

    questions = []
    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        q: dict = {}
        options: list[dict] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("Номер вопроса:"):
                q["num"] = int(line.split(":", 1)[1].strip())
            elif line.startswith("Вопрос:"):
                # Question may span multiple lines until "Варианты ответов:"
                text_parts = [line.split(":", 1)[1].strip()]
                j = i + 1
                while j < len(lines) and not lines[j].startswith("Варианты ответов:"):
                    text_parts.append(lines[j])
                    j += 1
                q["prompt"] = "\n".join(text_parts)
                i = j - 1
            elif line.startswith("Варианты ответов:"):
                pass
            elif re.match(r'^[A-D]\)', line):
                letter = line[0]
                text = line[3:].strip()
                options.append({"id": letter, "text": f"{letter}) {text}"})
            elif line.startswith("Правильный ответ:"):
                raw = line.split(":", 1)[1].strip()
                # Extract letter(s)
                letters = re.findall(r'\b([A-D])\)', raw)
                q["correct_option_ids"] = letters if letters else [raw[0]]
            elif line.startswith("Пояснение:"):
                q["explanation"] = line.split(":", 1)[1].strip()
            elif line.startswith("Сложность:"):
                raw_diff = line.split(":", 1)[1].strip().lower()
                mapping = {"легкий": "easy", "средний": "medium", "продвинутый": "hard"}
                q["difficulty"] = mapping.get(raw_diff, "medium")
            elif line.startswith("Необходимые навыки:"):
                skills_raw = line.split(":", 1)[1].strip()
                q["related_skills"] = [s.strip() for s in skills_raw.split(",")]
            i += 1

        if options:
            q["options"] = options
        if "num" in q and "prompt" in q and options:
            questions.append(q)

    questions.sort(key=lambda x: x["num"])
    return questions


# ── Assessment topic groupings ────────────────────────────────────────────────

ASSESSMENTS_CONFIG = [
    {
        "title": "SQL: Базовые запросы",
        "description": "Основы SQL: SELECT, фильтрация, агрегатные функции, JOIN. Проверьте знание базовых конструкций языка запросов.",
        "topic": "SQL",
        "difficulty": "easy",
        "related_skills": ["SQL", "агрегатные функции", "JOIN", "GROUP BY", "фильтрация данных"],
        "q_nums": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 99, 112, 118, 129, 138],
    },
    {
        "title": "SQL: Продвинутый уровень",
        "description": "Продвинутые возможности SQL: оконные функции, CTE, подзапросы, оптимизация и специальные операторы.",
        "topic": "SQL",
        "difficulty": "medium",
        "related_skills": ["SQL", "оконные функции", "CTE", "подзапросы", "оптимизация запросов"],
        "q_nums": [76, 77, 78, 79, 80, 103, 106, 127, 131, 132, 141, 150],
    },
    {
        "title": "Python: Основы",
        "description": "Базовый Python: типы данных, коллекции, управляющие конструкции, встроенные функции и основные идиомы языка.",
        "topic": "Python",
        "difficulty": "easy",
        "related_skills": ["Python", "типы данных", "коллекции", "функции", "итераторы"],
        "q_nums": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
    },
    {
        "title": "Python: Продвинутый и ООП",
        "description": "Генераторы списков, лямбды, декораторы, ООП, функциональное программирование и стандартная библиотека.",
        "topic": "Python",
        "difficulty": "medium",
        "related_skills": ["Python", "ООП", "декораторы", "функциональное программирование", "стандартная библиотека"],
        "q_nums": [74, 84, 85, 94, 95, 110, 115, 116, 120, 133],
    },
    {
        "title": "Pandas и NumPy: Аналитика данных",
        "description": "Работа с DataFrame в pandas и массивами NumPy: агрегация, трансформации, слияния, временные ряды и предобработка.",
        "topic": "Pandas",
        "difficulty": "medium",
        "related_skills": ["Python", "pandas", "NumPy", "Data Analysis", "обработка данных"],
        "q_nums": [55, 56, 57, 58, 59, 60, 70, 72, 92, 93, 96, 101, 102, 104, 111, 113, 117, 123, 125, 126, 128, 130, 134, 136, 140, 147],
    },
    {
        "title": "C++: Основы программирования",
        "description": "Управление памятью, указатели, ссылки, ООП, шаблоны и STL в C++.",
        "topic": "C++",
        "difficulty": "medium",
        "related_skills": ["C++", "ООП", "память", "указатели", "STL"],
        "q_nums": [26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
    },
    {
        "title": "C++ и Алгоритмы",
        "description": "Продвинутые темы C++: контейнеры STL, сложность алгоритмов, структуры данных и move-семантика.",
        "topic": "C++",
        "difficulty": "hard",
        "related_skills": ["C++", "алгоритмы", "структуры данных", "STL", "оптимизация"],
        "q_nums": [61, 62, 63, 64, 65, 81, 82, 83, 154],
    },
    {
        "title": "Анализ данных и Статистика",
        "description": "Статистика для аналитики: корреляция, распределения, p-value, нормализация, визуализация и работа с пропусками.",
        "topic": "Аналитика данных",
        "difficulty": "medium",
        "related_skills": ["Аналитика данных", "статистика", "корреляция", "визуализация", "предобработка данных"],
        "q_nums": [41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 71, 98, 114, 124, 135, 143],
    },
    {
        "title": "Машинное обучение",
        "description": "Алгоритмы ML, регуляризация, кросс-валидация, метрики качества, кластеризация и ансамблевые методы.",
        "topic": "Machine Learning",
        "difficulty": "medium",
        "related_skills": ["Machine Learning", "scikit-learn", "классификация", "регрессия", "метрики", "модели"],
        "q_nums": [66, 67, 68, 69, 73, 75, 97, 100, 105, 107, 108, 109, 119, 144, 145, 146, 149],
    },
    {
        "title": "A/B тестирование и статистические тесты",
        "description": "Методология A/B тестирования, тестирование гипотез, уровень значимости, t-тест, мощность теста и bootstrap.",
        "topic": "A/B тестирование",
        "difficulty": "hard",
        "related_skills": ["статистика", "A/B тестирование", "тестирование гипотез", "экспериментальный дизайн"],
        "q_nums": [86, 87, 88, 89, 90, 91, 121, 122, 137, 139, 142, 148],
    },
    # ── New assessments (questions 151–350) ──────────────────────────────────
    {
        "title": "Python: ООП и продвинутые темы",
        "description": "Объектно-ориентированное программирование, инкапсуляция, полиморфизм и типичные ловушки Python.",
        "topic": "Python",
        "difficulty": "medium",
        "related_skills": ["Python", "ООП", "функции", "стандартная библиотека"],
        "q_nums": [151, 156, 161, 162, 163],
    },
    {
        "title": "Алгоритмы: Big O и структуры данных",
        "description": "Сложность алгоритмов, сортировки, хэш-таблицы, очереди и базовые структуры данных.",
        "topic": "Алгоритмы",
        "difficulty": "medium",
        "related_skills": ["Big O", "алгоритмы", "структуры данных", "C++"],
        "q_nums": [152, 153, 155, 157, 158, 159, 160, 164, 165, 166],
    },
    {
        "title": "Алгоритмы: Графы и динамическое программирование",
        "description": "BFS, DFS, алгоритм Дейкстры, кучи, динамическое программирование и обход графов.",
        "topic": "Алгоритмы",
        "difficulty": "hard",
        "related_skills": ["Big O", "алгоритмы", "структуры данных", "Динамическое программирование"],
        "q_nums": [167, 168, 169, 170],
    },
    {
        "title": "Frontend: HTML и CSS",
        "description": "Разметка HTML, стили CSS, Flexbox, селекторы и адаптивная вёрстка.",
        "topic": "Frontend",
        "difficulty": "easy",
        "related_skills": ["HTML", "CSS", "Flexbox", "DOM"],
        "q_nums": [171, 172, 173, 175, 176, 180, 183],
    },
    {
        "title": "Frontend: JavaScript и React",
        "description": "Основы JavaScript, Event Loop, DOM, React-компоненты и современный frontend-стек.",
        "topic": "Frontend",
        "difficulty": "medium",
        "related_skills": ["JavaScript", "React", "DOM", "Event Loop", "Webpack"],
        "q_nums": [174, 177, 178, 179, 181, 182, 185, 186, 187, 190],
    },
    {
        "title": "Web: HTTP, REST и API",
        "description": "Протокол HTTP, REST API, статус-коды, методы запросов, rate limiting и проектирование API.",
        "topic": "Web/API",
        "difficulty": "medium",
        "related_skills": ["HTTP", "REST API", "API", "REST", "GraphQL"],
        "q_nums": [191, 192, 193, 194, 195, 197, 200, 203, 204, 205],
    },
    {
        "title": "Backend: Node.js и микросервисы",
        "description": "Node.js, Express, микросервисная архитектура, брокеры сообщений, SSR и идемпотентность API.",
        "topic": "Backend",
        "difficulty": "medium",
        "related_skills": ["Node.js", "Express", "Микросервисы", "Next.js", "SSR", "Message brokers"],
        "q_nums": [188, 189, 196, 198, 201, 206, 207, 208, 209, 210],
    },
    {
        "title": "SQL: Продвинутые запросы (новые)",
        "description": "Подзапросы, CTE, оконные функции, JOIN и сложные SELECT-запросы.",
        "topic": "SQL",
        "difficulty": "medium",
        "related_skills": ["SQL", "JOIN", "CTE", "подзапросы", "оконные функции", "GROUP BY"],
        "q_nums": [211, 212, 213, 214, 215, 216, 217, 218, 219, 230],
    },
    {
        "title": "SQL: Индексы, транзакции и архитектура БД",
        "description": "Индексы, транзакции, нормализация, репликация, sharding и оптимизация баз данных.",
        "topic": "SQL",
        "difficulty": "hard",
        "related_skills": ["SQL", "DDL", "PostgreSQL", "MySQL", "Микросервисы", "оптимизация запросов"],
        "q_nums": [220, 221, 222, 223, 224, 225, 226, 227, 228, 229],
    },
    {
        "title": "Web Security: OWASP и уязвимости",
        "description": "Уязвимости веб-приложений, OWASP Top 10, XSS, CSRF, SQL-инъекции и penetration testing.",
        "topic": "Web Security",
        "difficulty": "medium",
        "related_skills": ["Web Security", "OWASP", "SQL", "JavaScript"],
        "q_nums": [249, 231, 233, 244, 240, 245, 237, 238, 239, 243],
    },
    {
        "title": "Web Security: Базовые понятия",
        "description": "Firewall, malware и фундаментальные концепции информационной безопасности.",
        "topic": "Web Security",
        "difficulty": "easy",
        "related_skills": ["Web Security", "OWASP"],
        "q_nums": [235, 236],
    },
    {
        "title": "Web Security: Криптография и аутентификация",
        "description": "HTTPS, TLS, JWT, OAuth, хэширование, salt и симметричное шифрование.",
        "topic": "Web Security",
        "difficulty": "hard",
        "related_skills": ["Web Security", "Криптография", "Аутентификация", "HTTPS", "HTTP"],
        "q_nums": [184, 199, 232, 234, 241, 242, 246, 247, 248, 250],
    },
    {
        "title": "DevOps: Git, Docker и CI/CD",
        "description": "Git, Docker, CI/CD-пайплайны, canary deployment и основы DevOps-практик.",
        "topic": "DevOps",
        "difficulty": "medium",
        "related_skills": ["Git", "Docker", "CI/CD", "DevOps", "Linux"],
        "q_nums": [202, 251, 252, 253, 255, 256, 259, 261, 268, 270],
    },
    {
        "title": "DevOps: Kubernetes, облако и мониторинг",
        "description": "Kubernetes, AWS, Terraform, IaC, виртуализация, Prometheus и облачная инфраструктура.",
        "topic": "DevOps",
        "difficulty": "hard",
        "related_skills": ["Kubernetes", "Docker", "Terraform", "IaC", "AWS", "Prometheus", "DevOps"],
        "q_nums": [254, 257, 258, 260, 262, 263, 264, 265, 267, 269],
    },
    {
        "title": "Сети: TCP/IP и модель OSI",
        "description": "Модель OSI, TCP/IP, порты, NAT, VPN и сетевые протоколы.",
        "topic": "Сети",
        "difficulty": "medium",
        "related_skills": ["TCP/IP", "OSI", "HTTP", "NAT", "VPN", "ICMP"],
        "q_nums": [271, 272, 282, 280, 275, 276, 277, 278, 279, 290],
    },
    {
        "title": "Сети: IP, DNS и маршрутизация",
        "description": "IPv4, IPv6, CIDR, DNS, BGP, IP-адресация и маршрутизация в компьютерных сетях.",
        "topic": "Сети",
        "difficulty": "medium",
        "related_skills": ["IP", "IPv4", "IPv6", "DNS", "BGP", "CIDR", "TCP/IP"],
        "q_nums": [273, 281, 283, 284, 285, 286, 287, 288, 289, 274],
    },
    {
        "title": "QA: Тест-дизайн и методологии",
        "description": "Техники тест-дизайна, виды тестирования, тест-кейсы и методологии QA.",
        "topic": "QA",
        "difficulty": "medium",
        "related_skills": ["Тест-дизайн", "QA", "BDD", "Selenium"],
        "q_nums": [291, 292, 293, 294, 295, 296, 297, 298, 299, 300],
    },
    {
        "title": "QA: Автотесты и инструменты",
        "description": "Автоматизация тестирования, Selenium, юнит-тесты, mocking и инструменты QA.",
        "topic": "QA",
        "difficulty": "medium",
        "related_skills": ["Selenium", "Юнит-тестирование", "Mocking", "Тест-дизайн", "BDD"],
        "q_nums": [301, 302, 303, 304, 305, 306, 307, 308, 309, 310],
    },
    {
        "title": "ML: Классификация и регрессия",
        "description": "Алгоритмы ML, scikit-learn, метрики качества, переобучение и feature engineering.",
        "topic": "Machine Learning",
        "difficulty": "medium",
        "related_skills": ["ML", "scikit-learn", "Классификация", "Регрессия", "pandas"],
        "q_nums": [311, 312, 313, 314, 315, 316, 317, 318, 319, 320],
    },
    {
        "title": "ML: Глубокое обучение и NLP",
        "description": "Нейронные сети, глубокое обучение, transfer learning, NLP и ансамблевые методы.",
        "topic": "Machine Learning",
        "difficulty": "hard",
        "related_skills": ["ML", "Глубокое обучение", "Нейронные сети", "Transfer learning", "Ансамблевые методы"],
        "q_nums": [321, 322, 323, 324, 325, 326, 327, 328, 329, 330],
    },
    {
        "title": "UX/UI: Дизайн и исследования",
        "description": "Принципы UX/UI-дизайна, эвристики, user research, wireframes и design systems.",
        "topic": "Design",
        "difficulty": "medium",
        "related_skills": ["UX-дизайн", "UI-дизайн", "UX-исследования", "Прототипирование", "Design systems"],
        "q_nums": [331, 332, 333, 334, 335, 336, 337, 338, 339, 340],
    },
    {
        "title": "UX/UI: Прототипирование и доступность",
        "description": "Прототипы, usability-тестирование, WCAG, accessibility и практики inclusive design.",
        "topic": "Design",
        "difficulty": "medium",
        "related_skills": ["UX-дизайн", "UI-дизайн", "Accessibility", "WCAG", "Прототипирование", "CSS"],
        "q_nums": [341, 342, 343, 344, 345, 346, 347, 348, 349, 350],
    },
]


def build_item(q: dict, position: int) -> dict:
    """Build an assessment_items row dict from a parsed question."""
    correct_ids = q.get("correct_option_ids", [])
    return {
        "id": str(uuid.uuid4()),
        "position": position,
        "prompt": q["prompt"],
        "mode": "quiz",
        "options": q.get("options", []),
        "correct_option_ids": correct_ids,
        "expected_keywords": [],
        "rubric_checklist": [],
        "max_score": 1.0,
        "related_skills": q.get("related_skills", []),
        "explanation": q.get("explanation"),
    }


def main() -> None:
    if not TASKS_FILE.exists():
        print(f"ERROR: tasks.txt not found at {TASKS_FILE}")
        sys.exit(1)

    print("Parsing tasks.txt…")
    questions = parse_tasks(TASKS_FILE)
    q_by_num = {q["num"]: q for q in questions}
    print(f"  → {len(questions)} questions parsed")

    for cfg in ASSESSMENTS_CONFIG:
        if len(cfg["q_nums"]) > 10:
            print(f"  ⚠ '{cfg['title']}' has {len(cfg['q_nums'])} questions (>10)")

    engine = create_engine(DB_URL, echo=False)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # ── 1. Delete all existing assessments (CASCADE deletes items/attempts) ──
        print("Deleting existing assessments…")
        result = session.execute(text("DELETE FROM assessments"))
        session.commit()
        print(f"  → deleted {result.rowcount} assessments")

        # ── 2. Create new assessments ──────────────────────────────────────────
        import json as _json
        total_questions = 0
        for cfg in ASSESSMENTS_CONFIG:
            a_id = str(uuid.uuid4())

            # Insert assessment
            session.execute(
                text(
                    """
                    INSERT INTO assessments
                        (id, title, description, topic, difficulty, related_skills, is_published, created_at, updated_at)
                    VALUES
                        (:id, :title, :description, :topic, :difficulty, CAST(:related_skills AS jsonb),
                         true, NOW(), NOW())
                    """
                ),
                {
                    "id": a_id,
                    "title": cfg["title"],
                    "description": cfg["description"],
                    "topic": cfg["topic"],
                    "difficulty": cfg["difficulty"],
                    "related_skills": _json.dumps(cfg["related_skills"], ensure_ascii=False),
                },
            )

            # Insert items
            missing = []
            for pos, num in enumerate(cfg["q_nums"]):
                q = q_by_num.get(num)
                if q is None:
                    missing.append(num)
                    continue
                item = build_item(q, pos)
                session.execute(
                    text(
                        """
                        INSERT INTO assessment_items
                            (id, assessment_id, position, prompt, mode, options,
                             correct_option_ids, expected_keywords, rubric_checklist,
                             max_score, related_skills, explanation, created_at)
                        VALUES
                            (:id, :assessment_id, :position, :prompt, :mode,
                             CAST(:options AS jsonb), CAST(:correct_option_ids AS jsonb),
                             CAST(:expected_keywords AS jsonb), CAST(:rubric_checklist AS jsonb),
                             :max_score, CAST(:related_skills AS jsonb), :explanation, NOW())
                        """
                    ),
                    {
                        "id": item["id"],
                        "assessment_id": a_id,
                        "position": item["position"],
                        "prompt": item["prompt"],
                        "mode": item["mode"],
                        "options": _json.dumps(item["options"], ensure_ascii=False),
                        "correct_option_ids": _json.dumps(item["correct_option_ids"], ensure_ascii=False),
                        "expected_keywords": _json.dumps(item["expected_keywords"], ensure_ascii=False),
                        "rubric_checklist": _json.dumps(item["rubric_checklist"], ensure_ascii=False),
                        "max_score": item["max_score"],
                        "related_skills": _json.dumps(item["related_skills"], ensure_ascii=False),
                        "explanation": item["explanation"],
                    },
                )
                total_questions += 1

            session.commit()
            print(f"  ✓ '{cfg['title']}' — {len(cfg['q_nums']) - len(missing)} questions"
                  + (f" (missing q_nums: {missing})" if missing else ""))

        print(f"\nDone! {len(ASSESSMENTS_CONFIG)} assessments, {total_questions} total questions.")


if __name__ == "__main__":
    main()
