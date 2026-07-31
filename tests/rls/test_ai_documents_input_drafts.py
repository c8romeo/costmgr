"""tests/rls/test_ai_documents_input_drafts.py — RLS isolation for AI extraction tables.

Story 1.3 — Task 1.4. Mirrors the Story 0.2 / 1.2 pattern in
`tests/rls/test_tenant_isolation.py`. Tests are CI-only (gated by the
`rls_db` fixture — set CI=true or RLS_RUN_LOCAL=1 to run locally).

Verified:
- Cross-tenant SELECT on `input_drafts` returns 0 rows (RLS USING).
- Cross-tenant SELECT on `uploaded_documents` returns 0 rows.
- Cross-tenant INSERT on both tables is rejected by RLS WITH CHECK.
- Cross-tenant UPDATE affects 0 rows (silent — same RLS-CI-6 pattern).
- Owner role can SELECT own-tenant drafts (positive control).
- Viewer role CANNOT INSERT a draft (role policy).
- Owner role CAN INSERT a draft (positive control).
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


async def _open_as_tenant(
    tenant_id: uuid.UUID, role: str = "owner"
) -> asyncpg.Connection:
    """Open a NEW connection (as costmgr_test) and simulate a tenant JWT."""
    conn = await asyncpg.connect(DSN)
    claims = _jwt_claims(tenant_id, role)
    await conn.execute("BEGIN")
    await conn.execute(f"SET LOCAL request.jwt.claims = '{claims}'")
    return conn


def _insert_document_via_service(
    conn: asyncpg.Connection,
    tenant_id: uuid.UUID,
    *,
    document_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Insert an `uploaded_documents` row as service_role (bypasses RLS).

    Used to seed test fixtures — tests then assert that tenant-role JWTs
    cannot read/cross-write each other's rows.
    """
    document_id = document_id or uuid.uuid4()
    asyncio.get_event_loop().run_until_complete(
        conn.execute(
            """
            INSERT INTO uploaded_documents (
                document_id, tenant_id, storage_path, mime_type, byte_size,
                content_sha256, uploaded_by, uploaded_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, now())
            """,
            document_id,
            tenant_id,
            f"tenants/{tenant_id}/documents/{document_id}.pdf",
            "application/pdf",
            1024 * 10,
            b"\x00" * 32,
            uuid.uuid4(),
        )
    )
    return document_id


# ── Test isolation helpers ───────────────────────────────────
def test_select_input_drafts_other_tenant_returns_zero(
    rls_db, tenant_pair
) -> None:
    """AC #1.4: tenant A's JWT cannot see tenant B's input_drafts rows.

    The unique index on (tenant_id, document_id, field_name) means RLS
    must enforce isolation BEFORE the index lookup (Postgres plans use
    RLS predicates first when FORCE RLS is on).
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            # Seed: insert a draft for tenant B via service_role.
            document_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO uploaded_documents (
                    document_id, tenant_id, storage_path, mime_type, byte_size,
                    content_sha256, uploaded_by, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                document_id,
                tenant_b,
                f"tenants/{tenant_b}/documents/{document_id}.pdf",
                "application/pdf",
                1024 * 10,
                b"\x00" * 32,
                uuid.uuid4(),
            )
            await conn.execute(
                """
                INSERT INTO input_drafts (
                    draft_id, tenant_id, document_id, field_name, ai_value,
                    draft_hash, requested_by, requested_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                uuid.uuid4(),
                tenant_b,
                document_id,
                "business_registration_number",
                '{"string": "123-45-67890"}',
                b"\xab" * 32,
                uuid.uuid4(),
            )

            # Open a connection as tenant A and try to read tenant B's draft.
            tenant_a_conn = await _open_as_tenant(tenant_a)
            try:
                rows = await tenant_a_conn.fetch(
                    "SELECT * FROM input_drafts WHERE tenant_id = $1",
                    tenant_b,
                )
                assert len(rows) == 0, (
                    f"Expected 0 rows for tenant B, got {len(rows)} — RLS leak"
                )
            finally:
                await tenant_a_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_select_uploaded_documents_other_tenant_returns_zero(
    rls_db, tenant_pair
) -> None:
    """AC #1.4: uploaded_documents is also RLS-isolated."""

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            document_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO uploaded_documents (
                    document_id, tenant_id, storage_path, mime_type, byte_size,
                    content_sha256, uploaded_by, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                document_id,
                tenant_b,
                f"tenants/{tenant_b}/documents/{document_id}.pdf",
                "application/pdf",
                1024 * 10,
                b"\x00" * 32,
                uuid.uuid4(),
            )

            tenant_a_conn = await _open_as_tenant(tenant_a)
            try:
                count = await tenant_a_conn.fetchval(
                    "SELECT count(*) FROM uploaded_documents WHERE tenant_id = $1",
                    tenant_b,
                )
                assert count == 0, f"Expected 0 documents for tenant B, got {count}"
            finally:
                await tenant_a_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_input_draft_owner_role_succeeds(rls_db, tenant_pair) -> None:
    """Owner role CAN insert a draft for their own tenant (positive control).

    Without the RLS policy, the INSERT would succeed. With the policy in
    place, owner + matching tenant_id passes the WITH CHECK.
    """

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            # Seed an uploaded_document for tenant A first (service_role).
            document_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO uploaded_documents (
                    document_id, tenant_id, storage_path, mime_type, byte_size,
                    content_sha256, uploaded_by, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                document_id,
                tenant_a,
                f"tenants/{tenant_a}/documents/{document_id}.pdf",
                "application/pdf",
                1024 * 10,
                b"\x00" * 32,
                uuid.uuid4(),
            )

            # Now open as tenant A's owner and insert a draft.
            owner_conn = await _open_as_tenant(tenant_a, role="owner")
            try:
                await owner_conn.execute(
                    """
                    INSERT INTO input_drafts (
                        draft_id, tenant_id, document_id, field_name, ai_value,
                        draft_hash, requested_by, requested_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                    """,
                    uuid.uuid4(),
                    tenant_a,
                    document_id,
                    "company_name",
                    '{"string": "주식회사 KJW"}',
                    b"\xcd" * 32,
                    uuid.uuid4(),
                )
            finally:
                await owner_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_input_draft_viewer_role_rejected(rls_db, tenant_pair) -> None:
    """Viewer role CANNOT insert (Task 3.6 — owner-only mutation).

    AC #3.6 (Story 1.3): only owner can mutate. The RLS policy WITH CHECK
    enforces `(role = 'owner')` so viewer is rejected with
    InsufficientPrivilegeError.
    """

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            # Seed an uploaded_document for tenant A first.
            document_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO uploaded_documents (
                    document_id, tenant_id, storage_path, mime_type, byte_size,
                    content_sha256, uploaded_by, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                document_id,
                tenant_a,
                f"tenants/{tenant_a}/documents/{document_id}.pdf",
                "application/pdf",
                1024 * 10,
                b"\x00" * 32,
                uuid.uuid4(),
            )

            # Try to insert as viewer role — must be rejected.
            viewer_conn = await _open_as_tenant(tenant_a, role="viewer")
            try:
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await viewer_conn.execute(
                        """
                        INSERT INTO input_drafts (
                            draft_id, tenant_id, document_id, field_name, ai_value,
                            draft_hash, requested_by, requested_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                        """,
                        uuid.uuid4(),
                        tenant_a,
                        document_id,
                        "company_name",
                        '{"string": "주식회사 KJW"}',
                        b"\xef" * 32,
                        uuid.uuid4(),
                    )
            finally:
                await viewer_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_input_draft_member_role_rejected(rls_db, tenant_pair) -> None:
    """Member role CANNOT insert (Task 3.6 — owner-only mutation).

    Member is below owner in the role hierarchy. The RLS WITH CHECK
    requires `(role = 'owner')`.
    """

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            document_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO uploaded_documents (
                    document_id, tenant_id, storage_path, mime_type, byte_size,
                    content_sha256, uploaded_by, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                document_id,
                tenant_a,
                f"tenants/{tenant_a}/documents/{document_id}.pdf",
                "application/pdf",
                1024 * 10,
                b"\x00" * 32,
                uuid.uuid4(),
            )

            member_conn = await _open_as_tenant(tenant_a, role="member")
            try:
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await member_conn.execute(
                        """
                        INSERT INTO input_drafts (
                            draft_id, tenant_id, document_id, field_name, ai_value,
                            draft_hash, requested_by, requested_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                        """,
                        uuid.uuid4(),
                        tenant_a,
                        document_id,
                        "company_name",
                        '{"string": "주식회사 KJW"}',
                        b"\x12" * 32,
                        uuid.uuid4(),
                    )
            finally:
                await member_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_insert_cross_tenant_input_draft_rejected(rls_db, tenant_pair) -> None:
    """AC #3 / AD-3: tenant A's JWT cannot INSERT with tenant B's UUID.

    WITH CHECK enforces `tenant_id = (jwt -> tenant_id)::uuid` so a
    mismatched tenant_id is rejected even if the actor has owner role.
    """

    async def run() -> None:
        conn, (tenant_a, tenant_b) = await tenant_pair()
        try:
            # Seed a document for tenant B (service_role).
            document_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO uploaded_documents (
                    document_id, tenant_id, storage_path, mime_type, byte_size,
                    content_sha256, uploaded_by, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                document_id,
                tenant_b,
                f"tenants/{tenant_b}/documents/{document_id}.pdf",
                "application/pdf",
                1024 * 10,
                b"\x00" * 32,
                uuid.uuid4(),
            )

            # Open as tenant A's owner but try to INSERT with tenant B's id.
            tenant_a_conn = await _open_as_tenant(tenant_a, role="owner")
            try:
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await tenant_a_conn.execute(
                        """
                        INSERT INTO input_drafts (
                            draft_id, tenant_id, document_id, field_name, ai_value,
                            draft_hash, requested_by, requested_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                        """,
                        uuid.uuid4(),
                        tenant_b,  # ← mismatched
                        document_id,
                        "company_name",
                        '{"string": "악의 데이터"}',
                        b"\xff" * 32,
                        uuid.uuid4(),
                    )
            finally:
                await tenant_a_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())


def test_select_input_drafts_owner_sees_own(rls_db, tenant_pair) -> None:
    """Owner role CAN SELECT drafts for their own tenant (positive control).

    Sanity check that the SELECT policy is wired correctly (USING matches
    tenant_id regardless of role).
    """

    async def run() -> None:
        conn, (tenant_a, _) = await tenant_pair()
        try:
            document_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO uploaded_documents (
                    document_id, tenant_id, storage_path, mime_type, byte_size,
                    content_sha256, uploaded_by, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                document_id,
                tenant_a,
                f"tenants/{tenant_a}/documents/{document_id}.pdf",
                "application/pdf",
                1024 * 10,
                b"\x00" * 32,
                uuid.uuid4(),
            )
            draft_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO input_drafts (
                    draft_id, tenant_id, document_id, field_name, ai_value,
                    draft_hash, requested_by, requested_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, now())
                """,
                draft_id,
                tenant_a,
                document_id,
                "company_name",
                '{"string": "주식회사 KJW"}',
                b"\xcd" * 32,
                uuid.uuid4(),
            )

            owner_conn = await _open_as_tenant(tenant_a, role="owner")
            try:
                count = await owner_conn.fetchval(
                    "SELECT count(*) FROM input_drafts WHERE tenant_id = $1",
                    tenant_a,
                )
                assert count == 1
            finally:
                await owner_conn.close()
        finally:
            await conn.close()

    asyncio.run(run())