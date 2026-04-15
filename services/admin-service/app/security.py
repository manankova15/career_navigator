from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

bearer_scheme = HTTPBearer()


def _decode(token: str) -> dict:
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


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Return the full token payload – only for admin/superadmin roles."""
    payload = _decode(credentials.credentials)
    roles: list[str] = payload.get("roles", [])
    if not any(r in roles for r in ("admin", "superadmin")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return payload


def get_actor_id(payload: dict = Depends(require_admin)) -> UUID:
    return UUID(payload["sub"])


def get_forward_authorization(request: Request) -> str:
    """Authorization: Bearer … от админского клиента — проксируется в доменные сервисы."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )
    return auth
