"""Alembic env — async-aware migration runner.

Story 0.2 source-of-truth for `supabase/migrations/0001_platform_tenants.sql`
(Table creation). RLS policies live in `supabase/policies/0001_rls_policies.sql`
and must be applied AFTER `alembic upgrade head`.

Per AD-1, AD-11: this module imports only SQLAlchemy + Alembic + stdlib.
It does NOT import packages.cost_engine.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Pull DATABASE_URL from environment if not in alembic.ini.
# Migration uses async engine (postgresql+asyncpg://) — the URL is passed
# through verbatim. `connection.run_sync()` inside `run_migrations_online`
# bridges the async engine to Alembic's sync API.
_db_url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
if not _db_url:
    raise RuntimeError(
        "DATABASE_URL is required (or sqlalchemy.url in alembic.ini). "
        "Set DATABASE_URL=postgresql+asyncpg://... for the async engine."
    )
if _db_url.startswith("postgresql://") and "+asyncpg" not in _db_url:
    # Accept bare postgresql:// but warn — async engine needs the asyncpg driver.
    raise RuntimeError(
        f"DATABASE_URL must use the asyncpg driver for the async engine: "
        f"got {_db_url!r}. Use postgresql+asyncpg://... instead."
    )
config.set_main_option("sqlalchemy.url", _db_url)

# Target metadata — empty for the foundation migration.
# Future migrations will pick up ORM metadata via `target_metadata = Base.metadata`.
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emits SQL to stdout without a DB connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with an existing sync connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode — uses an async engine + sync executor."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
