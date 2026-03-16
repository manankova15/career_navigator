from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from .config import settings

bearer_scheme = HTTPBearer(auto_error=False)

def _decode(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Not an access token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> UUID:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UUID(_decode(credentials.credentials)["sub"])

def require_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> UUID:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = _decode(credentials.credentials)
    if not any(r in payload.get("roles", []) for r in ("admin", "superadmin")):
        raise HTTPException(status_code=403, detail="Admin role required")
    return UUID(payload["sub"])

def require_internal_or_service(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    x_internal_token: str | None = Header(None, alias="X-Internal-Token"),
) -> None:
    if x_internal_token == settings.internal_token:
        return
    if credentials:
        _decode(credentials.credentials)
        return
    raise HTTPException(status_code=401, detail="Authentication required")
