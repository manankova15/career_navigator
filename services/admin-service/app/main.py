from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .routers.assessments import router as assessments_router
from .routers.audit import router as audit_router
from .routers.ingestion_runs import router as ingestion_runs_router
from .routers.sources import router as sources_router
from .routers.stats import router as stats_router
from .routers.users import router as users_router
from .routers.vacancies import router as vacancies_router

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Admin service: audit-logged management of vacancies, sources, "
        "assessments and users. Proxies admin actions to domain services "
        "using the internal service token."
    ),
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

app.include_router(audit_router)
app.include_router(stats_router)
app.include_router(vacancies_router)
app.include_router(sources_router)
app.include_router(assessments_router)
app.include_router(ingestion_runs_router)
app.include_router(users_router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name, "version": settings.version}


@app.get("/admin/capabilities", tags=["meta"])
async def capabilities():
    return {
        "actions": [
            "audit_log_search",
            "vacancy_moderate",
            "source_sync_trigger",
            "assessment_publish",
            "user_list",
            "user_notify",
        ]
    }
