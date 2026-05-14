"""
API Gateway / BFF.

Routes:
  /api/auth/*           → auth-service
  /api/profiles/*       → profile-service
  /api/sources/*        → source-service
  /api/vacancies/*      → vacancy-service
  /api/recommendations/*→ recommendation-service
  /api/assessments/*    → assessment-service
  /api/attempts/*       → assessment-service
  /api/notifications/*  → notification-service
  /api/analytics/*      → analytics-service
  /api/admin/*          → admin-service
"""
import httpx
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .proxy import forward
from .rate_limiter import check_rate_limit

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description="Single entry point for the Career Navigator frontend. Proxies to domain services with rate limiting.",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route table: (prefix_to_strip, upstream_base) ────────────────────────────
_ROUTES: list[tuple[str, str]] = [
    ("/api/auth",            settings.auth_service_url),
    ("/api/profiles",        settings.profile_service_url),
    ("/api/sources",         settings.source_service_url),
    ("/api/vacancies",       settings.vacancy_service_url),
    ("/api/recommendations", settings.recommendation_service_url),
    ("/api/assessments",     settings.assessment_service_url),
    ("/api/attempts",        settings.assessment_service_url),
    ("/api/notifications",   settings.notification_service_url),
    ("/api/analytics",       settings.analytics_service_url),
    ("/api/admin",           settings.admin_service_url),
]


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Health probes must remain available under load: they are used by Docker,
    # monitoring and load tests to distinguish app failures from limiter policy.
    if request.url.path in {"/health", "/ready"}:
        return await call_next(request)

    # Use Authorization token as key for authenticated requests so that each
    # user gets their own bucket (important when all traffic arrives from the
    # same Podman/Docker host IP). Public read-only endpoints intentionally get
    # a wider shared bucket: otherwise a local load test from one IP measures
    # only the gateway limiter, not downstream service throughput.
    auth_header = request.headers.get("authorization", "")
    limit = settings.rate_limit_requests
    if auth_header.startswith("Bearer "):
        # Use last 32 chars of token as key — unique per user session.
        # Load tests may intentionally reuse one test account, so keep the
        # authenticated bucket wider than the base per-IP protection.
        client_key = "user:" + auth_header[-32:]
        limit *= settings.rate_limit_auth_multiplier
    else:
        client_key = "ip:" + (request.client.host if request.client else "unknown")
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            limit *= settings.rate_limit_public_multiplier
        elif request.url.path.startswith("/api/auth/"):
            limit *= settings.rate_limit_auth_multiplier

    if not check_rate_limit(client_key, limit=limit):
        return Response(
            content='{"detail":"Rate limit exceeded. Try again later."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
        )
    return await call_next(request)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def gateway(path: str, request: Request) -> Response:
    """Catch-all route: match prefix and proxy to upstream.

    We strip only the leading '/api' from the path so that the downstream
    service prefix is preserved (e.g. /api/auth/login → /auth/login).
    """
    full_path = f"/api/{path}"
    for prefix, upstream in _ROUTES:
        if full_path.startswith(prefix):
            try:
                # Strip only "/api", keep the service-level prefix intact
                return await forward(request, upstream, strip_prefix="/api")
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Upstream service unavailable: {exc}",
                )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")


# ── Health aggregation ────────────────────────────────────────────────────────

_ALL_SERVICES = {
    "auth": settings.auth_service_url,
    "profile": settings.profile_service_url,
    "source": settings.source_service_url,
    "vacancy": settings.vacancy_service_url,
    "recommendation": settings.recommendation_service_url,
    "assessment": settings.assessment_service_url,
    "notification": settings.notification_service_url,
    "analytics": settings.analytics_service_url,
    "admin": settings.admin_service_url,
}


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/health/all", tags=["meta"])
async def health_all():
    """Aggregate health check — pings all downstream services."""
    results: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
        for name, base in _ALL_SERVICES.items():
            try:
                resp = await client.get(f"{base}/health")
                results[name] = "ok" if resp.status_code == 200 else f"degraded ({resp.status_code})"
            except Exception:
                results[name] = "unreachable"

    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return {"status": overall, "services": results}


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name, "version": settings.version}


@app.get("/catalog", tags=["meta"])
async def catalog():
    return {"routes": [{"prefix": p, "upstream": u} for p, u in _ROUTES]}
