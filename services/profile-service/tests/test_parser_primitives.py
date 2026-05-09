"""Targeted tests for parser helpers and edge branches."""

from app.resume import parser as P
from app.resume.parser import (
    build_field_confidence,
    build_parsed_document,
    parse_citizenship_block,
    parse_contacts,
    parse_courses,
    parse_desired_job,
    parse_education,
    parse_experience,
    parse_header_and_personal,
    parse_languages,
    parse_resume_updated,
    parse_skills,
)


def test_iso_date_invalid_month_and_bad_day():
    assert P._iso_date(15, "неизвестный", 2020) is None
    assert P._iso_date(31, "февраля", 2021) is None


def test_parse_month_year_invalid():
    assert P._parse_month_year_to_iso("smarch", 2020) is None
    assert P._parse_month_year_to_iso("марта", 99999) is None


def test_parse_period_end_variants():
    assert P._parse_period_end("по настоящее время") == (None, True)
    assert P._parse_period_end("март 2022") == ("2022-03-01", False)
    assert P._parse_period_end("???") == (None, False)


def test_parse_contacts_empty_and_phone_pref():
    assert parse_contacts("")["email"] == ""
    block = "+7 999 111-22-33\nпредпочитаемый способ связи — телефон\n"
    out = parse_contacts(block)
    assert out["phone"]
    assert out["preferredContactMethod"] == "phone"


def test_parse_contacts_email_preferred():
    block = "a@b.co\nпредпочитаемый способ связи — email\n"
    out = parse_contacts(block)
    assert out["preferredContactMethod"] == "email"


def test_parse_salary_range_and_gross():
    from app.resume.parser import _parse_salary_line

    j = _parse_salary_line("100000–200000₽ до вычета налогов")
    assert j["salaryFrom"] == 100000
    assert j["salaryTo"] == 200000
    assert j["salaryNetType"] == "gross"


def test_parse_header_female_and_long_location_line():
    head = """Резюме
Иванова Мария Сергеевна
Женщина, 25 лет, родилась 5 мая 2000
Аналитик
150000 руб
""" + "x" * 400 + "\nготова к переезду\n"
    profile = parse_header_and_personal(head, {})
    assert profile.get("gender") == "female"


def test_parse_header_fallback_name_without_resume_marker():
    head = "Случайное Имя\nСтрока с мужчина не тут\n"
    profile = parse_header_and_personal(head, {})
    assert profile.get("fullName")


def test_parse_location_relocation_variants():
    head = (
        "Резюме\nИван\nМужчина, 30 лет, родился 1 января 1990\n"
        "Москва, готовность хочу переехать\n"
    )
    profile = parse_header_and_personal(head, {})
    assert profile.get("relocationReadiness") == "interested"


def test_parse_location_trip_not_ready():
    head = (
        "Резюме\nИван\nМужчина, 30 лет, родился 1 января 1990\n"
        "Москва, м. Киевская, не готов к командировкам\n"
    )
    profile = parse_header_and_personal(head, {})
    assert profile.get("businessTripReadiness") == "not_ready"


def test_parse_desired_job_pulls_specializations_from_sections():
    full = "Резюме\nИмя\nДолжность\nМужчина\n"
    sections = {
        "specializations": "Dev\nOps",
        "employment": "Полная",
        "work_schedule": "Удалённо",
    }
    job = parse_desired_job(full, sections)
    assert "Dev" in job["specializations"]
    assert job["employmentTypes"]
    assert job["workSchedules"]


def test_parse_desired_job_when_position_line_is_gender():
    head = """Резюме
Фамилия Имя
Мужчина, 40 лет, родился 1 января 1985
"""
    job = parse_desired_job(head, {})
    assert job.get("desiredPosition") == ""


def test_parse_experience_empty_and_no_periods():
    assert parse_experience("") == []
    assert parse_experience("просто текст без дат") == []


def test_parse_experience_meta_with_url_and_long_company_skip():
    block = """ООО ДлинноеНазваниеКомпании""" + "x" * 200 + """
Январь 2020 — по настоящее время
https://example.com
Информационные технологии, системная интеграция
Короткая роль
Описание строка 1
Описание строка 2
"""
    ex = parse_experience(block)
    assert isinstance(ex, list)


def test_parse_skills_with_levels_block():
    skills, levels = parse_skills("Go; Rust", "Уровень владения навыком — Продвинутый уровень\nGo\n")
    assert "Go" in skills
    assert any(x.get("skill") == "Go" for x in levels)


def test_parse_skills_levels_unknown_line():
    skills, levels = parse_skills("", "уровень не указан\nSomeSkill\n")
    assert any(x["level"] == "unknown" for x in levels)


def test_parse_education_and_courses_empty():
    assert parse_education("") == []
    assert parse_courses("") == []


def test_parse_education_skips_empty_line_chunks():
    out = parse_education("Вуз 2020\n\n\n\n\n")
    assert isinstance(out, list)


def test_parse_courses_skips_blank_paragraph():
    items = parse_courses("Курс А\n\n\n\n")
    assert isinstance(items, list)
    items2 = parse_courses("Only\n\n\n")
    assert isinstance(items2, list)


def test_parse_languages_hyphen_separator():
    langs = parse_languages("Deutsch - B1")
    assert langs and langs[0]["levelNormalized"] == "b1"


def test_parse_citizenship_commute_preference():
    from app.resume.parser import parse_citizenship_block

    out = parse_citizenship_block("времени в пути до метро: до 40 минут\n")
    assert "40" in out["commuteTimePreference"]


def test_parse_education_single_chunk():
    out = parse_education("Вуз им\nФакультет\n2018")
    assert out and out[0].get("endYear") == 2018


def test_parse_courses_multiline():
    items = parse_courses("Курс А\nШкола\n2021\n\nКурс Б\n2020")
    assert len(items) >= 1


def test_parse_languages_dash_and_cefr():
    langs = parse_languages("English — B2\nРусский — Родной")
    assert any(l["levelNormalized"] == "native" for l in langs)
    assert any(l["levelNormalized"] == "b2" for l in langs)


def test_parse_languages_skips_plain_lines():
    assert parse_languages("no separator here") == []


def test_parse_citizenship_partial():
    out = parse_citizenship_block("Разрешение на работу: США")
    assert out["workPermit"] == "США"


def test_parse_resume_updated_missing():
    assert parse_resume_updated("no date here") == ""


def test_build_parsed_document_low_confidence_warning():
    sections = {"contacts": "x@y.z"}
    doc = build_parsed_document("Контакты\nx@y.z", sections, False, 0.5)
    assert any("Проверьте" in w for w in doc["warnings"])


def test_build_field_confidence_bounds():
    parsed = {
        "profile": {"fullName": "A"},
        "job": {},
        "aboutMe": "",
        "additionalInfo": None,
        "experience": [{"companyName": "C"}],
        "education": [{"institution": "U"}],
        "skills": ["s"],
    }
    fc = build_field_confidence(parsed, 0.1)
    assert fc["profile"]["fullName"] == 0.35
    fc2 = build_field_confidence(parsed, 0.99)
    assert fc2["profile"]["fullName"] == 0.95


def test_head_text_without_contacts():
    head = P._head_text("x" * 100, {})
    assert len(head) <= 6000


def test_parse_experience_chunk_skips_bad_period_match():
    block = """Компания
Февраль 2020 — по настоящее время
Роль
описание
"""
    ex = parse_experience(block)
    assert isinstance(ex, list)
