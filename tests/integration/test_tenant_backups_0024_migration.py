"""tests.integration.test_tenant_backups_0024_migration — Story 12.2 migration pin.

Pins the 0024_tenant_backups migration schema against the TenantBackup ORM
model in apps/api/core/db_models.py. Catches drift between the migration
DDL and the ORM model definitions.

Coverage:
- Table exists with 12 expected columns
- Column types match ORM (UUID, TIMESTAMP, JSONB, INTEGER, TEXT, TIMESTAMPTZ)
- Indexes exist (tenant_id+backup_date DESC, partial purged_at,
  partial UNIQUE active per day)
- Foreign keys: tenants(id) ON DELETE CASCADE, users(id) ON DELETE SET NULL
- Comment on table references Story 12.2 + NFR4
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = REPO_ROOT / "apps" / "api" / "alembic" / "versions" / "0024_tenant_backups.py"


def _load_migration_text() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


# ── 1. Migration file exists ────────────────────────────────────
def test_migration_0024_exists() -> None:
    assert MIGRATION_PATH.exists(), f"missing migration: {MIGRATION_PATH}"


def test_migration_0024_revises_0023() -> None:
    """0024 must depend on 0023 (used_challenge_tokens)."""
    text = _load_migration_text()
    assert 'down_revision = "0023_used_challenge_tokens"' in text, (
        "0024 must revise 0023_used_challenge_tokens"
    )


# ── 2. Table schema coverage ─────────────────────────────────────
def test_migration_creates_tenant_backups_table() -> None:
    text = _load_migration_text()
    assert "CREATE TABLE tenant_backups" in text


def test_migration_uses_12_required_columns() -> None:
    """All 12 columns from db_models.TenantBackup must appear."""
    text = _load_migration_text()
    required_columns = [
        "backup_id",
        "tenant_id",
        "backup_date",
        "created_at",
        "schema_version",
        "payload",
        "payload_sha256",
        "row_count_total",
        "audit_log_exported_rows",
        "retention_class",
        "purged_at",
        "triggered_by_user_id",
    ]
    for col in required_columns:
        assert f"\n            {col} " in text or f" {col} " in text, (
            f"column {col!r} missing from migration 0024"
        )


def test_migration_payload_is_jsonb() -> None:
    text = _load_migration_text()
    assert "payload JSONB NOT NULL" in text


def test_migration_purged_at_nullable() -> None:
    text = _load_migration_text()
    assert "purged_at TIMESTAMPTZ NULL" in text


def test_migration_schema_version_default_1_0() -> None:
    text = _load_migration_text()
    assert "schema_version TEXT NOT NULL DEFAULT '1.0'" in text


def test_migration_tenant_id_fk_with_cascade() -> None:
    """tenant_id REFERENCES tenants(id) ON DELETE CASCADE."""
    text = _load_migration_text()
    assert "tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE" in text


def test_migration_triggered_by_user_id_fk_set_null() -> None:
    """triggered_by_user_id REFERENCES users(id) ON DELETE SET NULL."""
    text = _load_migration_text()
    assert (
        "triggered_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL"
        in text
    )


# ── 3. Index coverage ────────────────────────────────────────────
def test_migration_has_tenant_date_index() -> None:
    text = _load_migration_text()
    assert "tenant_backups_tenant_id_backup_date_idx" in text
    assert "ON tenant_backups (tenant_id, backup_date DESC)" in text


def test_migration_has_partial_purged_index() -> None:
    text = _load_migration_text()
    assert "tenant_backups_purged_at_idx" in text
    assert "WHERE purged_at IS NULL" in text


def test_migration_has_partial_unique_active_per_day() -> None:
    """One active (non-purged) backup per tenant per day."""
    text = _load_migration_text()
    assert "tenant_backups_unique_active_per_day" in text
    assert "ON tenant_backups (tenant_id, backup_date)" in text
    assert "WHERE purged_at IS NULL" in text


# ── 4. Documentation coverage ────────────────────────────────────
def test_migration_table_comment_references_nfr4() -> None:
    text = _load_migration_text()
    assert "NFR4" in text
    assert "30-day" in text or "30일" in text


def test_migration_column_payload_comment() -> None:
    text = _load_migration_text()
    assert "COMMENT ON COLUMN tenant_backups.payload" in text


def test_migration_column_sha256_comment() -> None:
    text = _load_migration_text()
    assert "COMMENT ON COLUMN tenant_backups.payload_sha256" in text
    assert "X-Backup-SHA256" in text


# ── 5. Downgrade coverage ────────────────────────────────────────
def test_migration_downgrade_drops_table() -> None:
    text = _load_migration_text()
    assert "DROP TABLE IF EXISTS tenant_backups" in text


# ── 6. ORM model matches migration ───────────────────────────────
def test_orm_model_TenantBackup_exists() -> None:
    """TenantBackup ORM model exists with 12 attributes."""
    from apps.api.core.db_models import TenantBackup

    expected_attrs = {
        "backup_id",
        "tenant_id",
        "backup_date",
        "created_at",
        "schema_version",
        "payload",
        "payload_sha256",
        "row_count_total",
        "audit_log_exported_rows",
        "retention_class",
        "purged_at",
        "triggered_by_user_id",
    }
    # Use __table__ columns to introspect
    actual_cols = {c.name for c in TenantBackup.__table__.columns}
    missing = expected_attrs - actual_cols
    assert not missing, f"TenantBackup ORM missing columns: {missing}"


# ── 7. RLS policy file 0014 exists ──────────────────────────────
def test_rls_0014_policy_file_exists() -> None:
    rls_path = REPO_ROOT / "supabase" / "policies" / "0014_tenant_backups_rls.sql"
    assert rls_path.exists(), f"missing RLS policy: {rls_path}"


def test_rls_0014_enables_rls() -> None:
    rls_path = REPO_ROOT / "supabase" / "policies" / "0014_tenant_backups_rls.sql"
    text = rls_path.read_text(encoding="utf-8")
    assert "ALTER TABLE tenant_backups ENABLE ROW LEVEL SECURITY" in text
    assert "FORCE ROW LEVEL SECURITY" in text


def test_rls_0014_has_3_policies() -> None:
    """3 explicit policies (SELECT same-tenant + SELECT owner + INSERT owner).
    UPDATE/DELETE intentionally absent (AD-2 INSERT-only invariant).
    """
    rls_path = REPO_ROOT / "supabase" / "policies" / "0014_tenant_backups_rls.sql"
    text = rls_path.read_text(encoding="utf-8")
    policy_names = [
        "tenant_backups_select_same_tenant",
        "tenant_backups_select_owner",
        "tenant_backups_insert_owner",
    ]
    for name in policy_names:
        assert f"CREATE POLICY {name}" in text, (
            f"RLS 0014 missing policy {name!r}"
        )


def test_rls_0014_no_update_or_delete_policies() -> None:
    """AD-2 INSERT-only: UPDATE/DELETE must be BLOCKED for app roles.

    Story 12.2 spec is a 5-policy split: 3 ALLOW policies (SELECT
    same-tenant, SELECT owner, INSERT owner) + 2 BLOCK policies
    (UPDATE blocked via `USING (false)`, DELETE blocked via
    `USING (false)`). The block policies ARE explicit named policies
    using `FOR UPDATE` / `FOR DELETE` keywords — that is the standard
    Postgres pattern for "deny via policy". The original test
    implementation (pre-2026-08-20) naively asserted that the literal
    string `FOR UPDATE` / `FOR DELETE` did not appear ANYWHERE in the
    file, which incorrectly rejected the blocking policies. The
    corrected invariant: any UPDATE/DELETE policy MUST have
    `USING (false)` (deny-all for app roles).
    """
    rls_path = REPO_ROOT / "supabase" / "policies" / "0014_tenant_backups_rls.sql"
    text = rls_path.read_text(encoding="utf-8")
    import re

    no_comments = re.sub(r"--[^\n]*", "", text)

    # Find all `CREATE POLICY ... FOR UPDATE` blocks and verify each has USING (false).
    # The pattern is non-greedy across multiple lines until the closing `;`.
    update_policies = re.findall(
        r"CREATE\s+POLICY\s+\w+\s+ON\s+tenant_backups\s+FOR\s+UPDATE\s*[^;]*;",
        no_comments,
        re.IGNORECASE | re.DOTALL,
    )
    for policy_block in update_policies:
        block_lower = policy_block.lower()
        assert "using (false)" in block_lower or "using(false)" in block_lower, (
            "AD-2 INSERT-only violated: RLS 0014 has an UPDATE policy that "
            "is NOT blocking (must use `USING (false)`):\n"
            + policy_block
        )

    delete_policies = re.findall(
        r"CREATE\s+POLICY\s+\w+\s+ON\s+tenant_backups\s+FOR\s+DELETE\s*[^;]*;",
        no_comments,
        re.IGNORECASE | re.DOTALL,
    )
    for policy_block in delete_policies:
        block_lower = policy_block.lower()
        assert "using (false)" in block_lower or "using(false)" in block_lower, (
            "AD-2 INSERT-only violated: RLS 0014 has a DELETE policy that "
            "is NOT blocking (must use `USING (false)`):\n"
            + policy_block
        )


@pytest.fixture(autouse=True)
def _ensure_imports() -> None:
    """Touch ORM module so static analyzers don't flag it unused."""
    pass
