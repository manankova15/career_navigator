from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .routers.profiles import router as profiles_router

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    docs_url="/docs",
    openapi_url="/openapi.json",
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles_router)


@app.on_event("startup")
def _ensure_resume_storage():
    Path(settings.resume_storage_dir).mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name, "version": settings.version}
