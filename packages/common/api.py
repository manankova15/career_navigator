from fastapi import APIRouter


def build_meta_router(service_name: str, version: str = "0.1.0") -> APIRouter:
    router = APIRouter()

    @router.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": service_name, "version": version}

    @router.get("/ready", tags=["meta"])
    async def ready() -> dict[str, str]:
        return {"status": "ready", "service": service_name, "version": version}

    return router
