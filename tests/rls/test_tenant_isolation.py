"""tests/rls/test_tenant_isolation.py — verifies RLS policies reject cross-tenant access.

Story 0.2 — Task 8.3. Per Decision 2 (Docker CI-only): these tests are
gated by the `rls_enabled` fixture (skipped unless CI=true or RLS_RUN_LOCAL=1).

Tests are sync; async work is driven by `asyncio.run()` to keep
pytest-asyncio out of the dep tree.

RLS-CI fixes applied (2026-07-25):
- RLS-CI-4: connect as `costmgr_test` (NOBYPASSRLS) instead of postgres superuser
- RLS-CI-5: wrap `SET LOCAL` in an explicit `conn.transaction()` block
- RLS-CI-6: UPDATE/DELETE on invisible rows return 0 rows affected, not an
  exception — assert on the command tag, not on raising
"""

from __future__ import annotations

import asyncio
import json
import uuid

import asyncpg
import pytest

# CI shim creates `costmgr_test` with password `costmgr_test` and
# NOSUPERUSER + NOBYPASSRLS so RLS actually filters rows.
DSN = "postgresql://costmgr_test:costmgr_test@localhost:54322/postgres"


def _jwt_claims(tenant_id: uuid.UUID, role: str = "owner") -> str:
    return json.dumps(
        {
            "sub": str(uuid.uuid4()),
            "app_metadata": {"tenant_id": str(tenant_id), "role": role},
        }
    )


async def _open_as_tenant(tenant_id: uuid.UUID, role: str = "owner") -> asyncpg.Connection:
    """Open a NEW connection (as costmgr_test) and simulate a tenant JWT
    via `SET LOCAL request.jwt.claims`. The transaction wrapping makes
    `SET LOCAL` durable for the duration of the connection.
    """
    conn = await asyncpg.connect(DSN)
    claims = _jwt_claims(tenant_id, role)
    # Begin an explicit transaction so SET LOCAL takes effect (asyncpg
    # autocommit is ON by default — without a tx, SET LOCAL is no-op).
    await conn.execute("BEGIN")
    await conn.execute(f"SET LOCAL request.jwt.claims = '{claims}'")
    return conn


# ── test_select_own_tenant_only ────────────────────────────


def test_select_own_tenant_only(rls_db, tenant_pair) -> None:
    """AC #5a: tenant A's JWT sees only A's row in tenant_settings."""

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            tenant_conn = await _open_as_tenant(tenant_a)
            try:
                # Spec uses count(*) — assert exactly 1 row visible.
                count = await tenant_conn.fetchval(
                    "SELECT count(*) FROM tenant_settings"
                )
                assert count == 1, f"Expected 1 row, got {count}"
            finally:
                await tenant_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_select_other_tenant_returns_zero(rls_db, tenant_pair) -> None:
    """AC #5b: tenant A's JWT cannot see tenant B's users."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            tenant_conn = await _open_as_tenant(tenant_a)
            try:
                rows = await tenant_conn.fetch(
                    "SELECT * FROM users WHERE tenant_id = $1", tenant_b
                )
                assert len(rows) == 0, f"Expected 0 rows, got {len(rows)}"
            finally:
                await tenant_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_other_tenant_rejected(rls_db, tenant_pair) -> None:
    """AC #5c: tenant A cannot INSERT a user with tenant B's UUID (WITH CHECK)."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            tenant_conn = await _open_as_tenant(tenant_a)
            try:
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await tenant_conn.execute(
                        """
                        INSERT INTO users (id, tenant_id, email, role)
                        VALUES ($1, $2, 'evil@example.com', 'owner')
                        """,
                        uuid.uuid4(), tenant_b,
                    )
            finally:
                await tenant_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_update_other_tenant_rejected(rls_db, tenant_pair) -> None:
    """AC #5d: tenant A cannot UPDATE a row owned by tenant B.

    RLS USING makes the row INVISIBLE, so the UPDATE silently affects
    0 rows (no exception). Verify the target data remains unchanged.
    """
    new_payload = '{"tampered": true}'

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            tenant_conn = await _open_as_tenant(tenant_a)
            try:
                status = await tenant_conn.execute(
                    "UPDATE tenant_settings SET onboarding = $1 "
                    "WHERE tenant_id = $2",
                    new_payload, tenant_b,
                )
                # asyncpg returns "UPDATE <n>" — assert zero rows touched.
                assert status.endswith(" 0"), f"Expected 0 rows updated, got: {status!r}"
            finally:
                await tenant_conn.close()
            # Verify the row is untouched (read as the owner of tenant B).
            owner_b_conn = await _open_as_tenant(tenant_b)
            try:
                onboarding = await owner_b_conn.fetchval(
                    "SELECT onboarding FROM tenant_settings WHERE tenant_id = $1",
                    tenant_b,
                )
                assert onboarding == {}, (
                    f"Expected tenant B's onboarding to remain '{{}}', got {onboarding!r}"
                )
            finally:
                await owner_b_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_delete_other_tenant_rejected(rls_db, tenant_pair) -> None:
    """AC #5e: tenant A cannot DELETE a row owned by tenant B.

    RLS USING makes the row INVISIBLE, so the DELETE silently affects
    0 rows. Verify the row still exists.
    """
    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            tenant_conn = await _open_as_tenant(tenant_a)
            try:
                status = await tenant_conn.execute(
                    "DELETE FROM tenant_settings WHERE tenant_id = $1", tenant_b
                )
                assert status.endswith(" 0"), f"Expected 0 rows deleted, got: {status!r}"
            finally:
                await tenant_conn.close()
            # Verify the row still exists.
            owner_b_conn = await _open_as_tenant(tenant_b)
            try:
                count = await owner_b_conn.fetchval(
                    "SELECT count(*) FROM tenant_settings WHERE tenant_id = $1",
                    tenant_b,
                )
                assert count == 1, f"Tenant B row was deleted! count={count}"
            finally:
                await owner_b_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())
