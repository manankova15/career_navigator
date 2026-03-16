#!/usr/bin/env python3
"""
Seed script: deletes all existing assessments and creates 10 new ones
from career_nagigator/tasks.txt.

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
        "q_nums": [61, 62, 63, 64, 65, 81, 82, 83],
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
