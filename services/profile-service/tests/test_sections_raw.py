"""Tests for section splitting and helpers."""

from app.resume.sections import raw_sections_detected, split_into_sections


def test_raw_sections_detected_sorted():
    assert raw_sections_detected({"b": "x", "a": "y"}) == ["a", "b"]


def test_split_merges_duplicate_section_keys():
    text = """Контакты
first block

Навыки
Python

Контакты
second block
"""
    sections = split_into_sections(text)
    assert "contacts" in sections
    assert "first block" in sections["contacts"]
    assert "second block" in sections["contacts"]


def test_split_skips_ignore_headings():
    text = """Сопроводительное письмо
ignored body
Контакты
only@mail.ru
"""
    sections = split_into_sections(text)
    assert sections.get("contacts", "").strip().startswith("only@")


def test_split_second_heading_inside_first_body_is_skipped():
    text = """Контакты
email@test.ru
Контакты
duplicate heading inside section
"""
    sections = split_into_sections(text)
    assert "@" in sections.get("contacts", "")


def test_split_overlapping_headings_keeps_first():
    text = """Гражданство
old
Гражданство, время в пути до работы
Гражданство: Россия
"""
    sections = split_into_sections(text)
    assert "citizenship" in sections
