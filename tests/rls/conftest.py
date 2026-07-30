"""tests/rls/conftest.py — fixtures for tenant isolation tests.

Per 2026-07-25 decision (Docker CI-only): RLS tests require a Postgres
instance with:
  1. `apps/api/alembic/versions/0001_*.py` applied
  2. `supabase/policies/0000_supabase_ci_shim.sql` applied
  3. `supabase/policies/0001_rls_policies.sql` applied

The `rls_db` fixture is auto-skipped if no Postgres is reachable on
`localhost:54322` (the CI default). CI spins up the stack via the
`rls-tests` GitHub Actions job.

RLS-CI fixes applied (2026-07-25):
- RLS-CI-4: `costmgr_test` role (NOBYPASSRLS) used for RLS connection
- RLS-CI-7: emails are unique per test run (uuid suffix) to avoid
  UNIQUE constraint violations across re-runs

Tests are sync; they call `asyncio.run(...)` on the fixture-provided
coroutine to keep pytest-asyncio out of the dep tree (incompatible with
pytest==9.1.1 per spec).
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import asyncpg
import pytest

# Ensure apps/api is on the Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps"))


def _ci_only() -> bool:
    """CI gate: only run RLS tests when CI=true or RLS_RUN_LOCAL=1."""
    return os.environ.get("CI", "").lower() == "true" or os.environ.get(
        "RLS_RUN_LOCAL", ""
    ) == "1"


def _dsn() -> str:
    """Connection string for the local Postgres / Supabase stack.

    Defaults to `costmgr_test` (NOBYPASSRLS) per RLS-CI-4 — connecting
    as the `postgres` superuser would BYPASSRLS and invalidate every
    isolation assertion.
    """
    return os.environ.get(
        "RLS_TEST_DATABASE_URL",
        "postgresql://costmgr_test:costmgr_test@localhost:54322/postgres",
    )


def _bootstrap_dsn() -> str:
    """DSN for schema migration + policy apply (needs DDL privileges).

    Uses the `postgres` superuser because migration creates roles,
    extensions, and triggers that NOBYPASSRLS roles can't.
    """
    return os.environ.get(
        "RLS_BOOTSTRAP_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:54322/postgres",
    )


def _run(coro):
    """Drive an async coroutine from a sync test body."""
    return asyncio.run(coro)


@pytest.fixture
def rls_enabled() -> bool:
    """Gate fixture: skip everything if RLS tests are not enabled."""
    return _ci_only()


@pytest.fixture
def rls_db(rls_enabled: bool):
    """Sync fixture: returns a coroutine that yields a connected asyncpg.Connection.

    Connects as `costmgr_test` (NOBYPASSRLS) so RLS actually filters rows.
    Usage in tests:
        def test_x(rls_db):
            conn = _run(rls_db())
            try:
                ...
            finally:
                _run(conn.close())
    """
    if not rls_enabled:
        pytest.skip(
            "RLS tests are CI-only (Decision 2, 2026-07-25). "
            "Set CI=true or RLS_RUN_LOCAL=1 to run locally with a Postgres on 54322."
        )

    async def _connect():
        conn = await asyncpg.connect(_dsn())
        tenants_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'tenants')"
        )
        if not tenants_exists:
            await conn.close()
            pytest.skip(
                "Schema not applied. Run: "
                "uv run alembic -c apps/api/alembic.ini upgrade head && "
                "psql $RLS_BOOTSTRAP_DATABASE_URL -f supabase/policies/0000_supabase_ci_shim.sql && "
                "psql $RLS_BOOTSTRAP_DATABASE_URL -f supabase/policies/0001_rls_policies.sql"
            )
        return conn

    return _connect


@pytest.fixture
def tenant_pair(rls_db):
    """Sync fixture: returns a coroutine that seeds 2 tenants + 4 users (2 per tenant) +
    2 tenant_settings rows.

    Returns (tenant_a, tenant_b) UUIDs. Emails use uuid suffix to avoid
    UNIQUE constraint collisions across test runs (RLS-CI-7).

    Spec (AC #5) requires 2 users per tenant. Cleanup is best-effort
    via TRUNCATE before insert; the test database is dedicated to
    RLS testing.
    """
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user_a1 = uuid.uuid4()
    user_a2 = uuid.uuid4()
    user_b1 = uuid.uuid4()
    user_b2 = uuid.uuid4()
    suffix = uuid.uuid4().hex[:8]
    email_a1 = f"a1-{suffix}@example.com"
    email_a2 = f"a2-{suffix}@example.com"
    email_b1 = f"b1-{suffix}@example.com"
    email_b2 = f"b2-{suffix}@example.com"

    async def _seed():
        conn = await rls_db()
        try:
            # Connect as the bootstrap role to insert cross-tenant data
            # (RLS would block otherwise). The tenant_pair fixture
            # intentionally operates outside the RLS context to set up
            # the test environment.
            await conn.execute("BEGIN")
            await conn.execute("SET LOCAL row_security = off")
            # Idempotent: delete any prior rows from previous test runs.
            await conn.execute("TRUNCATE tenants, users, tenant_memberships, tenant_settings, audit_logs CASCADE")
            await conn.execute(
                """
                INSERT INTO tenants (id, name, industry) VALUES
                    ($1, 'Tenant A', 'manufacturing'),
                    ($2, 'Tenant B', 'service')
                """,
                tenant_a, tenant_b,
            )
            await conn.execute(
                """
                INSERT INTO users (id, tenant_id, email, role) VALUES
                    ($1, $5, $7, 'owner'),
                    ($2, $5, $8, 'member'),
                    ($3, $6, $9, 'owner'),
                    ($4, $6, $10, 'member')
                """,
                user_a1, user_a2, user_b1, user_b2,
                tenant_a, tenant_b,
                email_a1, email_a2, email_b1, email_b2,
            )
            await conn.execute(
                """
                INSERT INTO tenant_settings (tenant_id, onboarding, baseline, abc, ai) VALUES
                    ($1, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb),
                    ($2, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb)
                """,
                tenant_a, tenant_b,
            )
            await conn.execute("COMMIT")
            # Re-open the conn in tenant-context mode (BEGIN, SET LOCAL)
            # is the test's job — we just return the IDs.
            return conn, (tenant_a, tenant_b)
        except Exception:
            await conn.execute("ROLLBACK")
            await conn.close()
            raise

    return _seed
