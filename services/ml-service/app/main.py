from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .ranking.model_loader import load_ranker
from .routers.ml import router as ml_router
from .training.trainer import ensure_trained_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_trained_model(settings.model_dir)
    app.state.rank_booster = load_ranker(settings.model_dir)
    yield
    app.state.rank_booster = None


app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Stateless ML computation service. "
        "Content-based scoring, hybrid LightGBM ranking, skill-gap analysis."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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
        "algorithm": "hybrid_lgb_v1",
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
