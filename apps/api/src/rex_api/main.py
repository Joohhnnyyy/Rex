from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rex_api.livekit_tokens import router as livekit_router
from rex_api.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
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

    app.include_router(livekit_router)
    return app


app = create_app()
