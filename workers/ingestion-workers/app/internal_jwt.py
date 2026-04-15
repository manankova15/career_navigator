"""Краткоживущий JWT с ролью admin для вызовов vacancy-service /internal/*."""

from datetime import datetime, timedelta
from uuid import uuid4

from jose import jwt

from .config import settings


def make_admin_access_token() -> str:
    payload = {
        "sub": str(uuid4()),
        "roles": ["admin", "superadmin"],
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(
        payload, settings.internal_jwt_secret, algorithm=settings.internal_jwt_algorithm
    )
