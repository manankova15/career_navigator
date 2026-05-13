"""
Сбор вакансий из Telegram-канала через официальный Telegram API (Telethon).

─── Как запустить ───────────────────────────────────────────────────────────

1. Установите зависимости (один раз):
       pip install telethon requests --break-system-packages

2. Вставьте свои api_id и api_hash в файл .env:
       TELEGRAM_API_ID=12345678
       TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890

3. Запустите скрипт (сервисы должны работать в Docker):
       python scripts/seed_telegram_vacancies.py

   При ПЕРВОМ запуске Telethon спросит «phone (or bot token)» — введите только
   **номер личного аккаунта** в формате +7XXXXXXXXXX. Токен бота из @BotFather
   сюда вводить **нельзя**: бот не может читать историю каналов через этот API
   (будет BotMethodInvalidError).

     • Telegram пришлёт код в приложение Telegram (раздел входов / устройств).
     • Введите код — сессия сохранится в файл scripts/.tg_session.session
       (повторная авторизация не нужна). Если видите «too many values to unpack» —
       удалите этот файл или запустите: python3 scripts/seed_telegram_vacancies.py --reset-session

   Если вы уже случайно вошли как бот — снова: --reset-session и вход по телефону.

─── Что делает скрипт ───────────────────────────────────────────────────────

  • Читает каналы из файла scripts/telegram_channels.txt (по одному юзернейму на строку)
    или один канал из переменной TELEGRAM_CHANNEL (по умолчанию job_for_analysts).
  • Парсит сообщения, извлекая: должность, компанию, зарплату, локацию, навыки.
  • Добавляет вакансии в vacancy-service через внутренний REST API.
  • Не требует быть подписанным на канал.
  • Не нарушает правила Telegram: официальный API, задержки между запросами.

─── Параметры ───────────────────────────────────────────────────────────────

  TELEGRAM_CHANNEL   — один канал (если не задан файл каналов)
  TELEGRAM_CHANNELS — путь к файлу со списком каналов (по умолчанию telegram_channels.txt в этой папке)
  TELEGRAM_SESSION  — путь к файлу сессии без суффикса .session (по умолчанию scripts/.tg_session)
  TELEGRAM_TARGET_COUNT — сколько вакансий собрать всего со всех каналов
  VACANCY_SERVICE_URL — URL вашего vacancy-service

  Флаги:
  --reset-session   — удалить локальные файлы сессии Telethon перед запуском (новый вход в Telegram)
"""

import asyncio
import json
import os
import re
import sys
import time
import uuid
import base64
import hashlib
import hmac

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backfill_classification import (  # noqa: E402
    classify_profession_area,
    classify_specialization,
    infer_education_level,
    infer_employment_type,
    infer_english_level,
    infer_experience_level,
    infer_schedule_type,
    infer_work_format,
    split_location,
)
from salary_parser import parse_salary as _parse_salary_full  # noqa: E402

# ── Параметры ─────────────────────────────────────────────────────────────────

# Файл со списком каналов (юзернейм без @ на строку; # и пустые — игнор)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNELS_FILE = os.getenv("TELEGRAM_CHANNELS", os.path.join(SCRIPT_DIR, "telegram_channels.txt"))

# Канал по умолчанию, если нет файла со списком
TELEGRAM_CHANNEL_DEFAULT = os.getenv("TELEGRAM_CHANNEL", "job_for_analysts")

# Количество вакансий для загрузки (всего со всех каналов)
TARGET_COUNT = int(os.getenv("TELEGRAM_TARGET_COUNT", "1000"))
# Максимум сообщений на итерацию (Telegram отдаёт по 100 штук)
BATCH_SIZE = 100
# Задержка между запросами (секунды) — важно для соблюдения лимитов
REQUEST_DELAY = 1.5

VACANCY_SERVICE_URL = os.getenv("VACANCY_SERVICE_URL", "http://localhost:8004")

# Имя сессии Telethon (к пути добавится .session); после load_dotenv — TELEGRAM_SESSION
_DEFAULT_TG_SESSION = os.path.join(SCRIPT_DIR, ".tg_session")


def _session_base() -> str:
    """Базовый путь сессии (как первый аргумент TelegramClient). .env уже должен быть загружен."""
    return os.getenv("TELEGRAM_SESSION", _DEFAULT_TG_SESSION)


def _telethon_sqlite_path(session_base: str | None = None) -> str:
    """Путь к файлу БД сессии Telethon (…/name.session)."""
    base = session_base if session_base is not None else _session_base()
    return base if base.endswith(".session") else base + ".session"


def _remove_corrupt_session_files(session_base: str | None = None) -> list[str]:
    """Удаляет файлы сессии Telethon (основной + journal/wal/shm). Возвращает список удалённых."""
    base = _telethon_sqlite_path(session_base)
    removed: list[str] = []
    for suffix in ("", "-journal", "-wal", "-shm"):
        path = base + suffix if suffix else base
        try:
            if os.path.isfile(path):
                os.remove(path)
                removed.append(path)
        except OSError:
            pass
    return removed


def load_telegram_channels() -> list[str]:
    """Читает список каналов из файла или возвращает один канал из TELEGRAM_CHANNEL."""
    if os.path.exists(CHANNELS_FILE):
        channels = []
        with open(CHANNELS_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    channels.append(line.lstrip("@"))
        if channels:
            return channels
    return [TELEGRAM_CHANNEL_DEFAULT]


def get_source_id(channel: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://t.me/{channel}"))

# ── JWT для внутреннего API ────────────────────────────────────────────────────

def make_admin_jwt() -> str:
    """Генерирует временный JWT с ролью admin для вызова внутреннего API."""
    secret = os.getenv("JWT_SECRET", "my_super_secret_jwt_key_change_in_prod")
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload_data = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "roles": ["admin", "superadmin"],
        "type": "access",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    payload = base64.urlsafe_b64encode(
        json.dumps(payload_data).encode()
    ).rstrip(b"=").decode()
    sig_input = f"{header}.{payload}".encode()
    sig = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), sig_input, hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


INTERNAL_HEADERS = {
    "Authorization": f"Bearer {make_admin_jwt()}",
    "Content-Type": "application/json",
}

# ── Парсинг сообщений ─────────────────────────────────────────────────────────

_SENIORITY_MAP = [
    ("intern",  ["стажёр", "стажер", "intern", "trainee"]),
    ("junior",  ["junior", "джун", "джуниор", "начинающий"]),
    ("middle",  ["middle", "мидл", "миддл"]),
    ("senior",  ["senior", "сеньор", "ведущий"]),
    ("lead",    ["lead", "лид", "principal", "staff", "архитектор", "руководитель"]),
]

# Типичные IT-навыки для обнаружения в тексте
_SKILL_KEYWORDS = [
    "Python", "SQL", "Excel", "Power BI", "Tableau", "R",
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
    "PostgreSQL", "MySQL", "ClickHouse", "Redshift", "BigQuery",
    "Spark", "Hadoop", "Airflow", "dbt", "Kafka",
    "Machine Learning", "Deep Learning", "NLP",
    "TensorFlow", "PyTorch", "scikit-learn", "Catboost", "XGBoost",
    "Git", "Docker", "Kubernetes", "Linux",
    "A/B тесты", "A/B testing", "статистика", "statistics",
    "Google Analytics", "Amplitude", "Mixpanel",
    "JIRA", "Confluence", "Notion",
    "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "Java", "Kotlin", "Go", "Golang", "C++", "C#", ".NET",
    "Swift", "iOS", "Android",
    "REST", "API", "GraphQL",
    "AWS", "GCP", "Azure",
    "Looker", "Superset", "Metabase",
]

_LOCATION_PATTERNS = [
    re.compile(r"(?:локация|место работы|город|офис)[:\s]+([^\n,;]{3,40})", re.IGNORECASE),
    re.compile(r"📍\s*([^\n,;]{3,40})"),
    re.compile(r"🗺\s*([^\n,;]{3,40})"),
    re.compile(r"(?:москва|санкт-петербург|спб|питер|новосибирск|екатеринбург|казань|удалённо|remote|дистанционно)", re.IGNORECASE),
]

_COMPANY_PATTERNS = [
    re.compile(r"(?:компания|работодатель|company)[:\s]+([^\n]{3,100})", re.IGNORECASE),
    re.compile(r"🏢\s*([^\n]{3,100})"),
    re.compile(r"🏦\s*([^\n]{3,100})"),
    re.compile(r"(?:ООО|ОАО|ЗАО|АО|ИП)\s+[«\"]?([^\n»\"]{3,80})"),
]

# Markdown link pattern: [text](url)
_MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)", re.IGNORECASE)

# Markdown emphasis patterns (Telegram uses __text__ for bold, *text* for italic).
_MD_EMPHASIS_PATTERNS = [
    re.compile(r"\*\*(.+?)\*\*", re.DOTALL),
    re.compile(r"__(.+?)__", re.DOTALL),
    re.compile(r"~~(.+?)~~", re.DOTALL),
]

# Lead-in tokens we explicitly drop from the cleaned title (e.g. "__tldr ... __" → "").
_TITLE_LEAD_TOKENS = ("tldr", "tl;dr", "tl dr")


def _strip_markdown_links(text: str) -> str:
    """Replace [text](url) with just 'text'."""
    return _MD_LINK_PATTERN.sub(r"\1", text)


def _strip_markdown_emphasis(text: str) -> str:
    """Strip Telegram Markdown emphasis markers (**bold**, __bold__, ~~strike~~)."""
    out = text
    for _ in range(2):
        for pat in _MD_EMPHASIS_PATTERNS:
            out = pat.sub(r"\1", out)
    return out


def _clean_title(raw: str) -> str:
    """Final clean-up for vacancy titles parsed from TG posts."""
    s = _strip_markdown_emphasis(raw)
    s = s.strip().strip("_*-—–·• \t")
    low = s.lower()
    for token in _TITLE_LEAD_TOKENS:
        if low.startswith(token):
            s = s[len(token):].lstrip(" :—-·•_*")
            break
    return s.strip()


def parse_salary(text: str) -> tuple[
    int | None, int | None, str, str | None, str, int | None, int | None
]:
    """
    Извлекает зарплату через salary_parser.parse_salary. Возвращает кортеж:
      (salary_from, salary_to, salary_currency, salary_gross_type,
       salary_period, salary_from_rub, salary_to_rub)
    Все суммы — в исходной валюте, приведённые к месяцу.
    """
    info = _parse_salary_full(text)
    if info is None:
        return None, None, "RUB", None, "month", None, None
    return (
        info.salary_from,
        info.salary_to,
        info.salary_currency,
        info.salary_gross_type,
        info.salary_period,
        info.salary_from_rub,
        info.salary_to_rub,
    )


def parse_seniority(text: str) -> str | None:
    """Возвращает все найденные уровни через запятую (например 'middle, senior')."""
    lower = text.lower()
    found = []
    for level, keywords in _SENIORITY_MAP:
        if any(k in lower for k in keywords) and level not in found:
            found.append(level)
    return ", ".join(found) if found else None


def parse_skills(text: str) -> list[str]:
    found = []
    for skill in _SKILL_KEYWORDS:
        if re.search(re.escape(skill), text, re.IGNORECASE):
            found.append(skill)
    return found[:20]


def parse_location(text: str) -> str | None:
    for pat in _LOCATION_PATTERNS:
        m = pat.search(text)
        if m:
            loc = m.group(1).strip() if m.lastindex else m.group(0).strip()
            return loc[:100]
    return None


def parse_company(text: str) -> str | None:
    for pat in _COMPANY_PATTERNS:
        m = pat.search(text)
        if m:
            company = m.group(1).strip()[:200]
            # Strip Markdown link format [Company Name](url) → Company Name
            company = _strip_markdown_links(company)
            # And drop emphasis markers like __Company__ → Company.
            company = _strip_markdown_emphasis(company).strip().strip("_*")
            return company or None
    return None


def extract_title(text: str) -> str:
    """Берём первую непустую строку как заголовок вакансии."""
    cleaned_text = _strip_markdown_emphasis(text)
    for line in cleaned_text.strip().splitlines():
        clean = re.sub(r"[^\w\s\-\+\./,()А-Яа-яёЁ]", "", line).strip()
        clean = _clean_title(clean)
        if len(clean) > 5:
            return clean[:300]
    # Fallback: первые 80 символов первой строки
    first_line = cleaned_text.strip().splitlines()[0] if cleaned_text.strip() else "Вакансия"
    return _clean_title(first_line)[:300] or "Вакансия"


def is_vacancy_message(text: str) -> bool:
    """Грубая проверка — похоже ли сообщение на вакансию."""
    if not text or len(text) < 50:
        return False
    lower = text.lower()
    vacancy_markers = [
        "вакансия", "ищем", "требуется", "нужен", "нужна", "открыта позиция",
        "job", "vacancy", "hiring", "analyst", "аналитик", "разработчик",
        "developer", "engineer", "инженер", "менеджер", "manager",
        "опыт", "зарплата", "salary", "обязанности", "требования",
        "откликнуться", "резюме", "cv", "hh.ru", "t.me", "career",
    ]
    return sum(1 for m in vacancy_markers if m in lower) >= 2


def contains_multiple_vacancies(text: str) -> bool:
    """Определяет, что в одном посте перечислено несколько вакансий (такие посты пропускаем)."""
    if not text or len(text) < 100:
        return False
    # Нумерованные блоки вакансий: "1. ... 2. ... 3. ..." или "Вакансия 1 / 2 / 3"
    numbered_vacancy = re.compile(
        r"(?:^|\n)\s*(?:\d+[.)]\s*|ваканси[яи]\s*\d+|#\d+)\s*[:\-]?\s*"
        r".{20,200}(?:ваканси|ищем|требуется|нужен|нужна|hiring|job)",
        re.IGNORECASE | re.MULTILINE,
    )
    if len(numbered_vacancy.findall(text)) >= 2:
        return True
    # Несколько явных заголовков "Вакансия:" или "Ищем:" в разных местах (разделены переносами)
    parts = re.split(r"\n\s*\n", text)
    vacancy_headers = [
        p.strip()
        for p in parts
        if re.search(r"^(ваканси[яи]|ищем|требуется|открыта позиция)\s*[:\-]", p[:80], re.IGNORECASE)
    ]
    if len(vacancy_headers) >= 2:
        return True
    # Маркеры "• Вакансия" или "— Вакансия" повторяются 2+ раз
    bullet_vacancy = re.compile(r"(?:^|\n)\s*[•\-*]\s*(?:ваканси|ищем|требуется)", re.IGNORECASE | re.MULTILINE)
    if len(bullet_vacancy.findall(text)) >= 2:
        return True
    return False


def parse_message(msg_id: int, text: str, date, channel: str) -> dict | None:
    """Парсим одно сообщение в структуру вакансии. channel — юзернейм канала без @."""
    if not is_vacancy_message(text):
        return None
    if contains_multiple_vacancies(text):
        return None

    title      = extract_title(text)
    company    = parse_company(text)
    location   = parse_location(text)
    (
        salary_from,
        salary_to,
        currency,
        gross_type,
        period,
        salary_from_rub,
        salary_to_rub,
    ) = parse_salary(text)
    seniority  = parse_seniority(text)
    skills     = parse_skills(text)
    # Кнопка «Откликнуться на источнике» ведёт на пост в Telegram; ссылки из текста (hh.ru и т.д.) остаются в description.
    canonical_url = f"https://t.me/{channel}/{msg_id}"
    source_id  = get_source_id(channel)

    published_at = date.isoformat() if date else None

    blob = " ".join(p for p in [title, company or "", text, location or "", " ".join(skills)] if p)
    city_guess, country_guess = split_location(location)

    return {
        "source_id":         source_id,
        "external_id":       f"tg_{channel}_{msg_id}",
        "title":             title,
        "company":           company or "Не указано",
        "canonical_url":     canonical_url,
        "location":          location,
        "location_city":     city_guess,
        "location_country":  country_guess,
        "salary_from":       salary_from,
        "salary_to":         salary_to,
        "salary_currency":   currency,
        "salary_period":     period,
        "salary_gross_type": gross_type,
        "salary_from_rub":   salary_from_rub,
        "salary_to_rub":     salary_to_rub,
        "seniority":         seniority,
        "employment_type":   infer_employment_type(blob),
        "work_format":       infer_work_format(blob),
        "schedule_type":     infer_schedule_type(blob),
        "experience_level":  infer_experience_level(blob, seniority),
        "profession_area":   classify_profession_area(blob, title),
        "specialization":    classify_specialization(blob, title),
        "english_level":     infer_english_level(blob),
        "education_level":   infer_education_level(blob),
        "description":       text[:4000],
        "skills":            skills,
        "status":            "active",
        "published_at":      published_at,
    }


# ── Отправка в vacancy-service ────────────────────────────────────────────────

def post_vacancy(vacancy_data: dict) -> bool:
    url = f"{VACANCY_SERVICE_URL}/internal/canonical"
    try:
        resp = requests.post(url, json=vacancy_data, headers=INTERNAL_HEADERS, timeout=10)
        if resp.status_code in (200, 201):
            return True
        print(f"  ⚠ Ошибка добавления вакансии: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"  ⚠ Сетевая ошибка: {e}")
        return False


# ── Telethon: сбор вакансий ─────────────────────────────────────────────────────

async def collect_vacancies():
    try:
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
    except ImportError:
        print(
            "❌ Пакет telethon не установлен.\n"
            "   Выполните: pip install telethon --break-system-packages"
        )
        return

    api_id   = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or api_id == "YOUR_API_ID_HERE":
        print(
            "❌ TELEGRAM_API_ID не задан!\n"
            "   Откройте файл .env и замените YOUR_API_ID_HERE на ваш api_id\n"
            "   (его можно найти на https://my.telegram.org → API development tools)"
        )
        return

    if not api_hash or api_hash == "YOUR_API_HASH_HERE":
        print(
            "❌ TELEGRAM_API_HASH не задан!\n"
            "   Откройте файл .env и замените YOUR_API_HASH_HERE на ваш api_hash\n"
            "   (его можно найти на https://my.telegram.org → API development tools)"
        )
        return

    session_base = _session_base()
    sqlite_path = _telethon_sqlite_path(session_base)

    print(f"[tg-seed] Подключаюсь к Telegram (api_id={api_id})…")
    print(f"[tg-seed] Файл сессии (SQLite): {sqlite_path}")

    try:
        client = TelegramClient(session_base, int(api_id), api_hash)
    except ValueError as e:
        err = str(e).lower()
        if "unpack" in err or "expected" in err:
            print(
                "\n[tg-seed] Не удалось прочитать файл сессии Telethon — он повреждён, "
                "не от Telethon или создан очень старой версией библиотеки.\n"
                f"   Файл: {sqlite_path}\n\n"
                "   Удалите его и запустите скрипт снова (Telegram снова запросит код из приложения):\n"
                f"     rm -f {sqlite_path!r} {sqlite_path + '-journal'!r} "
                f"{sqlite_path + '-wal'!r} {sqlite_path + '-shm'!r}\n\n"
                "   Или одной командой:\n"
                "     python3 scripts/seed_telegram_vacancies.py --reset-session\n"
            )
            return
        raise

    await client.start()          # При первом запуске запросит телефон и код из Telegram

    me = await client.get_me()
    if getattr(me, "bot", False):
        print(
            "\n❌ [tg-seed] Сейчас активна сессия **бота** (вы ввели токен из @BotFather).\n"
            "   Чтение истории публичных каналов через Telethon делается методом, который\n"
            "   для ботов Telegram **запрещает** — отсюда BotMethodInvalidError на get_messages.\n\n"
            "   Нужен **личный аккаунт** (ваш номер телефона + SMS-код в приложении Telegram).\n"
            "   Токен TELEGRAM_BOT_TOKEN из .env для этого скрипта не подходит.\n\n"
            "   Дальнейшие шаги:\n"
            "     1) python3 scripts/seed_telegram_vacancies.py --reset-session\n"
            "     2) На запрос phone введите +7XXXXXXXXXX (не токен бота).\n"
            "     3) Введите код из приложения Telegram.\n"
        )
        await client.disconnect()
        return

    channels = load_telegram_channels()
    who = me.username or me.first_name or "user"
    print(f"[tg-seed] Авторизован как: @{who}" if me.username else f"[tg-seed] Авторизован как: {who}")
    print(f"[tg-seed] Каналы: {', '.join('@' + c for c in channels)}")
    print(f"[tg-seed] Цель: {TARGET_COUNT} вакансий всего.\n")

    loaded  = 0
    skipped = 0

    for channel in channels:
        if loaded >= TARGET_COUNT:
            break
        offset_id = 0
        print(f"[tg-seed] Канал @{channel}…")

        while loaded < TARGET_COUNT:
            batch = await client.get_messages(
                f"@{channel}",
                limit=BATCH_SIZE,
                offset_id=offset_id,
            )
            if not batch:
                print(f"  @{channel}: сообщения закончились.")
                break

            for msg in batch:
                text = msg.text or msg.message or ""
                if not text:
                    continue

                vacancy = parse_message(msg.id, text, msg.date, channel)
                if vacancy is None:
                    skipped += 1
                    continue

                ok = post_vacancy(vacancy)
                if ok:
                    loaded += 1
                    sal_str = ""
                    if vacancy["salary_from"] or vacancy["salary_to"]:
                        f_ = vacancy["salary_from"] or "?"
                        t_ = vacancy["salary_to"]   or "?"
                        sal_str = f" | {f_}–{t_} {vacancy.get('salary_currency', 'RUB')}"
                    print(
                        f"  [{loaded}/{TARGET_COUNT}] ✓ {vacancy['title'][:55]}"
                        f" @ {vacancy['company'][:25]}{sal_str}"
                    )
                else:
                    skipped += 1

                if loaded >= TARGET_COUNT:
                    break

            offset_id = batch[-1].id
            await asyncio.sleep(REQUEST_DELAY)

    await client.disconnect()

    print(f"\n[tg-seed] Готово!")
    print(f"  Загружено вакансий : {loaded}")
    print(f"  Пропущено сообщений: {skipped}")


def main():
    # Загружаем .env вручную (без python-dotenv)
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

    if "--reset-session" in sys.argv:
        removed = _remove_corrupt_session_files()
        if removed:
            print(f"[tg-seed] Удалены файлы сессии ({len(removed)} шт.):")
            for p in removed:
                print(f"   • {p}")
        else:
            print("[tg-seed] Файлов сессии Telethon не найдено (сбрасывать нечего).")

    asyncio.run(collect_vacancies())


if __name__ == "__main__":
    main()
