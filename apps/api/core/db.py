"""apps.api.core.db — async SQLAlchemy 2.0 engine + session.

Story 0.2 — module 3.1. The async engine is created once at process startup
and reused per request via the `get_session()` async generator dependency.

Per AD-1: this module imports only SQLAlchemy + stdlib. No packages.cost_engine
imports (the engine is an INFRASTRUCTURE concern; the engine CORE lives in
`packages.cost_engine.core` and is pure).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.api.core.settings import Settings, get_settings


@lru_cache(maxsize=1)
def _create_engine(settings: Settings) -> AsyncEngine:
    """Create the async engine. Cached at process level."""
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not set — Story 0.2 requires a database connection. "
            "Copy apps/api/.env.example to apps/api/.env and set DATABASE_URL."
        )
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=False,
        future=True,
    )


def get_engine() -> AsyncEngine:
    """FastAPI dependency — returns the cached async engine."""
    return _create_engine(get_settings())


@lru_cache(maxsize=1)
def _sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Sessionmaker cached against the engine."""
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — yields a transactional session.

    Caller is responsible for commit / rollback. The session is closed
    after the request scope ends.
    """
    session_local = _sessionmaker()
    async with session_local() as session:
        yield session
