from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.conversations import (
    router as conversation_router,
)
from app.api.documents import (
    router as document_router,
)
from app.api.tenants import router as tenant_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )

    app.include_router(auth_router)
    app.include_router(tenant_router)
    app.include_router(document_router)
    app.include_router(conversation_router)

    @app.get(
        "/health",
        tags=["system"],
    )
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
        }

    return app


app = create_app()