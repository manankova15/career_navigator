from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.ml import router as ml_router

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Stateless ML computation service. "
        "Phase 1: content-based scoring and skill-gap analysis."
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

app.include_router(ml_router)


@app.get("/health", tags=["meta"])
async def health():
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
        "algorithm": "content_v1",
        "weights": {
            "skills": settings.weight_skills,
            "location": settings.weight_location,
            "salary": settings.weight_salary,
            "seniority": settings.weight_seniority,
        },
    }


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name}
