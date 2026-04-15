from app.resume.detect_hh import detect_hh_resume
from app.resume.normalize_text import normalize_resume_text
from app.resume.parser import build_parsed_document
from app.resume.sections import split_into_sections


def sample_hh_text() -> str:
    return """
Резюме
Иванов Иван Иванович
Мужчина, 30 лет, родился 8 февраля 1995

Data Engineer / Analyst
200 000 ₽ на руки

Москва, м. Рязанский проспект, не готов к переезду, готов к командировкам

Контакты
+7 (999) 123-45-67
Телефон подтвержден
ivan@example.com
предпочитаемый способ связи — email

Специализации
Аналитик
Программист

Занятость
полная занятость

График работы
полный день
удаленная работа

Опыт работы
ООО «Ромашка»
Январь 2020 — по настоящее время
Москва
https://romashka.example
Информационные технологии
Инженер данных
Поддержка пайплайнов.

Навыки
Python, SQL, Git

Образование
МГУ
Факультет ВМК
2017

Знание языков
Русский — Родный

Гражданство, время в пути до работы
Гражданство: Россия
Разрешение на работу: Россия
Желательное время в пути до работы: не более часа

hh.ru/applicant/resumes/view?print=true
Резюме обновлено 1 апреля 2026
"""


def test_detect_hh_positive():
    n = normalize_resume_text(sample_hh_text())
    is_hh, score, _ = detect_hh_resume(n)
    assert score >= 0.45
    assert is_hh or score >= 0.45


def test_parse_sections_and_header():
    n = normalize_resume_text(sample_hh_text())
    sections = split_into_sections(n)
    assert "contacts" in sections
    assert "experience" in sections
    parsed = build_parsed_document(n, sections, True, 0.9)
    assert parsed["profile"].get("email") == "ivan@example.com"
    assert parsed["profile"].get("phoneVerified") is True
    assert parsed["job"].get("salaryNetType") == "net"
    assert len(parsed["experience"]) >= 1


def test_detect_random_pdf_low_score():
    noise = "Счёт на оплату № 44 от 12.12.2025. Сумма 1000 руб."
    n = normalize_resume_text(noise)
    _, score, _ = detect_hh_resume(n)
    assert score < 0.45
