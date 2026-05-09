from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .routers.assessments import router as assessments_router
from .routers.attempts import router as attempts_router

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Assessment service: bank of quizzes and tasks, attempt submission, "
        "auto-check engine (quiz / multi-select / short-text / case), "
        "per-attempt feedback and weak-skills tracking."
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

app.include_router(assessments_router)
app.include_router(attempts_router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name, "version": settings.version}


@app.get("/supported-modes", tags=["meta"])
async def supported_modes():
    return {
        "modes": ["quiz", "multi-select", "short-text", "case"],
        "future_scope": ["code-task"],
        "scoring": {
            "quiz": "deterministic – full score or zero",
            "multi-select": "partial – proportional to correct selections minus false positives",
            "short-text": "partial – keyword coverage with optional rubric",
            "case": "partial – rubric criterion coverage",
        },
    }
