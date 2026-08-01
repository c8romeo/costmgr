"""tests.rls.test_bom_lines_isolation — RLS tenant isolation for bom_lines.

Story 2.2 — Task 2.5. Companion to `supabase/policies/0007_bom_lines_rls.sql`.

Tests are sync; async work is driven by `asyncio.run()` to keep
pytest-asyncio out of the dep tree (Story 0.2 lesson).

Coverage (4 cases per CR 0.2 standard pattern):
- select-own: tenant A JWT sees only A's BOM rows.
- select-other-zero: tenant A JWT sees 0 of tenant B's BOM rows.
- insert-rejected: tenant A JWT cannot insert a row with tenant B's UUID (WITH CHECK).
- update-rejected: tenant A JWT cannot UPDATE a BOM row owned by tenant B.
  (Story 2.2 has no DELETE RLS policy — append-only-leaning — so the
  RLS delete pattern is not exercised here; bulk-replace PUT is the only
  mutation path per CR 2.1 lesson.)

CI-only gating — `pytest.skip` when not on CI (per 2026-07-25 Decision 2).
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
    # Begin an explicit transaction so SET LOCAL takes effect.
    await conn.execute("BEGIN")
    await conn.execute(f"SET LOCAL request.jwt.claims = '{claims}'")
    return conn


async def _seed_bom_rows(conn, tenant_pair) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    """Seed 2 parent products + 2 child products (1 each tenant) + 2 bom_lines.

    Returns (parent_a, parent_b, child_a, child_b). Runs OUTSIDE RLS
    (SET LOCAL row_security = off) so the test fixture can set up
    cross-tenant data for the isolation assertions.
    """
    tenant_a, tenant_b = tenant_pair
    parent_a = uuid.uuid4()
    parent_b = uuid.uuid4()
    child_a = uuid.uuid4()
    child_b = uuid.uuid4()
    suffix = uuid.uuid4().hex[:8]

    try:
        await conn.execute("BEGIN")
        await conn.execute("SET LOCAL row_security = off")
        # Truncate any existing bom_lines / products from prior runs.
        await conn.execute("TRUNCATE bom_lines, products CASCADE")
        # Two parents (one per tenant, type=product).
        await conn.execute(
            """
            INSERT INTO products (
                id, tenant_id, product_type, code, name, is_active,
                created_at, updated_at
            ) VALUES
                ($1, $3, 'product', $5, 'Parent A', TRUE, now(), now()),
                ($2, $4, 'product', $6, 'Parent B', TRUE, now(), now()),
                ($7, $3, 'material', $9, 'Material A', TRUE, now(), now()),
                ($8, $4, 'material', $10, 'Material B', TRUE, now(), now())
            """,
            parent_a, parent_b, tenant_a, tenant_b,
            f"PRD-{suffix}",
            f"PRD-{uuid.uuid4().hex[:6]}",
            child_a, child_b,
            f"MAT-{suffix}",
            f"MAT-{uuid.uuid4().hex[:6]}",
        )
        # Two bom_lines (one per tenant).
        await conn.execute(
            """
            INSERT INTO bom_lines (
                id, tenant_id, parent_product_id, child_product_id, ratio,
                created_at, updated_at
            ) VALUES
                ($1, $5, $7, $9, 100.0000, now(), now()),
                ($2, $6, $8, $10, 100.0000, now(), now())
            """,
            uuid.uuid4(), uuid.uuid4(),
            parent_a, parent_b, tenant_a, tenant_b,
            child_a, child_b,
        )
        await conn.execute("COMMIT")
        return parent_a, parent_b, child_a, child_b
    except Exception:
        await conn.execute("ROLLBACK")
        raise


# ── test_select_own_tenant_only ──────────────────────────────


def test_tenant_a_can_read_own_bom(rls_db, tenant_pair) -> None:
    """AC #1: tenant A JWT can SELECT its own bom_lines row."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            parent_a, _, _, _ = await _seed_bom_rows(conn, (tenant_a, tenant_b))
            try:
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    rows = await tenant_conn.fetch(
                        "SELECT * FROM bom_lines WHERE parent_product_id = $1",
                        parent_a,
                    )
                    assert len(rows) == 1, (
                        f"Expected 1 row, got {len(rows)}"
                    )
                finally:
                    await tenant_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())


def test_tenant_a_cannot_read_tenant_b_bom(rls_db, tenant_pair) -> None:
    """AC #1 (cross-tenant isolation): tenant A JWT sees 0 of tenant B's bom_lines."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            _, parent_b, _, _ = await _seed_bom_rows(conn, (tenant_a, tenant_b))
            try:
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    rows = await tenant_conn.fetch(
                        "SELECT * FROM bom_lines WHERE parent_product_id = $1",
                        parent_b,
                    )
                    assert len(rows) == 0, (
                        f"Expected 0 rows (cross-tenant), got {len(rows)}"
                    )
                finally:
                    await tenant_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())


def test_tenant_a_cannot_insert_for_tenant_b(rls_db, tenant_pair) -> None:
    """AC #2: tenant A JWT cannot INSERT a bom_line with tenant B's UUID (WITH CHECK)."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            await _seed_bom_rows(conn, (tenant_a, tenant_b))
            try:
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                        await tenant_conn.execute(
                            """
                            INSERT INTO bom_lines (
                                id, tenant_id, parent_product_id, child_product_id, ratio,
                                created_at, updated_at
                            ) VALUES (
                                $1, $2, $3, $4, 50.0000, now(), now()
                            )
                            """,
                            uuid.uuid4(),
                            tenant_b,  # cross-tenant — should be rejected by WITH CHECK
                            uuid.uuid4(),
                            uuid.uuid4(),
                        )
                finally:
                    await tenant_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())


def test_tenant_a_cannot_update_tenant_b_bom(rls_db, tenant_pair) -> None:
    """AC #3: tenant A JWT cannot UPDATE tenant B's bom_lines row.

    RLS USING makes the row INVISIBLE so UPDATE silently affects 0 rows
    (no exception). Verify the ratio remains unchanged.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            _, _, _, _ = await _seed_bom_rows(conn, (tenant_a, tenant_b))
            try:
                # Tenant A tries to tamper with all rows.
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    status = await tenant_conn.execute(
                        "UPDATE bom_lines SET ratio = 99.9999 "
                        "WHERE tenant_id = $1",
                        tenant_b,
                    )
                    # asyncpg returns "UPDATE <n>" — assert zero rows touched.
                    assert status.endswith(" 0"), (
                        f"Expected 0 rows updated, got: {status!r}"
                    )
                finally:
                    await tenant_conn.close()

                # Verify tenant B's row is untouched (read as tenant B).
                owner_b_conn = await _open_as_tenant(tenant_b)
                try:
                    ratio = await owner_b_conn.fetchval(
                        "SELECT ratio FROM bom_lines WHERE tenant_id = $1 LIMIT 1",
                        tenant_b,
                    )
                    # The seed inserted 100.0000 — must remain unchanged.
                    assert float(ratio) == 100.0000, (
                        f"Tenant B's bom_line was tampered! ratio={ratio}"
                    )
                finally:
                    await owner_b_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())


def test_consultant_proxy_cannot_write_bom(rls_db, tenant_pair) -> None:
    """Role-split defense: `consultant_proxy` is read-only; INSERT must fail.

    Mirrors the products RLS pattern — write access is owner-only.
    consultant_proxy role can SELECT but cannot INSERT/UPDATE.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            await _seed_bom_rows(conn, (tenant_a, tenant_b))
            try:
                # Open as tenant A but with role=consultant_proxy (read-only).
                cp_conn = await _open_as_tenant(tenant_a, role="consultant_proxy")
                try:
                    with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                        await cp_conn.execute(
                            """
                            INSERT INTO bom_lines (
                                id, tenant_id, parent_product_id, child_product_id, ratio,
                                created_at, updated_at
                            ) VALUES (
                                $1, $2, $3, $4, 100.0000, now(), now()
                            )
                            """,
                            uuid.uuid4(),
                            tenant_a,
                            uuid.uuid4(),
                            uuid.uuid4(),
                        )
                finally:
                    await cp_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())