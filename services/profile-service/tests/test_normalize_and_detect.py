"""Tests for normalize_resume_text and detect_hh_resume."""

from app.resume.detect_hh import detect_hh_resume
from app.resume.normalize_text import normalize_resume_text


def test_normalize_empty_and_whitespace():
    assert normalize_resume_text("") == ""
    assert normalize_resume_text("   \n\t  ") == ""


def test_normalize_strips_hh_print_url():
    raw = "Intro\nhttps://hh.ru/applicant/resumes/view?print=true\nКонтакты\n"
    out = normalize_resume_text(raw)
    assert "http" not in out.lower()


def test_normalize_page_numbers_and_multispace():
    raw = "Line one\n1 / 3\nLine two\n\n\n\nLine three  with   spaces"
    out = normalize_resume_text(raw)
    assert "1 / 3" not in out
    assert "  " not in out.replace("\n", "")


def test_normalize_standalone_page_fraction_line_removed():
    raw = "Header\n2/5\nBody"
    out = normalize_resume_text(raw)
    assert "2/5" not in out.split()


def test_normalize_skips_line_that_is_only_page_fraction():
    raw = "Intro\n3 / 7\nRest of text"
    out = normalize_resume_text(raw)
    assert "3 / 7" not in out
    assert "Rest of text" in out


def test_normalize_skips_compact_page_fraction_line():
    raw = "Header\n1/2\nFooter"
    out = normalize_resume_text(raw)
    assert "1/2" not in out
    assert "Footer" in out


def test_normalize_crlf():
    assert normalize_resume_text("a\r\nb") == "a\nb"


def test_detect_short_text_warning():
    t = "x" * 100
    is_hh, score, warnings = detect_hh_resume(t)
    assert not is_hh
    assert any("Мало текста" in w for w in warnings)


def test_detect_contract_penalty():
    t = "Резюме\n" * 30 + "Опыт работы\n" * 5 + "счёт на оплату № 1\n" + "hh.ru\n" * 5
    _, score, warnings = detect_hh_resume(t)
    assert any("договор" in w or "счёт" in w for w in warnings)
    assert score < 1.0


def test_detect_medium_text_returns_structured_result():
    t = (
        "\n".join(
            [
                "Резюме",
                "Иванов Иван",
                "Инженер",
                "Москва, готов к переезду",
                "Контакты",
                "a@b.co",
                "Опыт работы",
                "Январь 2020 — по настоящее время",
                "ООО Тест",
                "Разработчик",
                "hh.ru/applicant/resumes/view?print=true",
            ]
        )
        * 3
    )
    is_hh, score, warnings = detect_hh_resume(t)
    assert isinstance(score, float)
    assert isinstance(warnings, list)
    assert 0.0 <= score <= 1.0


def test_detect_low_confidence_warning():
    t = "hello world " * 5
    _, score, warnings = detect_hh_resume(t)
    assert score < 0.45
    assert any("Низкая уверенность" in w for w in warnings)


def test_detect_strong_hh_flags():
    blob = """
Резюме
Петров Пётр
Мужчина, 28 лет, родился 1 января 1998
Backend
250 000 ₽ на руки
Санкт-Петербург, готов к переезду, готов к командировкам
Контакты
+7 900 000-00-00
Телефон подтвержден
user@example.com
Специализации
Инженер
Занятость
полная
График работы
удалённо
Опыт работы
ООО Рога
Март 2019 — Декабрь 2023
Москва
Разработчик
Код.
Навыки
Go, PostgreSQL
Образование
ВУЗ
2019
Знание языков
Английский — B2
Гражданство, время в пути до работы
Гражданство: Россия
https://hh.ru/applicant/resumes/view?print=true
Резюме обновлено 1 апреля 2026
"""
    n = normalize_resume_text(blob)
    _, score, _ = detect_hh_resume(n)
    assert score >= 0.65
