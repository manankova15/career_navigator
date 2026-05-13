"""
Тесты парсера зарплат (`app/salary_parser.py`).

Покрывают:
- все форматы из ТЗ (USD, EUR, GBP, USDT, RUB, KZT и т.п.);
- множители «k», «к», «kk», «тыс.», «млн»;
- периоды «/мес», «/year», «в час» и приведение к месяцу;
- обнаружение gross/net («на руки», «до налогов»);
- отсутствие ложных срабатываний (опыт работы, размер команды и т.п.).
"""

from __future__ import annotations

import pytest

from app.salary_parser import (
    EXCHANGE_RATES_RUB,
    compute_rub_amounts,
    normalize_period_to_month,
    parse_salary,
)


# =====================================================================
# Базовые форматы из ТЗ (см. сообщение пользователя в чате).
# =====================================================================


@pytest.mark.parametrize(
    "text, expected",
    [
        # Доллар c множителем k
        ("Аналитик данных, $3-6k, Москва",
         {"salary_from": 3000, "salary_to": 6000, "salary_currency": "USD"}),
        # Доллар + явный период /мес
        ("Senior backend, $4000–7000/мес",
         {"salary_from": 4000, "salary_to": 7000, "salary_currency": "USD",
          "salary_period": "month"}),
        # Русское «от ... до ... тыс. руб.»
        ("Зарплата от 300 до 600 тыс. руб., полный день",
         {"salary_from": 300_000, "salary_to": 600_000,
          "salary_currency": "RUB", "salary_period": "month"}),
        # Доллар с пробелами вокруг тире и /месяц
        ("Salary $2000 - 5000/месяц",
         {"salary_from": 2000, "salary_to": 5000, "salary_currency": "USD"}),
        # Кириллическое «К» и net (на руки)
        ("ЗП 400-500К на руки, офис",
         {"salary_from": 400_000, "salary_to": 500_000,
          "salary_currency": "RUB", "salary_gross_type": "net"}),
        # Маленький from + большой to с пробелом, GBP после
        ("Salary 55-90 000 GBP, London hybrid",
         {"salary_from": 55_000, "salary_to": 90_000, "salary_currency": "GBP"}),
        # USDT с дробным k и /mo
        ("Compensation 2.5-4k USDT/mo, remote",
         {"salary_from": 2500, "salary_to": 4000, "salary_currency": "USDT"}),
        # Доллар, оба k
        ("We pay $105k-150k for the role",
         {"salary_from": 105_000, "salary_to": 150_000, "salary_currency": "USD"}),
        # Валюта через слэш в конце
        ("Стек: 5-7k/usd, Python",
         {"salary_from": 5000, "salary_to": 7000, "salary_currency": "USD"}),
        ("Зарплата 360-500к/руб",
         {"salary_from": 360_000, "salary_to": 500_000, "salary_currency": "RUB"}),
        # Год -> делим на 12
        ("EU role, 75-105k EUR/year",
         {"salary_from": 6250, "salary_to": 8750, "salary_currency": "EUR",
          "salary_period": "month"}),
        # Одиночное число
        ("Зарплата 275 тыс. руб",
         {"salary_from": 275_000, "salary_currency": "RUB"}),
        # «kk» = млн
        ("Senior, 750k-1kk руб/мес",
         {"salary_from": 750_000, "salary_to": 1_000_000, "salary_currency": "RUB"}),
        # USD/year + множитель
        ("$150-200k/year, FAANG",
         {"salary_from": 12_500, "salary_to": 16_667, "salary_currency": "USD"}),
        # «до» — только верхняя граница
        ("Оклад до 300 тыс.руб",
         {"salary_to": 300_000, "salary_from": None, "salary_currency": "RUB"}),
        # «Вилка» как префикс
        ("Вилка 260-320к руб",
         {"salary_from": 260_000, "salary_to": 320_000, "salary_currency": "RUB"}),
        # «до» + «на руки»
        ("ЗП до 180к руб на руки",
         {"salary_to": 180_000, "salary_currency": "RUB",
          "salary_gross_type": "net"}),
        # Тире-em-dash после «Вилка»
        ("Вилка — 100–200k руб. на руки",
         {"salary_from": 100_000, "salary_to": 200_000,
          "salary_currency": "RUB", "salary_gross_type": "net"}),
        ("Вилка 220-300к руб на руки",
         {"salary_from": 220_000, "salary_to": 300_000,
          "salary_currency": "RUB", "salary_gross_type": "net"}),
    ],
)
def test_parse_salary_known_formats(text, expected):
    info = parse_salary(text)
    assert info is not None, f"Парсер должен распознать: {text!r}"
    for key, value in expected.items():
        actual = getattr(info, key)
        assert actual == value, (
            f"{text!r}: поле {key} ожидалось {value!r}, получили {actual!r}"
        )


# =====================================================================
# Антипаттерны: эти строки НЕ должны парситься как зарплата.
# =====================================================================


@pytest.mark.parametrize(
    "text",
    [
        "Опыт от 1 года в Python",
        "Опыт от 3 до 5 лет в backend",
        "Команда из 10-20 человек",
        "Аудитория более 1 000 000 пользователей",
        "Возраст от 25 до 35 лет",
        "Уже больше 5 000 клиентов в нашем продукте",
        "Доступно 24/7 поддержка",
        # Опыт работы — даже когда рядом случайно есть слово "руб"
        "опыт от 3 лет",
        "опыт от 3х лет",
        "опыт от 3-х лет",
        "Требуется опыт от 3 лет, работа с базой рублей",
        # Типовая ТГ-опечатка: "5к лет" — без анти-паттерна это давало 5000 руб
        "требуется опыт от 5к лет",
        "опыт от 5к лет рублей",
        "опыт от 10к лет работы",
        "Зарплата от 3 лет\nЛокация: Москва",
        "опыт от 3 до 5 лет, разработчик Python",
        "5 years of experience required",
        "2 yrs experience minimum",
    ],
)
def test_parse_salary_no_false_positives(text):
    info = parse_salary(text)
    assert info is None, (
        f"{text!r} ошибочно распознано как зарплата: {info!r}"
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        # Опыт + реальная зарплата — должны взять зарплату, а не опыт.
        (
            "Java-разработчик. Опыт от 3 лет. Зп от 100 тыс. руб",
            {"salary_from": 100_000, "salary_currency": "RUB"},
        ),
        (
            "опыт от 3-х лет, зп от 100 до 200к руб",
            {"salary_from": 100_000, "salary_to": 200_000, "salary_currency": "RUB"},
        ),
        (
            "опыт от 5 лет, salary 100k USD",
            {"salary_from": 100_000, "salary_currency": "USD"},
        ),
        # "/год" и "в год" — это период зарплаты, должен распознаваться.
        (
            "Зарплата 200 000 руб в год",
            {"salary_currency": "RUB", "salary_period": "month"},
        ),
        (
            "100k EUR/year",
            {"salary_currency": "EUR", "salary_period": "month"},
        ),
    ],
)
def test_experience_doesnt_break_real_salary(text, expected):
    """После вырезки фраз опыта реальная зарплата всё ещё корректно парсится."""
    info = parse_salary(text)
    assert info is not None, f"{text!r}: зарплата не распознана"
    for key, value in expected.items():
        actual = getattr(info, key)
        assert actual == value, (
            f"{text!r}: поле {key} ожидалось {value!r}, получили {actual!r}"
        )


# =====================================================================
# Период: год / час / день -> месяц.
# =====================================================================


def test_year_normalized_to_month():
    info = parse_salary("$150-200k/year")
    assert info is not None
    assert info.salary_period == "month"
    # 150_000/12 ≈ 12_500, 200_000/12 ≈ 16_667
    assert info.salary_from == 12_500
    assert info.salary_to == 16_667


def test_hour_normalized_to_month():
    # Один час 50 USD * 168 = 8400 USD / month
    info = parse_salary("Rate 50 USD/hour")
    assert info is not None
    assert info.salary_currency == "USD"
    assert info.salary_period == "month"
    assert info.salary_from == 50 * 168


# =====================================================================
# Конвертация в RUB (для сортировки и фильтрации).
# =====================================================================


def test_rub_equivalent_for_usd():
    info = parse_salary("$5000 в месяц")
    assert info is not None
    assert info.salary_currency == "USD"
    expected = round(5000 * EXCHANGE_RATES_RUB["USD"])
    assert info.salary_from_rub == expected


def test_rub_equivalent_for_eur():
    info = parse_salary("Зарплата 4000 EUR в месяц")
    assert info is not None
    assert info.salary_currency == "EUR"
    expected = round(4000 * EXCHANGE_RATES_RUB["EUR"])
    assert info.salary_from_rub == expected


def test_rub_equivalent_for_rub_unchanged():
    info = parse_salary("Вилка 200-300к руб")
    assert info is not None
    assert info.salary_from_rub == info.salary_from
    assert info.salary_to_rub == info.salary_to


# =====================================================================
# Вспомогательные публичные функции.
# =====================================================================


def test_compute_rub_amounts_handles_unknown_currency():
    # Неизвестная валюта -> RUB-эквивалент None (нельзя сортировать корректно).
    sf_rub, st_rub = compute_rub_amounts(1000, 2000, "XYZ")
    assert sf_rub is None
    assert st_rub is None


def test_compute_rub_amounts_handles_none_amounts():
    sf_rub, st_rub = compute_rub_amounts(None, 1000, "USD")
    assert sf_rub is None
    assert st_rub == round(1000 * EXCHANGE_RATES_RUB["USD"])


def test_normalize_period_year_to_month():
    sf, st, period = normalize_period_to_month(120_000, 240_000, "year")
    assert sf == 10_000
    assert st == 20_000
    assert period == "month"


def test_normalize_period_month_unchanged():
    sf, st, period = normalize_period_to_month(50_000, 80_000, "month")
    assert sf == 50_000
    assert st == 80_000
    assert period == "month"


def test_normalize_period_handles_none():
    sf, st, period = normalize_period_to_month(None, None, "year")
    assert sf is None
    assert st is None
    assert period == "month"
