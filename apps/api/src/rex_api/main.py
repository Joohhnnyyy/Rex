import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rex_api.connections import router as connections_router
from rex_api.discover import background_loop
from rex_api.discover import router as discover_router
from rex_api.livekit_tokens import router as livekit_router
from rex_api.memory import router as memory_router
from rex_api.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        task = asyncio.create_task(background_loop()) if settings.discover_in_background else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title="Rex API", version="0.1.0", lifespan=lifespan)
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
    app.include_router(connections_router)
    app.include_router(memory_router)
    app.include_router(discover_router)
    return app


# The real server researches in the background; apps built in tests don't.
app = create_app(Settings(discover_in_background=True))
