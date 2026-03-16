from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError, jwt

from .config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UUID:
    """Require valid user JWT, return user_id."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = _decode_token(credentials.credentials)
    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UUID:
    """Require admin role from JWT."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = _decode_token(credentials.credentials)
    roles: list[str] = payload.get("roles", [])
    if not any(r in roles for r in ("admin", "superadmin")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")


def require_internal_or_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    x_internal_token: str | None = Header(None, alias="X-Internal-Token"),
) -> UUID | None:
    """
    Allow dispatch from:
      - internal services using X-Internal-Token header → returns None (no user context)
      - authenticated admin users using Bearer JWT → returns user_id
    This endpoint is meant for service-to-service notification dispatch.
    """
    if x_internal_token:
        if x_internal_token != settings.internal_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal token")
        return None

    if credentials:
        payload = _decode_token(credentials.credentials)
        roles: list[str] = payload.get("roles", [])
        if any(r in roles for r in ("admin", "superadmin")):
            try:
                return UUID(payload["sub"])
            except (KeyError, ValueError):
                pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide X-Internal-Token or admin Bearer token",
    )
