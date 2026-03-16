"""
Simple internal-token guard for ml-service.
Only recommendation-service (and admins) should call scoring endpoints.
"""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_header = APIKeyHeader(name="X-Internal-Token", auto_error=False)

INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "change_me_internal_token")


def require_internal(token: str | None = Security(_header)) -> None:
    if not token or token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid X-Internal-Token header required",
        )
