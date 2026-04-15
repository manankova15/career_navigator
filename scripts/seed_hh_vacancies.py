"""
Seed script: загружает IT-вакансии из публичного API HH.ru
и добавляет их в vacancy-service через внутренний REST API.

Запуск (пока сервисы в Docker работают):
    python scripts/seed_hh_vacancies.py

Требования:
    pip install requests

Используем официальный публичный API hh.ru:
  https://api.hh.ru/openapi/redoc  (без авторизации, с ограничением ~200 req/day на IP)
  Задержка между запросами 0.5с — безопасно, не попадём под блокировку.
"""

import time
import uuid
import json
import datetime
import requests
import sys
import os

# ── Настройки ────────────────────────────────────────────────────────────────
VACANCY_SERVICE_URL = os.getenv("VACANCY_SERVICE_URL", "http://localhost:8004")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "my_internal_service_token")

HH_API_BASE = "https://api.hh.ru"
HH_AREA_RUSSIA = 113       # Россия
HH_SEARCH_QUERY = "Python OR JavaScript OR Backend OR Frontend OR Data Engineer"
TARGET_COUNT = int(os.getenv("HH_TARGET_COUNT", "500"))  # сколько вакансий загрузить

FAKE_SOURCE_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://hh.ru"))

HEADERS_HH = {
    "User-Agent": "CareerNavigator/1.0 (student diploma project; contact: student@university.ru)",
    "Accept": "application/json",
}


def make_admin_jwt() -> str:
    """Создаём временный JWT с ролью admin для seeder."""
    import base64 as b64, hmac, hashlib, time as _time
    secret = os.getenv("JWT_SECRET", "my_super_secret_jwt_key_change_in_prod")
    header = b64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    payload_data = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "roles": ["admin", "superadmin"],
        "type": "access",
        "iat": int(_time.time()),
        "exp": int(_time.time()) + 3600,
    }
    payload = b64.urlsafe_b64encode(json.dumps(payload_data).encode()).rstrip(b"=").decode()
    sig_input = f"{header}.{payload}".encode()
    sig = b64.urlsafe_b64encode(
        hmac.new(secret.encode(), sig_input, hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


INTERNAL_HEADERS = {
    "Authorization": f"Bearer {make_admin_jwt()}",
    "Content-Type": "application/json",
}

SENIORITY_KEYWORDS = {
    "intern": ["intern", "стажёр", "стажер", "trainee"],
    "junior": ["junior", "джун", "джуниор", "начинающий"],
    "middle": ["middle", "мидл", "миддл"],
    "senior": ["senior", "сеньор", "ведущий"],
    "lead": ["lead", "лид", "principal", "staff", "архитектор", "руководитель"],
}


def detect_seniority(title: str, description: str | None = None) -> str | None:
    """Ищет все упомянутые уровни в заголовке и описании, возвращает через запятую."""
    text = (title + " " + (description or "")).lower()
    found = []
    for level, kw in SENIORITY_KEYWORDS.items():
        if any(k in text for k in kw) and level not in found:
            found.append(level)
    return ", ".join(found) if found else None


def extract_skills(vacancy_detail: dict) -> list[str]:
    skills = []
    for s in vacancy_detail.get("key_skills", []):
        name = s.get("name", "").strip()
        if name:
            skills.append(name[:100])
    return skills[:20]


def salary_info(vacancy: dict) -> tuple[int | None, int | None, str]:
    sal = vacancy.get("salary") or {}
    salary_from = sal.get("from")
    salary_to = sal.get("to")
    currency = sal.get("currency", "RUR")
    if currency == "RUR":
        currency = "RUB"
    return salary_from, salary_to, currency


def fetch_vacancy_detail(hh_id: str) -> dict:
    url = f"{HH_API_BASE}/vacancies/{hh_id}"
    resp = requests.get(url, headers=HEADERS_HH, timeout=10)
    resp.raise_for_status()
    return resp.json()


def ensure_source_exists():
    """Убеждаемся, что source_id существует в source-service.
    Если нет — просто используем UUID без создания (vacancy-service не проверяет FK по source_id)."""
    return FAKE_SOURCE_ID


def post_canonical(vacancy_data: dict) -> bool:
    url = f"{VACANCY_SERVICE_URL}/internal/canonical"
    resp = requests.post(url, json=vacancy_data, headers=INTERNAL_HEADERS, timeout=10)
    if resp.status_code in (200, 201):
        return True
    print(f"  ⚠ Ошибка добавления вакансии: {resp.status_code} {resp.text[:200]}")
    return False


def run():
    source_id = ensure_source_exists()
    print(f"[hh-seed] Source ID: {source_id}")
    print(f"[hh-seed] Цель: загрузить {TARGET_COUNT} вакансий из HH.ru")

    loaded = 0
    page = 0
    per_page = 20

    while loaded < TARGET_COUNT:
        params = {
            "text": HH_SEARCH_QUERY,
            "area": HH_AREA_RUSSIA,
            "per_page": per_page,
            "page": page,
            "only_with_salary": False,
            "professional_role": "96",  # 96 = Программист/разработчик
        }

        print(f"[hh-seed] Запрос страницы {page}…")
        try:
            resp = requests.get(f"{HH_API_BASE}/vacancies", params=params,
                                headers=HEADERS_HH, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[hh-seed] Ошибка запроса к HH API: {e}")
            break

        data = resp.json()
        items = data.get("items", [])
        if not items:
            print("[hh-seed] Больше нет вакансий.")
            break

        for item in items:
            if loaded >= TARGET_COUNT:
                break

            hh_id = str(item.get("id", ""))
            title = item.get("name", "").strip()
            company = (item.get("employer") or {}).get("name", "Не указано").strip()
            location = (item.get("area") or {}).get("name")
            canonical_url = item.get("alternate_url", f"https://hh.ru/vacancy/{hh_id}")
            salary_from, salary_to, currency = salary_info(item)
            published_at = item.get("published_at")

            # Получаем детали вакансии (навыки, описание)
            time.sleep(0.3)
            description = None
            try:
                detail = fetch_vacancy_detail(hh_id)
                skills = extract_skills(detail)
                description = detail.get("description", "") or ""
                import re
                # Remove dangerous tags entirely
                description = re.sub(r"<script[\s\S]*?</script>", "", description, flags=re.IGNORECASE)
                description = re.sub(r"<iframe[\s\S]*?</iframe>", "", description, flags=re.IGNORECASE)
                description = re.sub(r"<style[\s\S]*?</style>", "", description, flags=re.IGNORECASE)
                # Strip inline style and class attributes (they override our CSS)
                description = re.sub(r'\s+style="[^"]*"', "", description, flags=re.IGNORECASE)
                description = re.sub(r"\s+style='[^']*'", "", description, flags=re.IGNORECASE)
                description = re.sub(r'\s+class="[^"]*"', "", description, flags=re.IGNORECASE)
                description = re.sub(r"\s+class='[^']*'", "", description, flags=re.IGNORECASE)
                # Remove empty paragraphs and divs left after stripping
                description = re.sub(r"<(p|div)[^>]*>\s*</\1>", "", description, flags=re.IGNORECASE)
                # Replace non-breaking spaces
                description = description.replace("&nbsp;", " ")
                # Collapse multiple blank lines
                description = re.sub(r"(\s*<br\s*/?>){3,}", "<br><br>", description, flags=re.IGNORECASE)
                # Open all links in new tab
                description = re.sub(r"<a\s", '<a target="_blank" rel="noopener noreferrer" ', description, flags=re.IGNORECASE)
                description = description.strip()[:8000]
            except Exception as e:
                print(f"  ⚠ Не удалось получить детали {hh_id}: {e}")
                skills = []
                description = None

            seniority = detect_seniority(title, description)

            vacancy_data = {
                "source_id": source_id,
                "external_id": f"hh_{hh_id}",
                "title": title[:300],
                "company": company[:300],
                "canonical_url": canonical_url,
                "location": location,
                "salary_from": salary_from,
                "salary_to": salary_to,
                "salary_currency": currency,
                "seniority": seniority,
                "employment_type": None,
                "work_format": [],
                "description": description,
                "skills": skills,
                "status": "active",
                "published_at": published_at,
                "source_name": "hh",
            }

            ok = post_canonical(vacancy_data)
            if ok:
                loaded += 1
                print(f"  [{loaded}/{TARGET_COUNT}] ✓ {title[:60]} @ {company[:30]}")

            time.sleep(0.2)

        page += 1
        time.sleep(1.0)

    print(f"\n[hh-seed] Готово! Загружено вакансий: {loaded}")


if __name__ == "__main__":
    run()
