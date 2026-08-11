"""tests.api.test_alembic_0022_users_totp_columns — Story 12.4 migration tests.

8 cases — verify the Alembic 0022 migration shape (Epic 12 carry-over sprint,
sprint-up of Story 12.1 honestly-DEFERred T4):

- revision / down_revision attributes
- down_revision = '0021_cache_invalidation_multi_channel' (11-3 wire tip)
- upgrade() adds 5 columns: totp_secret / totp_enabled_at /
  totp_failed_attempts / totp_lockout_until / totp_recovery_codes_hash
- totp_failed_attempts non-negative CHECK constraint present
- ix_users_totp_lockout_until partial index (lockout-cleanup cron)
- ix_users_totp_enabled_at partial index (M2 entry gate)
- downgrade() drops all 5 columns + 2 indexes + 1 CHECK
- COMMENT ON COLUMN on totp_secret (NFR6 AES-256-GCM contract pin)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

# Lazy-load migration module to avoid alembic env side effects.
_MIGRATION_FILENAME = "0022_users_totp_columns.py"


def _load_migration_module() -> object:
    """Import the 0022 migration module by file path.

    Alembic migration files live in `apps/api/alembic/versions/` (not the
    apps.api. package layout), so we load by file location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions" / _MIGRATION_FILENAME
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0022",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _read_migration_source() -> str:
    """Read the raw migration source for source-text inspections."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / _MIGRATION_FILENAME
    ).read_text(encoding="utf-8")


def test_migration_revision_attribute() -> None:
    m = _load_migration_module()
    assert m.revision == "0022_users_totp_columns"


def test_migration_down_revision_is_11_3_tip() -> None:
    """down_revision must be '0021_cache_invalidation_multi_channel' (Story 11.3 tip)."""
    m = _load_migration_module()
    assert m.down_revision == "0021_cache_invalidation_multi_channel"


def test_migration_upgrade_and_downgrade_callables() -> None:
    m = _load_migration_module()
    assert callable(m.upgrade)
    assert callable(m.downgrade)


def test_migration_upgrade_adds_5_totp_columns() -> None:
    """upgrade() must add all 5 columns via ADD COLUMN IF NOT EXISTS.

    Columns (per `apps/api/core/db_models.py::User`):
    - totp_secret              BYTEA       (NFR6 AES-256-GCM ciphertext)
    - totp_enabled_at          TIMESTAMPTZ (authoritative 2FA-enrolled predicate)
    - totp_failed_attempts     INTEGER     (consecutive challenge failures)
    - totp_lockout_until       TIMESTAMPTZ (5-fail → 15min lockout)
    - totp_recovery_codes_hash JSONB       (8 PBKDF2 entries)
    """
    src = _read_migration_source()
    # Each column literal name must appear in the ALTER TABLE statement.
    for column in (
        "totp_secret",
        "totp_enabled_at",
        "totp_failed_attempts",
        "totp_lockout_until",
        "totp_recovery_codes_hash",
    ):
        assert column in src, f"column {column!r} missing from migration"
    # All 5 must appear in a single ALTER TABLE … ADD COLUMN block (or
    # explicit 5 ADD lines). Source-text presence is enough for the wire.
    add_count = src.count("ADD COLUMN IF NOT EXISTS")
    assert add_count == 5, (
        f"expected 5 ADD COLUMN IF NOT EXISTS statements, got {add_count}"
    )


def test_migration_upgrade_enforces_failed_attempts_non_negative() -> None:
    """upgrade() must enforce totp_failed_attempts >= 0 CHECK invariant.

    The service increments by 1 on failure and resets to 0 on success, so
    a negative value can only come from a bug or a manual UPDATE. The
    CHECK constraint pins the invariant at the DB level.
    """
    src = _read_migration_source()
    assert (
        "users_totp_failed_attempts_non_negative" in src
    ), "migration must name the non-negative CHECK constraint"
    assert "CHECK (totp_failed_attempts >= 0)" in src, (
        "non-negative CHECK expression missing"
    )


def test_migration_upgrade_creates_2_partial_indexes() -> None:
    """upgrade() must create 2 partial indexes for hot-path queries.

    - ix_users_totp_lockout_until: WHERE totp_lockout_until IS NOT NULL
      (lockout-cleanup cron AD-9 KST 02:00 daily)
    - ix_users_totp_enabled_at:    WHERE totp_enabled_at IS NOT NULL
      (M2 entry gate "is this user enrolled?" lookup)
    """
    src = _read_migration_source()
    assert "ix_users_totp_lockout_until" in src, (
        "partial index ix_users_totp_lockout_until missing"
    )
    assert "ix_users_totp_enabled_at" in src, (
        "partial index ix_users_totp_enabled_at missing"
    )
    # Both must be partial indexes (WHERE clause).
    assert "WHERE totp_lockout_until IS NOT NULL" in src, (
        "ix_users_totp_lockout_until must be a partial index"
    )
    assert "WHERE totp_enabled_at IS NOT NULL" in src, (
        "ix_users_totp_enabled_at must be a partial index"
    )


def test_migration_upgrade_documents_nfr6_aes_gcm() -> None:
    """upgrade() must pin NFR6 via COMMENT ON COLUMN totp_secret.

    The comment is the DB-side SSOT for the AES-256-GCM ciphertext
    invariant — any future operator inspecting `\\d+ users` in psql sees
    the encryption contract.
    """
    src = _read_migration_source()
    assert "COMMENT ON COLUMN users.totp_secret" in src, (
        "NFR6 comment on users.totp_secret missing"
    )
    assert "AES-256-GCM" in src, (
        "NFR6 AES-256-GCM contract not documented in migration"
    )
    assert "aad=" in src, (
        "NFR6 aad= binding not documented in migration"
    )


def test_migration_downgrade_drops_5_columns_2_indexes_1_check() -> None:
    """downgrade() must drop 5 columns + 2 indexes + 1 CHECK constraint.

    WARNING: destructive — operators must export `users.totp_*` before
    downgrading. The downgrade is intentionally idempotent (`IF EXISTS`).
    """
    src = _read_migration_source()
    drop_column_count = src.count("DROP COLUMN IF EXISTS")
    assert drop_column_count == 5, (
        f"expected 5 DROP COLUMN IF EXISTS in downgrade, got {drop_column_count}"
    )
    # Both indexes must be dropped.
    assert "DROP INDEX IF EXISTS ix_users_totp_lockout_until" in src
    assert "DROP INDEX IF EXISTS ix_users_totp_enabled_at" in src
    # The non-negative CHECK must be dropped.
    assert (
        "DROP CONSTRAINT IF EXISTS users_totp_failed_attempts_non_negative" in src
    )
