from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.recommendations import router as rec_router

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Orchestrates content-based vacancy recommendations (Phase 1). "
        "Fetches profile, candidates, calls ml-service, persists results."
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

app.include_router(rec_router)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name, "version": settings.version}
