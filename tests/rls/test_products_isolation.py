"""tests/rls/test_products_isolation.py — RLS isolation for the products table.

Story 2.1 — Task 6.3. Mirrors the Story 1.3 pattern in
`test_ai_documents_input_drafts.py`. Tests are CI-only (gated by the
`rls_db` fixture — set CI=true or RLS_RUN_LOCAL=1 to run locally).

Verified (AC #3 / AD-3):
- Cross-tenant SELECT on `products` returns 0 rows (RLS USING).
- Cross-tenant INSERT on `products` is rejected by RLS WITH CHECK.
- Cross-tenant UPDATE affects 0 rows (silent — same RLS-CI-6 pattern).
- Owner role can SELECT + INSERT + UPDATE own-tenant products (positive control).
- Viewer role CANNOT INSERT a product (role policy: owner-only mutation).
- Service-role seeded fixture: `service_role` write + tenant-role JWT read.

H8 / H9 / M9 review patches (Story 2.1):
- H8 — `_seed_product` is now `async`; tests `await` it instead of
  calling `asyncio.get_event_loop().run_until_complete` (the sync
  wrapper hung silently under pytest 9.1.1 when no event loop was
  running yet — `DeprecationWarning` in 3.10, `RuntimeError` in 3.12+).
- H9 — the seeding transaction sets `request.jwt.claims = '{"role":
  "service_role",...}'` so the INSERT actually bypasses RLS. Without
  this, the seed hit the WITH CHECK policy and was rejected.
- M9 — UUID v7 fallback uses the project's `packages.common.uuid7`
  module (Python 3.12 stdlib has no `uuid.uuid7()`). The previous
  `hasattr(uuid, "uuid7")` check returned False and silently fell
  through to v4.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import asyncpg

# `rls_db` is the CI gate fixture (pytest.skip when RLS not enabled).
# `tenant_pair` depends on it transitively, so ruff sees the test
# signatures as taking an unused argument. The fixture MUST remain in
# the signature so the gate fires before any `await tenant_pair()` call.
# ruff: noqa: ARG001
import pytest  # noqa: E402  (follows the noqa comment above)

# Ensure packages/ is on sys.path so the uuid7 import resolves regardless
# of the test runner's CWD.
_PKG_ROOT = Path(__file__).resolve().parents[2] / "packages"
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

# M9: use the project's UUID v7 helper. Python 3.12 stdlib does NOT
# expose `uuid.uuid7()`; the previous `hasattr` probe always returned
# False and silently degraded to v4, breaking time-ordered assumptions.
from common.uuid7 import uuid7 as _uuid7  # type: ignore[import-not-found]  # noqa: E402

# CR 0.2: DSN uses the non-superuser + non-bypassrls role created by the
# RLS CI shim (see scripts/ci/rls_db_setup.sh).
DSN = "postgresql://costmgr_test:costmgr_test@localhost:54322/postgres"


def _jwt_claims(tenant_id: uuid.UUID, role: str = "owner") -> str:
    return json.dumps(
        {
            "sub": str(uuid.uuid4()),
            "app_metadata": {"tenant_id": str(tenant_id), "role": role},
        }
    )


async def _open_as_tenant(
    tenant_id: uuid.UUID, role: str = "owner"
) -> asyncpg.Connection:
    """Open a NEW connection (as costmgr_test) and simulate a tenant JWT."""
    conn = await asyncpg.connect(DSN)
    claims = _jwt_claims(tenant_id, role)
    await conn.execute("BEGIN")
    await conn.execute(f"SET LOCAL request.jwt.claims = '{claims}'")
    return conn


def _service_role_claims() -> str:
    """JWT claims that exercise the `service_role` bypass.

    H9: seeding INSERTs run on the same `costmgr_test` connection used
    by the test bodies (RLS-active). To insert a fixture row that the
    subsequent tenant-role JWT can read, the seed transaction must
    present service-role claims so the WITH CHECK policy admits it.
    """
    return json.dumps(
        {
            "sub": str(uuid.uuid4()),
            "app_metadata": {"role": "service_role"},
            "role": "service_role",
        }
    )


async def _seed_product(
    conn: asyncpg.Connection,
    tenant_id: uuid.UUID,
    *,
    product_id: uuid.UUID | None = None,
    code: str = "MAT-0001",
    product_type: str = "material",
    name: str = "테스트 원자재",
) -> uuid.UUID:
    """Insert a `products` row as service_role (bypasses RLS).

    Used to seed test fixtures — tests then assert that tenant-role JWTs
    cannot read/cross-write each other's rows.

    H8: now `async`; callers `await` it. The previous sync wrapper that
    used `asyncio.get_event_loop().run_until_complete` hung under
    pytest 9.1.1 + Python 3.12 (no running loop + deprecation).
    """
    pid = product_id or _uuid7()
    # H9: the seed transaction must impersonate `service_role` for the
    # WITH CHECK policy to admit the INSERT. Without this, the seed
    # itself failed with InsufficientPrivilegeError and the test got
    # 0 rows back instead of asserting isolation.
    await conn.execute("BEGIN")
    await conn.execute(
        f"SET LOCAL request.jwt.claims = '{_service_role_claims()}'"
    )
    try:
        await conn.execute(
            """
            INSERT INTO products (
                id, tenant_id, product_type, code, name,
                unit, unit_cost_krw, unit_cost_usd, description,
                is_active, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE, now(), now())
            """,
            pid,
            tenant_id,
            product_type,
            code,
            name,
            "EA",
            1000,
            Decimal("0.75"),
            "테스트 제품",
        )
        await conn.execute("COMMIT")
    except Exception:
        await conn.execute("ROLLBACK")
        raise
    return pid


# ── Test isolation helpers ───────────────────────────────────
def test_select_products_other_tenant_returns_zero(
    rls_db, tenant_pair
) -> None:
    """AC #3 / AD-3: tenant A's JWT cannot see tenant B's products rows.

    Mirrors Story 1.3's `test_select_input_drafts_other_tenant_returns_zero`.
    The unique index on (tenant_id, code) enforces intra-tenant
    uniqueness; RLS enforces inter-tenant isolation.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            # Seed: insert a product for tenant B via service_role.
            await _seed_product(conn, tenant_b, code="MAT-0001")

            # Open a connection as tenant A and try to read tenant B's product.
            tenant_a_conn = await _open_as_tenant(tenant_a)
            try:
                rows = await tenant_a_conn.fetch(
                    "SELECT * FROM products WHERE tenant_id = $1",
                    tenant_b,
                )
                assert len(rows) == 0, (
                    f"Expected 0 products for tenant B, got {len(rows)} — RLS leak"
                )
            finally:
                await tenant_a_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_select_owner_sees_own(rls_db, tenant_pair) -> None:
    """Owner role CAN SELECT products for their own tenant (positive control).

    Sanity check that the SELECT policy is wired correctly.
    """

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            # Seed a product for tenant A.
            await _seed_product(conn, tenant_a, code="MAT-0001")

            # Open as tenant A's owner and check the row is visible.
            owner_conn = await _open_as_tenant(tenant_a, role="owner")
            try:
                count = await owner_conn.fetchval(
                    "SELECT count(*) FROM products WHERE tenant_id = $1",
                    tenant_a,
                )
                assert count == 1, f"Expected 1 product for tenant A, got {count}"
            finally:
                await owner_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_product_owner_succeeds(rls_db, tenant_pair) -> None:
    """Owner role CAN insert a product for their own tenant (positive control).

    AC #1: owner + matching tenant_id passes the WITH CHECK.
    """

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            owner_conn = await _open_as_tenant(tenant_a, role="owner")
            try:
                await owner_conn.execute(
                    """
                    INSERT INTO products (
                        id, tenant_id, product_type, code, name,
                        unit, unit_cost_krw, unit_cost_usd,
                        is_active, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE, now(), now())
                    """,
                    uuid.uuid4(),
                    tenant_a,
                    "product",
                    "PRD-0001",
                    "테스트 제품",
                    "EA",
                    5000,
                    Decimal("3.75"),
                )
            finally:
                await owner_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_product_viewer_role_rejected(rls_db, tenant_pair) -> None:
    """Viewer role CANNOT insert a product (AC #1 — owner-only mutation).

    The RLS WITH CHECK policy restricts to `TO owner`. Viewer must be
    rejected with `InsufficientPrivilegeError`.
    """

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            viewer_conn = await _open_as_tenant(tenant_a, role="viewer")
            try:
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await viewer_conn.execute(
                        """
                        INSERT INTO products (
                            id, tenant_id, product_type, code, name,
                            is_active, created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5, TRUE, now(), now())
                        """,
                        uuid.uuid4(),
                        tenant_a,
                        "product",
                        "PRD-0002",
                        "시도 — 거부되어야 함",
                    )
            finally:
                await viewer_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_cross_tenant_product_rejected(rls_db, tenant_pair) -> None:
    """AC #3 / AD-3: tenant A's JWT cannot INSERT with tenant B's UUID.

    WITH CHECK enforces `tenant_id = (jwt -> tenant_id)::uuid` so a
    mismatched tenant_id is rejected even when the actor has owner role.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            # Open as tenant A's owner but try to INSERT with tenant B's id.
            tenant_a_conn = await _open_as_tenant(tenant_a, role="owner")
            try:
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await tenant_a_conn.execute(
                        """
                        INSERT INTO products (
                            id, tenant_id, product_type, code, name,
                            is_active, created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5, TRUE, now(), now())
                        """,
                        uuid.uuid4(),
                        tenant_b,  # ← mismatched
                        "material",
                        "MAT-0099",
                        "악의 시도 — 거부되어야 함",
                    )
            finally:
                await tenant_a_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_update_cross_tenant_product_zero_rows(rls_db, tenant_pair) -> None:
    """AC #3: cross-tenant UPDATE is silent (USING filters out non-own rows).

    RLS USING clause filters SELECT to own-tenant; UPDATE then operates on
    zero rows. The service relies on the rowcount check to surface 404.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            # Seed a product for tenant B.
            product_id = await _seed_product(conn, tenant_b, code="MAT-0001")

            # Tenant A's owner tries to update tenant B's product.
            tenant_a_conn = await _open_as_tenant(tenant_a, role="owner")
            try:
                result = await tenant_a_conn.execute(
                    """
                    UPDATE products SET name = '해킹 시도'
                    WHERE id = $1
                    """,
                    product_id,
                )
                # Result is "UPDATE 0" — silent, no rows affected.
                assert "0" in result, f"Expected UPDATE 0, got {result!r}"
            finally:
                await tenant_a_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())
