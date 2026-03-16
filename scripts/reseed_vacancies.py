#!/usr/bin/env python3
"""
Удаляет все вакансии из БД и заново загружает 500 с HH.ru и 500 из Telegram-канала.

Запуск (из корня проекта, при работающих сервисах):
  python scripts/reseed_vacancies.py

Или по шагам:
  python scripts/reseed_vacancies.py --truncate-only   # только очистка
  HH_TARGET_COUNT=100 TELEGRAM_TARGET_COUNT=100 python scripts/reseed_vacancies.py  # другое кол-во
"""

import os
import sys

# Подгружаем .env до импорта сидеров
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

import requests

VACANCY_SERVICE_URL = os.getenv("VACANCY_SERVICE_URL", "http://localhost:8004")
JWT_SECRET = os.getenv("JWT_SECRET", "my_super_secret_jwt_key_change_in_prod")


def make_admin_jwt() -> str:
    import base64 as b64
    import hashlib
    import hmac
    import json
    import time as _time

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
        hmac.new(JWT_SECRET.encode(), sig_input, hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


def truncate_vacancies() -> bool:
    url = f"{VACANCY_SERVICE_URL}/internal/truncate"
    headers = {"Authorization": f"Bearer {make_admin_jwt()}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        print(f"[reseed] Очищено: raw={data.get('raw_deleted', 0)}, canonical={data.get('canonical_deleted', 0)}")
        return True
    except Exception as e:
        print(f"[reseed] Ошибка очистки: {e}")
        return False


def main():
    import subprocess

    script_dir = os.path.dirname(os.path.abspath(__file__))
    truncate_only = "--truncate-only" in sys.argv
    if truncate_only:
        ok = truncate_vacancies()
        sys.exit(0 if ok else 1)

    print("[reseed] 1/3 Очистка старых вакансий…")
    if not truncate_vacancies():
        sys.exit(1)

    print("\n[reseed] 2/3 Загрузка вакансий с HH.ru…")
    rc = subprocess.run(
        [sys.executable, os.path.join(script_dir, "seed_hh_vacancies.py")],
        env=os.environ,
        cwd=os.path.dirname(script_dir),
    )
    if rc.returncode != 0:
        sys.exit(rc.returncode)

    print("\n[reseed] 3/3 Загрузка вакансий из Telegram-канала…")
    rc = subprocess.run(
        [sys.executable, os.path.join(script_dir, "seed_telegram_vacancies.py")],
        env=os.environ,
        cwd=os.path.dirname(script_dir),
    )
    if rc.returncode != 0:
        sys.exit(rc.returncode)

    print("\n[reseed] Готово.")


if __name__ == "__main__":
    main()
