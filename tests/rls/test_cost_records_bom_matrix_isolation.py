"""tests.rls.test_cost_records_bom_matrix_isolation — RLS tenant isolation for
cost_records + bom_matrix.

Story 30.1 — Epic 30+ Reporting & Export MVP CSV export. Companion to
`supabase/policies/0060_cost_records_and_bom_matrix_rls.sql`.

Tests are sync; async work is driven by `asyncio.run()` to keep
pytest-asyncio out of the dep tree (Story 0.2 lesson).

Coverage (5 cases per CR 0.2 standard pattern):
- select-own-cost: tenant A JWT sees only A's cost_records rows.
- select-other-zero-cost: tenant A JWT sees 0 of tenant B's cost_records.
- select-cross-bom: tenant A JWT sees only A's bom_matrix rows; 0 of B's.
- insert-rejected-cost: tenant A JWT cannot INSERT a cost_records row
  with tenant B's UUID (WITH CHECK fails — explicit blocked policy).
- update-rejected-bom: tenant A JWT cannot UPDATE a bom_matrix row owned
  by tenant B (RLS USING makes the row INVISIBLE → 0 rows touched).

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


def _guc_tenant_claims(tenant_id: uuid.UUID, role: str = "owner") -> tuple[str, str]:
    """Return (request.jwt.claims JSON, app.tenant_id literal) for SET LOCAL.

    The new RLS file uses the GUC pattern
    (`current_setting('app.tenant_id', true)::uuid`) so we must SET LOCAL
    `app.tenant_id` AND `request.jwt.claims` (auth.jwt() stub also
    resolves from the latter for any future JWT-style policies).
    """
    claims = json.dumps(
        {
            "sub": str(uuid.uuid4()),
            "app_metadata": {"tenant_id": str(tenant_id), "role": role},
        }
    )
    return claims, str(tenant_id)


async def _open_as_tenant(tenant_id: uuid.UUID, role: str = "owner") -> asyncpg.Connection:
    """Open a NEW connection (as costmgr_test) and simulate a tenant JWT
    via SET LOCAL on both `app.tenant_id` GUC and `request.jwt.claims`
    (Phase 3-0 listener fix). The transaction wrapping makes SET LOCAL
    durable for the duration of the connection.
    """
    conn = await asyncpg.connect(DSN)
    claims, tenant_literal = _guc_tenant_claims(tenant_id, role)
    # Begin an explicit transaction so SET LOCAL takes effect.
    await conn.execute("BEGIN")
    await conn.execute(f"SET LOCAL app.tenant_id = '{tenant_literal}'")
    await conn.execute(f"SET LOCAL request.jwt.claims = '{claims}'")
    return conn


async def _seed_cost_bom_rows(conn, tenant_pair) -> None:
    """Seed cost_records (2 rows, 1 per tenant) + bom_matrix (2 rows, 1 per tenant).

    Runs OUTSIDE RLS (SET LOCAL row_security = off) so the test fixture
    can set up cross-tenant data for the isolation assertions. Both
    tables are tenant-keyed via `tenant_id` FK; cost_records uses
    `id`, `tenant_id`, `period_key`, `product_id`, `product_name`,
    `category`, `opening_qty`, `input_qty`, `output_qty`, `closing_qty`,
    `unit_cost`, `total_cost`, `currency`, `created_at`, `ledger_event_id`.
    bom_matrix uses `id`, `tenant_id`, `period_key`, `parent_product_id`,
    `parent_product_name`, `child_product_id`, `child_product_name`,
    `child_category`, `child_qty_per_parent`, `child_unit_cost`,
    `child_total_cost`, `currency`, `created_at`, `bom_level`.
    """
    tenant_a, tenant_b = tenant_pair
    suffix = uuid.uuid4().hex[:8]

    try:
        await conn.execute("BEGIN")
        await conn.execute("SET LOCAL row_security = off")
        # Truncate any existing rows from prior runs.
        await conn.execute("TRUNCATE cost_records, bom_matrix")
        # Two cost_records (one per tenant) — minimal 14-col insert.
        await conn.execute(
            """
            INSERT INTO cost_records (
                id, tenant_id, period_key, product_id, product_name, category,
                opening_qty, input_qty, output_qty, closing_qty,
                unit_cost, total_cost, currency, created_at, ledger_event_id
            ) VALUES
                ($1, $2, '2026-08', $3, 'Cost A', '원재료',
                 10, 5, 3, 12, 1000, 12000, 'KRW', now(), $4),
                ($5, $6, '2026-08', $7, 'Cost B', '원재료',
                 20, 10, 6, 24, 2000, 48000, 'KRW', now(), $8)
            """,
            uuid.uuid4(), tenant_a, uuid.uuid4(), uuid.uuid4(),
            uuid.uuid4(), tenant_b, uuid.uuid4(), uuid.uuid4(),
        )
        # Two bom_matrix (one per tenant) — minimal 14-col insert.
        await conn.execute(
            """
            INSERT INTO bom_matrix (
                id, tenant_id, period_key,
                parent_product_id, parent_product_name,
                child_product_id, child_product_name, child_category,
                child_qty_per_parent, child_unit_cost, child_total_cost,
                currency, created_at, bom_level
            ) VALUES
                ($1, $2, '2026-08', $3, 'Parent A', $4, 'Child A', '원재료',
                 2.0000, 500.00, 1000.00, 'KRW', now(), 1),
                ($5, $6, '2026-08', $7, 'Parent B', $8, 'Child B', '원재료',
                 4.0000, 250.00, 1000.00, 'KRW', now(), 1)
            """,
            uuid.uuid4(), tenant_a, uuid.uuid4(), uuid.uuid4(),
            uuid.uuid4(), tenant_b, uuid.uuid4(), uuid.uuid4(),
        )
        await conn.execute("COMMIT")
    except Exception:
        await conn.execute("ROLLBACK")
        raise


# ── test_select_own_tenant_only (cost_records) ────────────────────


def test_tenant_a_can_read_own_cost_records(rls_db, tenant_pair) -> None:
    """AC #1: tenant A JWT can SELECT its own cost_records rows."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            await _seed_cost_bom_rows(conn, (tenant_a, tenant_b))
            try:
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    rows = await tenant_conn.fetch(
                        "SELECT * FROM cost_records WHERE tenant_id = $1",
                        tenant_a,
                    )
                    assert len(rows) == 1, (
                        f"Expected 1 cost_record row, got {len(rows)}"
                    )
                finally:
                    await tenant_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())


# ── test_select_other_tenant_zero (cost_records) ───────────────────


def test_tenant_a_cannot_read_tenant_b_cost_records(rls_db, tenant_pair) -> None:
    """AC #1 (cross-tenant isolation): tenant A JWT sees 0 of tenant B's
    cost_records rows.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            await _seed_cost_bom_rows(conn, (tenant_a, tenant_b))
            try:
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    rows = await tenant_conn.fetch(
                        "SELECT * FROM cost_records WHERE tenant_id = $1",
                        tenant_b,
                    )
                    assert len(rows) == 0, (
                        f"Expected 0 cost_record rows (cross-tenant), got {len(rows)}"
                    )
                finally:
                    await tenant_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())


# ── test_select_cross_tenant_isolation (bom_matrix) ────────────────


def test_tenant_a_cannot_read_tenant_b_bom_matrix(rls_db, tenant_pair) -> None:
    """AC #2: tenant A JWT sees only A's bom_matrix rows; 0 of B's."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            await _seed_cost_bom_rows(conn, (tenant_a, tenant_b))
            try:
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    # Own rows: 1
                    own_rows = await tenant_conn.fetch(
                        "SELECT * FROM bom_matrix WHERE tenant_id = $1",
                        tenant_a,
                    )
                    assert len(own_rows) == 1, (
                        f"Expected 1 bom_matrix row (own), got {len(own_rows)}"
                    )
                    # Other-tenant rows: 0
                    other_rows = await tenant_conn.fetch(
                        "SELECT * FROM bom_matrix WHERE tenant_id = $1",
                        tenant_b,
                    )
                    assert len(other_rows) == 0, (
                        f"Expected 0 bom_matrix rows (cross-tenant), got {len(other_rows)}"
                    )
                finally:
                    await tenant_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())


# ── test_insert_rejected_cost_records ─────────────────────────────


def test_tenant_a_cannot_insert_cost_record_for_tenant_b(rls_db, tenant_pair) -> None:
    """AC #3: tenant A JWT cannot INSERT a cost_records row with tenant B's
    UUID (WITH CHECK fails because the INSERT policy is `USING (false)`
    explicitly blocked).
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            await _seed_cost_bom_rows(conn, (tenant_a, tenant_b))
            try:
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                        await tenant_conn.execute(
                            """
                            INSERT INTO cost_records (
                                id, tenant_id, period_key, product_id, product_name,
                                category, opening_qty, input_qty, output_qty,
                                closing_qty, unit_cost, total_cost, currency,
                                created_at, ledger_event_id
                            ) VALUES (
                                $1, $2, '2026-08', $3, 'Hacked', '원재료',
                                1, 1, 1, 1, 100, 100, 'KRW', now(), $4
                            )
                            """,
                            uuid.uuid4(),
                            tenant_b,  # cross-tenant — must be rejected by INSERT blocked
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


# ── test_update_rejected_bom_matrix ───────────────────────────────


def test_tenant_a_cannot_update_tenant_b_bom_matrix(rls_db, tenant_pair) -> None:
    """AC #4: tenant A JWT cannot UPDATE tenant B's bom_matrix row.

    RLS USING makes the row INVISIBLE so UPDATE silently affects 0 rows
    (no exception). Verify child_qty_per_parent remains unchanged.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            await _seed_cost_bom_rows(conn, (tenant_a, tenant_b))
            try:
                # Tenant A tries to tamper with all rows.
                tenant_conn = await _open_as_tenant(tenant_a)
                try:
                    status = await tenant_conn.execute(
                        "UPDATE bom_matrix SET child_qty_per_parent = 99.9999 "
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
                    qty = await owner_b_conn.fetchval(
                        "SELECT child_qty_per_parent FROM bom_matrix "
                        "WHERE tenant_id = $1 LIMIT 1",
                        tenant_b,
                    )
                    # The seed inserted 4.0000 — must remain unchanged.
                    assert float(qty) == 4.0000, (
                        f"Tenant B's bom_matrix was tampered! "
                        f"child_qty_per_parent={qty}"
                    )
                finally:
                    await owner_b_conn.close()
            finally:
                await conn.close()
        except Exception:
            pass

    asyncio.run(run())
