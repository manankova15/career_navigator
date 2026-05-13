"""
Парсер заработной платы из произвольного текста (вакансии Telegram, HH и др.).

Что делает модуль:
1. Извлекает нижнюю и верхнюю границу зарплаты в исходной валюте.
2. Определяет валюту (RUB, USD, EUR, GBP, USDT, KZT, ...).
3. Определяет период (месяц / год / час / день) и приводит сумму к месячному
   эквиваленту: /год -> /12, /день -> *22, /час -> *168.
4. Определяет gross/net (на руки / до налогов).
5. Считает рублёвый эквивалент (по фиксированным курсам ниже) — нужен для
   сортировки и фильтрации по зарплате независимо от валюты.

Основное правило, чтобы не было ложных срабатываний типа
"от 1 года опыта" -> 1 руб: число распознаётся как зарплата только если
рядом есть один из якорей — символ валюты, ISO-код валюты, множитель
тысяч (k / к / тыс. / млн), либо текстовый префикс «зп / вилка / оклад /
зарплата / salary / compensation».
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SalaryInfo:
    """Результат парсинга зарплаты."""

    salary_from: int | None
    salary_to: int | None
    salary_currency: str
    salary_period: str           # после нормализации обычно "month"
    salary_gross_type: str | None  # "gross" | "net" | None
    salary_from_rub: int | None
    salary_to_rub: int | None


# Фиксированные курсы (рублей за 1 единицу валюты).
# Менять вручную при сильном изменении курсов или подтянуть из ЦБ.
EXCHANGE_RATES_RUB: dict[str, float] = {
    "RUB": 1.0,
    "USD": 95.0,
    "USDT": 95.0,
    "EUR": 105.0,
    "GBP": 120.0,
    "KZT": 0.20,
    "UZS": 0.0075,
    "BYN": 30.0,
    "GEL": 35.0,
    "TRY": 2.7,
    "AED": 26.0,
    "INR": 1.10,
    "PLN": 24.0,
    "CNY": 13.0,
    "AMD": 0.24,
    "AZN": 56.0,
}

# === Базовые регулярные выражения ===

# Числа: 1+ цифр + опциональные группы тысяч через пробел/NBSP + опциональная
# дробная часть. Примеры: "5", "100", "100 000", "1.5", "2,5".
_NUM = r"\d+(?:[ \u00a0]\d{3})*(?:[.,]\d+)?"

# Множители (тысяч / миллионов). Длинные варианты идут раньше коротких.
_MULT = r"(?:kkk|kk|ккк|кк|млн\.?|тыс\.?|mln|mm|m|k|к|К)"

# Тире (включая en-dash, em-dash, ~)
_DASH = r"[-–—~]"

# Префиксные символы валют (могут стоять перед числом)
_CUR_SYM = r"\$|€|£|₽"

# Слова валют (могут стоять и до, и после числа). Берём с учётом регистра
# через флаг IGNORECASE при поиске.
_CUR_WORD = (
    r"\b(?:usdt|усдт|usd|eur|gbp|kzt|byn|gel|try|aed|inr|pln|cny|amd|azn|"
    r"руб(?:лей|ля)?|тенге|сум(?:ов)?|лир[аы]?|дирхам(?:ов)?|"
    r"юан(?:ей|я)?|злот(?:ых|ый)?|драм|манат)\b"
)

# Любой токен валюты: символ или слово.
_CUR_ANY = rf"(?:{_CUR_SYM}|{_CUR_WORD})"


# Маппинг символов / ключевых слов на ISO-коды валют.
_CURRENCY_PATTERNS: list[tuple[str, str]] = [
    (r"₽", "RUB"),
    (r"\$", "USD"),
    (r"€", "EUR"),
    (r"£", "GBP"),
    (r"\busdt\b|\bусдт\b", "USDT"),
    (r"\busd\b", "USD"),
    (r"\beur\b", "EUR"),
    (r"\bgbp\b", "GBP"),
    (r"\bkzt\b|\bтенге\b", "KZT"),
    (r"\buzs\b|\bсум(?:ов)?\b", "UZS"),
    (r"\bbyn\b", "BYN"),
    (r"\bgel\b", "GEL"),
    (r"\btry\b|\bлир[аы]?\b", "TRY"),
    (r"\baed\b|\bдирхам(?:ов)?\b", "AED"),
    (r"\binr\b", "INR"),
    (r"\bpln\b|\bзлот(?:ых|ый)?\b", "PLN"),
    (r"\bcny\b|\bюан(?:ей|я)?\b", "CNY"),
    (r"\bamd\b|\bдрам\b", "AMD"),
    (r"\bazn\b|\bманат\b", "AZN"),
    (r"\bруб(?:лей|ля)?\.?\b|\bр\.", "RUB"),
]


# ── Конструкции опыта работы ────────────────────────────────────────────────
# Если после числа сразу идёт слово «лет / года / год / years / yrs», это
# почти всегда срок опыта, а не зарплата. Удаляем такие куски из текста до
# запуска парсера зарплат, чтобы они не давали ложных срабатываний
# ("опыт от 3 лет" -> 3 RUB/мес, "опыт от 5к лет" -> 5 000 RUB/мес).
#
# Покрываем варианты записи: "3 лет", "3-х лет", "3х лет", "3 года", "5 years",
# "5к лет" (типовая опечатка/телеграмм-стиль). НЕ удаляем "/год", "в год",
# "за год" — это маркеры периода (зарплата за год), там перед "год" стоит
# "/" или предлог, а не число.
_EXPERIENCE_TAIL = r"(?:лет|год[ауов]?|years?|yrs?)"
_EXPERIENCE_RE = re.compile(
    rf"\b\d+(?:[-\s]*[xх])?(?:\s*[кk])?\s*{_EXPERIENCE_TAIL}\b",
    re.IGNORECASE,
)


def _strip_experience_phrases(text: str) -> str:
    """Удаляет конструкции "X лет / X-х лет / 5к лет" — это опыт, не зарплата."""
    return _EXPERIENCE_RE.sub(" ", text)


# Маркеры периода. ВАЖНО: распознаём только при явном префиксе ("/" или
# "в " / "за "), иначе "полный день" в описании ловится как период day и
# зарплата ошибочно умножается на 22.
_PERIOD_PATTERNS: list[tuple[str, str]] = [
    (
        r"(?:/|\bв\s+|\bза\s+)\s*(?:год(?:а|у)?|year|annual(?:ly)?|annum|yr|y)\b",
        "year",
    ),
    (
        r"(?:/|\bв\s+|\bза\s+)\s*(?:час(?:а|ов)?|hour|hr|h)\b",
        "hour",
    ),
    (
        r"(?:/|\bв\s+|\bза\s+)\s*(?:день|дня|day|d)\b",
        "day",
    ),
    (
        r"(?:/|\bв\s+|\bза\s+)\s*(?:мес(?:яц|яца)?\.?|month|mo|m)\b",
        "month",
    ),
]


# Множители (числовые значения).
_MULT_VALUES: dict[str, int] = {
    "kkk": 1_000_000_000,
    "ккк": 1_000_000_000,
    "kk": 1_000_000,
    "кк": 1_000_000,
    "млн": 1_000_000,
    "mln": 1_000_000,
    "mm": 1_000_000,
    "m": 1_000_000,
    "k": 1_000,
    "к": 1_000,
    "тыс": 1_000,
}

# Минимальные «осмысленные» суммы (в исходной валюте), чтобы отсеять,
# например, "1" => 1 рубль.
_MINIMAL_AMOUNT: dict[str, int] = {
    "RUB": 5_000,
    "USD": 100,
    "USDT": 100,
    "EUR": 100,
    "GBP": 100,
    "KZT": 25_000,
    "UZS": 500_000,
    "BYN": 200,
    "GEL": 250,
    "TRY": 2_500,
    "AED": 350,
    "INR": 8_000,
    "PLN": 500,
    "CNY": 700,
    "AMD": 40_000,
    "AZN": 150,
}


# === Вспомогательные функции ===


def _normalize(text: str) -> str:
    """Нормализуем NBSP, тонкие пробелы, странные кавычки."""
    return (
        text.replace("\u00a0", " ")
        .replace("\u202f", " ")
        .replace("\u2009", " ")
    )


def _detect_currency(text: str) -> str | None:
    if not text:
        return None
    for pattern, code in _CURRENCY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return code
    return None


def _detect_period(text: str) -> str | None:
    if not text:
        return None
    for pattern, period in _PERIOD_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return period
    return None


def _detect_gross(text: str) -> str | None:
    if not text:
        return None
    low = text.lower()
    if any(k in low for k in ("на руки", "после налог", "after tax", "net pay", "net ")):
        return "net"
    if any(k in low for k in ("до налог", "до вычета", "gross", "before tax")):
        return "gross"
    return None


def _normalize_cur_token(token: str | None) -> str | None:
    """Сводим символ или слово валюты к ISO-коду."""
    if not token:
        return None
    return _detect_currency(token)


def _parse_amount(num_str: str | None, mult_str: str | None) -> int | None:
    """
    Превращает строку числа (возможно с разделителями тысяч и/или дробной
    частью) в целое значение, умноженное на множитель если он указан.
    """
    if num_str is None:
        return None
    cleaned = num_str.replace(" ", "").replace("\u00a0", "")

    # Разбираемся с разделителями: если последняя группа из 1-2 цифр — это
    # десятичная часть (например "1.5", "2,5"); иначе любые точки/запятые —
    # это разделители тысяч ("100,000", "100.000").
    if "," in cleaned or "." in cleaned:
        m = re.match(r"^(.*[.,])(\d+)$", cleaned)
        if m and len(m.group(2)) <= 2 and len(m.group(1)) > 1:
            int_part = m.group(1)[:-1].replace(".", "").replace(",", "")
            cleaned = f"{int_part}.{m.group(2)}"
        else:
            cleaned = cleaned.replace(",", "").replace(".", "")

    try:
        val = float(cleaned)
    except ValueError:
        return None

    if mult_str:
        key = mult_str.lower().rstrip(".")
        if key in _MULT_VALUES:
            val *= _MULT_VALUES[key]

    return int(val)


def _validate_amount(value: int | None, currency: str) -> bool:
    """Проверяем, что сумма «осмысленная» — больше минимального порога."""
    if value is None:
        return True
    threshold = _MINIMAL_AMOUNT.get(currency.upper(), 100)
    return value >= threshold


def _monthly_equivalent(value: int | None, period: str | None) -> int | None:
    """Возвращает сумму, приведённую к месяцу (для валидации)."""
    if value is None:
        return None
    if period == "year":
        return round(value / 12)
    if period == "hour":
        return value * 168
    if period == "day":
        return value * 22
    return value


def _validate_match(
    sf: int | None,
    st: int | None,
    currency: str,
    period: str,
) -> bool:
    """Проверяем минимальный порог по месячному эквиваленту в исходной валюте."""
    sf_m = _monthly_equivalent(sf, period)
    st_m = _monthly_equivalent(st, period)
    return _validate_amount(sf_m, currency) and _validate_amount(st_m, currency)


# === Поиск кандидатов ===


def _search_window(text: str, span_start: int, span_end: int) -> str:
    """Кусок текста ±N символов вокруг найденного диапазона (для gross)."""
    win_start = max(0, span_start - 30)
    win_end = min(len(text), span_end + 50)
    return text[win_start:win_end]


def _maybe_scale_from_to(
    n1: int | None,
    n2: int | None,
    m1: str | None,
    m2: str | None,
    n1_str: str,
) -> tuple[int | None, int | None]:
    """Множитель только у верхней границы (100-200k); вариант «55 - 90 000 GBP» → 55000–90000"""
    if n1 is None or n2 is None:
        return n1, n2

    # Случай 1: явный множитель только у `to` -> применяем к `from`.
    if m2 and not m1:
        scaled = _parse_amount(n1_str, m2)
        if scaled and scaled <= int(n2 * 1.5):
            return scaled, n2

    # Случай 2: множителей нет, но у `from` сильно меньший порядок
    # ("55 - 90 000 GBP" -> понимаем как 55000 - 90000).
    if not m1 and not m2 and n1 < 1000 and n2 >= 1000 and n1 * 50 < n2:
        return n1 * 1000, n2

    return n1, n2


def _try_range(text: str) -> dict | None:
    """
    Пробуем диапазон вида X[mult] - Y[mult] [cur] [/period].
    Требуем якорь: либо валюта, либо множитель на любой из границ.
    """
    pat = re.compile(
        rf"(?P<cur_pre>{_CUR_SYM})?\s*"
        rf"(?P<n1>{_NUM})\s*(?P<m1>{_MULT})?"
        rf"\s*{_DASH}\s*"
        rf"(?P<n2>{_NUM})\s*(?P<m2>{_MULT})?"
        rf"(?P<rest>[^\n]{{0,40}})",
        re.IGNORECASE,
    )

    for m in pat.finditer(text):
        cur_pre = m.group("cur_pre")
        m1 = m.group("m1")
        m2 = m.group("m2")
        rest = m.group("rest") or ""

        cur_code = _normalize_cur_token(cur_pre) or _detect_currency(rest)

        # Якорь: валюта или множитель.
        if not (cur_code or m1 or m2):
            continue

        n1 = _parse_amount(m.group("n1"), m1)
        n2 = _parse_amount(m.group("n2"), m2)

        if n1 is None and n2 is None:
            continue

        n1, n2 = _maybe_scale_from_to(n1, n2, m1, m2, m.group("n1"))

        # Сортируем from <= to.
        if n1 and n2 and n1 > n2:
            n1, n2 = n2, n1

        currency = cur_code or "RUB"
        period = _detect_period(rest) or "month"
        if not _validate_match(n1, n2, currency, period):
            continue

        return {
            "from": n1,
            "to": n2,
            "currency": currency,
            "period": period,
            "gross": _detect_gross(_search_window(text, m.start(), m.end())),
        }
    return None


def _try_from_to_words(text: str) -> dict | None:
    """
    «от X [mult] до Y [mult] [cur]» — рус. форма диапазона без явного тире.
    """
    pat = re.compile(
        rf"\bот\s+(?P<n1>{_NUM})\s*(?P<m1>{_MULT})?"
        rf"\s+до\s+(?P<n2>{_NUM})\s*(?P<m2>{_MULT})?"
        rf"(?P<rest>[^\n]{{0,40}})",
        re.IGNORECASE,
    )

    for m in pat.finditer(text):
        m1 = m.group("m1")
        m2 = m.group("m2")
        rest = m.group("rest") or ""

        cur_code = _detect_currency(rest)
        if not (cur_code or m1 or m2):
            continue

        # Если множитель указан только у одной границы — применим к обеим.
        if m2 and not m1:
            m1 = m2
        elif m1 and not m2:
            m2 = m1

        n1 = _parse_amount(m.group("n1"), m1)
        n2 = _parse_amount(m.group("n2"), m2)
        if n1 is None or n2 is None:
            continue

        if n1 > n2:
            n1, n2 = n2, n1

        currency = cur_code or "RUB"
        period = _detect_period(rest) or "month"
        if not _validate_match(n1, n2, currency, period):
            continue

        return {
            "from": n1,
            "to": n2,
            "currency": currency,
            "period": period,
            "gross": _detect_gross(_search_window(text, m.start(), m.end())),
        }
    return None


def _try_from_only(text: str) -> dict | None:
    """«от X [mult] [cur]» — нижняя граница."""
    pat = re.compile(
        rf"\bот\s+(?P<cur_pre>{_CUR_SYM})?\s*(?P<n>{_NUM})\s*(?P<m>{_MULT})?"
        rf"(?P<rest>[^\n]{{0,40}})",
        re.IGNORECASE,
    )

    for m in pat.finditer(text):
        cur_pre = m.group("cur_pre")
        mult = m.group("m")
        rest = m.group("rest") or ""

        cur_code = _normalize_cur_token(cur_pre) or _detect_currency(rest)
        if not (cur_code or mult):
            continue

        n = _parse_amount(m.group("n"), mult)
        if n is None:
            continue

        currency = cur_code or "RUB"
        period = _detect_period(rest) or "month"
        if not _validate_match(n, None, currency, period):
            continue

        return {
            "from": n,
            "to": None,
            "currency": currency,
            "period": period,
            "gross": _detect_gross(_search_window(text, m.start(), m.end())),
        }
    return None


def _try_to_only(text: str) -> dict | None:
    """«до X [mult] [cur]» — верхняя граница."""
    pat = re.compile(
        rf"\bдо\s+(?P<cur_pre>{_CUR_SYM})?\s*(?P<n>{_NUM})\s*(?P<m>{_MULT})?"
        rf"(?P<rest>[^\n]{{0,40}})",
        re.IGNORECASE,
    )

    for m in pat.finditer(text):
        cur_pre = m.group("cur_pre")
        mult = m.group("m")
        rest = m.group("rest") or ""

        cur_code = _normalize_cur_token(cur_pre) or _detect_currency(rest)
        if not (cur_code or mult):
            continue

        n = _parse_amount(m.group("n"), mult)
        if n is None:
            continue

        currency = cur_code or "RUB"
        period = _detect_period(rest) or "month"
        if not _validate_match(None, n, currency, period):
            continue

        return {
            "from": None,
            "to": n,
            "currency": currency,
            "period": period,
            "gross": _detect_gross(_search_window(text, m.start(), m.end())),
        }
    return None


def _try_single(text: str) -> dict | None:
    """
    Одиночное число с явной валютой и/или множителем.
    Например: "$5000", "5000 USD", "275 тыс. руб", "100к руб".
    """
    # Вариант 1: символ валюты ПЕРЕД числом ("$5000", "$5k").
    pat_pre = re.compile(
        rf"(?P<cur_pre>{_CUR_SYM})\s*(?P<n>{_NUM})\s*(?P<m>{_MULT})?"
        rf"(?P<rest>[^\n]{{0,40}})",
        re.IGNORECASE,
    )

    for m in pat_pre.finditer(text):
        cur_pre = m.group("cur_pre")
        mult = m.group("m")
        rest = m.group("rest") or ""

        # Если в rest есть тире — это диапазон, его обработает _try_range.
        if re.search(_DASH, rest[:5]):
            continue

        currency = _normalize_cur_token(cur_pre)
        if not currency:
            continue

        n = _parse_amount(m.group("n"), mult)
        if n is None:
            continue

        period = _detect_period(rest) or "month"
        if not _validate_match(n, None, currency, period):
            continue

        return {
            "from": n,
            "to": None,
            "currency": currency,
            "period": period,
            "gross": _detect_gross(_search_window(text, m.start(), m.end())),
        }

    # Вариант 2: число, потом множитель/валюта ("5000 USD", "275 тыс. руб").
    pat_post = re.compile(
        rf"(?P<n>{_NUM})\s*(?P<m>{_MULT})?\s*(?P<cur>{_CUR_WORD})"
        rf"(?P<rest>[^\n]{{0,40}})",
        re.IGNORECASE,
    )

    for m in pat_post.finditer(text):
        mult = m.group("m")
        cur_word = m.group("cur")
        rest = m.group("rest") or ""

        currency = _detect_currency(cur_word)
        if not currency:
            continue

        n = _parse_amount(m.group("n"), mult)
        if n is None:
            continue

        period = _detect_period(rest) or "month"
        if not _validate_match(n, None, currency, period):
            continue

        return {
            "from": n,
            "to": None,
            "currency": currency,
            "period": period,
            "gross": _detect_gross(_search_window(text, m.start(), m.end())),
        }

    return None


# === Публичные функции ===


def parse_salary(text: str | None) -> SalaryInfo | None:
    """
    Главный парсер. Принимает произвольный текст вакансии (заголовок + описание),
    возвращает SalaryInfo или None если зарплата не распознана.
    """
    if not text:
        return None

    t = _normalize(text)
    # Вырезаем фразы об опыте работы ("от 3 лет", "3-х лет", "5к лет"), чтобы
    # они не считались зарплатой. Период зарплаты ("/год", "в год") не
    # затрагивается — там перед "год" стоит "/" или предлог, не цифра.
    t = _strip_experience_phrases(t)
    # Берём первую часть текста — обычно зарплата указана в начале вакансии.
    sample = t[:3000]

    # Пробуем по убыванию специфичности.
    parsed = (
        _try_range(sample)
        or _try_from_to_words(sample)
        or _try_from_only(sample)
        or _try_to_only(sample)
        or _try_single(sample)
    )
    if parsed is None:
        return None

    return _finalize(parsed)


def _finalize(parsed: dict) -> SalaryInfo:
    sf = parsed["from"]
    st = parsed["to"]
    currency = parsed["currency"].upper()
    period = parsed["period"] or "month"
    gross = parsed["gross"]

    # Нормализация к месяцу.
    if period == "year":
        sf = round(sf / 12) if sf else None
        st = round(st / 12) if st else None
    elif period == "hour":
        # ~168 рабочих часов в месяц (40ч * 4.2 недели).
        sf = sf * 168 if sf else None
        st = st * 168 if st else None
    elif period == "day":
        sf = sf * 22 if sf else None
        st = st * 22 if st else None

    sf_rub, st_rub = compute_rub_amounts(sf, st, currency)

    return SalaryInfo(
        salary_from=sf,
        salary_to=st,
        salary_currency=currency,
        salary_period="month",
        salary_gross_type=gross,
        salary_from_rub=sf_rub,
        salary_to_rub=st_rub,
    )


def compute_rub_amounts(
    salary_from: int | None,
    salary_to: int | None,
    currency: str | None,
) -> tuple[int | None, int | None]:
    """
    Считает рублёвый эквивалент для заданных from/to и валюты по фиксированным
    курсам. Используется как из парсера, так и из vacancy-service при
    upsert-е канонической вакансии.
    """
    if not currency:
        return salary_from, salary_to
    rate = EXCHANGE_RATES_RUB.get(currency.upper())
    if rate is None:
        return None, None
    sf_rub = round(salary_from * rate) if salary_from else None
    st_rub = round(salary_to * rate) if salary_to else None
    return sf_rub, st_rub


def normalize_period_to_month(
    salary_from: int | None,
    salary_to: int | None,
    period: str | None,
) -> tuple[int | None, int | None, str]:
    """
    Приводит зарплату к месячному эквиваленту в той же валюте.
    Возвращает (from, to, "month"). Не меняет валюту.
    """
    if period == "year":
        return (
            round(salary_from / 12) if salary_from else None,
            round(salary_to / 12) if salary_to else None,
            "month",
        )
    if period == "hour":
        return (
            salary_from * 168 if salary_from else None,
            salary_to * 168 if salary_to else None,
            "month",
        )
    if period == "day":
        return (
            salary_from * 22 if salary_from else None,
            salary_to * 22 if salary_to else None,
            "month",
        )
    return salary_from, salary_to, "month"


__all__ = [
    "SalaryInfo",
    "EXCHANGE_RATES_RUB",
    "parse_salary",
    "compute_rub_amounts",
    "normalize_period_to_month",
]
