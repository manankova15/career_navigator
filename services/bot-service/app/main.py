"""
bot-service entry point.

Runs aiogram in either:
  - polling mode  (BOT_MODE=polling, default for dev)
  - webhook mode  (BOT_MODE=webhook, for prod behind HTTPS)

A minimal FastAPI app is co-hosted to expose /health and /ready endpoints
for Docker health checks and the compose depends_on condition.
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings
from .handlers.assessments import router as assessments_router
from .handlers.common import router as common_router
from .handlers.profile import router as profile_router
from .handlers.recommendations import router as recommendations_router
from .handlers.vacancies import router as vacancies_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Aiogram setup ─────────────────────────────────────────────────────────────

bot = Bot(
    token=settings.telegram_bot_token or "0:placeholder",
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(common_router)
dp.include_router(profile_router)
dp.include_router(vacancies_router)
dp.include_router(recommendations_router)
dp.include_router(assessments_router)

# ── FastAPI app (health checks + optional webhook endpoint) ───────────────────

fastapi_app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    docs_url="/docs",
)


@fastapi_app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@fastapi_app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@fastapi_app.get("/ready", tags=["meta"])
async def ready():
    bot_ok = bool(settings.telegram_bot_token)
    return {
        "status": "ready" if bot_ok else "degraded",
        "telegram_configured": bot_ok,
        "mode": settings.bot_mode,
    }


@fastapi_app.get("/commands", tags=["meta"])
async def commands():
    return {
        "commands": ["/start", "/menu", "/help", "/logout", "/profile",
                     "/vacancies", "/recommendations", "/skillgap",
                     "/assessments", "/notifications"],
    }


# Webhook endpoint — Telegram sends updates here in webhook mode
@fastapi_app.post(settings.webhook_path)
async def telegram_webhook(request: Request) -> Response:
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response()


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def _start_polling() -> None:
    logger.info("[bot-service] Starting in polling mode")
    # Сброс webhook — иначе polling не получает апдейты
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def _setup_webhook() -> None:
    url = f"{settings.webhook_base_url}{settings.webhook_path}"
    logger.info("[bot-service] Setting webhook: %s", url)
    await bot.set_webhook(url)


async def _on_startup() -> None:
    # Webhook только при BOT_MODE=webhook и непустом webhook_base_url
    if settings.bot_mode.strip().lower() == "webhook" and settings.webhook_base_url:
        await _setup_webhook()
    else:
        # Иначе polling (в т.ч. если в .env остался плейсхолдер ${BOT_MODE:-polling})
        asyncio.create_task(_start_polling())


@fastapi_app.on_event("startup")
async def startup():
    if settings.telegram_bot_token:
        logger.info("[bot-service] TELEGRAM_BOT_TOKEN is set (len=%d), mode=%s", len(settings.telegram_bot_token), settings.bot_mode)
        await _on_startup()
    else:
        logger.warning("[bot-service] TELEGRAM_BOT_TOKEN not set – bot will NOT respond to Telegram. Set TELEGRAM_BOT_TOKEN in .env and restart.")


@fastapi_app.on_event("shutdown")
async def shutdown():
    await bot.session.close()


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "app.main:fastapi_app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
    )
