from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .routers.ml import router as ml_router

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Stateless ML computation service. "
        "Content-based AHP-weighted scoring and skill-gap analysis. "
        "No pretrained model, no external training data."
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


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
async def health():
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
        "algorithm": settings.algorithm_name,
        "weights": {
            "skills": settings.weight_skills,
            "specialization": settings.weight_specialization,
            "category": settings.weight_category,
            "seniority": settings.weight_seniority,
            "salary": settings.weight_salary,
            "location": settings.weight_location,
            "format": settings.weight_format,
        },
        "behavior": {
            "trust_n0": settings.behavior_trust_n0,
            "alpha_category": settings.behavior_alpha_category,
            "alpha_specialization": settings.behavior_alpha_specialization,
            "alpha_skills": settings.behavior_alpha_skills,
            "alpha_title": settings.behavior_alpha_title,
            "time_decay_half_life_days": settings.time_decay_half_life_days,
        },
    }


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name}
