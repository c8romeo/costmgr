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

from apps.api.core.settings import get_settings


@lru_cache(maxsize=1)
def _create_engine(database_url: str) -> AsyncEngine:
    """Create the async engine. Cached at process level (keyed by URL).

    The URL is the only thing that matters for engine identity — the full
    `Settings` object is unhashable (Pydantic v2), so the cache is keyed on
    the string URL instead. `get_settings()` is itself already cached, so
    the lookup is cheap.
    """
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set — Story 0.2 requires a database connection. "
            "Copy apps/api/.env.example to apps/api/.env and set DATABASE_URL."
        )
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        echo=False,
        future=True,
    )


def get_engine() -> AsyncEngine:
    """FastAPI dependency — returns the cached async engine."""
    return _create_engine(get_settings().database_url)


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

    Auto-commits on successful request scope end; auto-rollbacks on
    unhandled exception. Handlers may also call `await session.commit()`
    explicitly — calling it again at dep-end is a no-op when the session
    is already clean.

    Walking Skeleton (2026-08-16): prior implementation only yielded the
    session without committing. Every `service.foo()` that flushed but
    never committed was being rolled back when the session closed — this
    silently broke m0_onboarding write handlers (update_industry /
    save_fiscal_year_start / save_currency / save_language /
    save_allocation_criteria) and any other handler that relied on the
    dep to commit. Now the dep commits on success and rollbacks on
    exception.
    """
    session_local = _sessionmaker()
    async with session_local() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
