from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .routers.recommendations import router as rec_router
from .scheduler_jobs import run_hourly_recommendation_refresh

scheduler = BackgroundScheduler()


def _scheduled_refresh_job() -> None:
    from .database import SessionLocal

    db = SessionLocal()
    try:
        run_hourly_recommendation_refresh(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.enable_scheduled_refresh:
        scheduler.add_job(
            _scheduled_refresh_job,
            "interval",
            hours=float(settings.refresh_interval_hours),
            id="hourly_rec_refresh",
            replace_existing=True,
        )
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Orchestrates content-based vacancy recommendations (Phase 1). "
        "Fetches profile, candidates, calls ml-service, persists results."
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

app.include_router(rec_router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name, "version": settings.version}
