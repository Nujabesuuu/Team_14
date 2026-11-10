from collections.abc import AsyncIterator

from sqlalchemy import Connection, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    # In-memory SQLite must share one connection or every session sees an empty DB.
    if url.endswith(":memory:") or url == "sqlite+aiosqlite://":
        return {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    return {}


settings = get_settings()
engine = create_async_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def _missing_columns(sync_conn: Connection) -> list[str]:
    inspector = inspect(sync_conn)
    missing = []
    for table in Base.metadata.sorted_tables:
        existing = {column["name"] for column in inspector.get_columns(table.name)}
        missing += [f"{table.name}.{column.name}" for column in table.columns if column.name not in existing]
    return missing


async def create_all() -> None:
    # Import models so they register on Base.metadata before create_all.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all adds new tables but never alters existing ones. Without migrations (ADR-0007)
        # an older local database would fail later with an obscure "no such column", so fail here instead.
        missing = await conn.run_sync(_missing_columns)
    if missing:
        raise RuntimeError(
            f"The database is older than the code (missing: {', '.join(missing)}). "
            "Recreate it: `python dev.py --fresh`, or `docker compose down -v` for the Docker setup."
        )
