from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.db import create_all, engine
from app.core.errors import ApiError, install_error_handlers

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_all()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Teamate API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)

    media = Path(settings.media_dir)
    media.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(media)), name="media")

    api = APIRouter(prefix=API_PREFIX)

    @api.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/health/db", tags=["meta"])
    async def health_db() -> dict[str, str]:
        """Walking-skeleton check: the API can open a connection and run a query."""
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise ApiError(503, "DB_UNAVAILABLE", "Database is not reachable") from exc
        return {"status": "ok", "database": engine.dialect.name}

    from app.routers import register_routers

    register_routers(api)
    app.include_router(api)
    return app


app = create_app()
