from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .routers.notifications import router as notifications_router
from .routers.preferences import router as preferences_router

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description=(
        "Notification service: template rendering, "
        "multi-channel dispatch (email via SMTP, Telegram via Bot API, in-app), "
        "delivery tracking, user preferences, retry logic."
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

app.include_router(notifications_router)
app.include_router(preferences_router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/ready", tags=["meta"])
async def ready():
    return {"status": "ready", "service": settings.service_name, "version": settings.version}


@app.get("/channels", tags=["meta"])
async def supported_channels():
    return {
        "channels": ["email", "telegram", "in-app"],
        "email_configured": bool(settings.smtp_host and settings.smtp_from_address),
        "telegram_configured": bool(settings.telegram_bot_token),
    }
