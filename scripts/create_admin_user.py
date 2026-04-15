#!/usr/bin/env python3
"""
Создать (или повысить до admin) учётную запись администратора в auth-service БД.

Запуск из корня репозитория career_nagigator (рядом с compose.yaml):

  PYTHONPATH=services/auth-service python scripts/create_admin_user.py \\
    --email admin@example.com --password 'SecurePass123' --full-name 'Админ'

Если email уже зарегистрирован — добавляется только роль admin.
"""
from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", help="Required for new users (min 8 chars)")
    parser.add_argument("--full-name", default="Administrator", dest="full_name")
    args = parser.parse_args()

    if "DATABASE_URL" not in os.environ:
        os.environ.setdefault(
            "DATABASE_URL",
            "postgresql://career_navigator:change_me@localhost:5432/career_navigator",
        )

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auth_pkg = os.path.join(root, "services", "auth-service")
    if auth_pkg not in sys.path:
        sys.path.insert(0, auth_pkg)

    from sqlalchemy.orm import Session

    from app.crud import assign_admin_role_by_email, create_admin_user
    from app.database import SessionLocal

    db: Session = SessionLocal()
    try:
        existing = assign_admin_role_by_email(db, args.email)
        if existing:
            print(f"OK: role admin assigned to existing user {args.email}")
            return
        if not args.password:
            print("Error: --password required for new user", file=sys.stderr)
            sys.exit(1)
        if len(args.password) < 8:
            print("Error: password must be at least 8 characters", file=sys.stderr)
            sys.exit(1)
        user = create_admin_user(db, args.full_name, args.email, args.password)
        print(f"OK: admin user created id={user.id} email={args.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
