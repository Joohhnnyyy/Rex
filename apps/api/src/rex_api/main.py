import logging
import secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rex_api.auth import router as auth_router
from rex_api.livekit_tokens import router as livekit_router
from rex_api.sessions import router as sessions_router
from rex_api.settings import Settings
from rex_api.timeline import router as timeline_router
from rex_api.tools import router as tools_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if len(settings.session_secret) < 32:
        logging.getLogger("rex.api").warning(
            "SESSION_SECRET missing or shorter than 32 chars; using a random per-process secret"
        )
        settings = settings.model_copy(update={"session_secret": secrets.token_urlsafe(48)})
    app = FastAPI(title="Rex API", version="0.1.0")
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    app.include_router(auth_router)
    app.include_router(livekit_router)
    app.include_router(sessions_router)
    app.include_router(tools_router)
    app.include_router(timeline_router)
    return app


app = create_app()
