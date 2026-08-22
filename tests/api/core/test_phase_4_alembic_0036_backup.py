"""tests/api/core/test_phase_4_alembic_0036_backup.py — alembic 0036 backup strategy.

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.7.
Alembic migration code-shape verification for `phase_4_backup_strategy` table.
Mirrors Phase 3-0 test_phase_3_0_hook_migration.py pattern (T9 precedent).
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
ALEMBIC_0036 = (
    REPO_ROOT
    / "apps"
    / "api"
    / "alembic"
    / "versions"
    / "0036_phase_4_backup_strategy.py"
)


@pytest.fixture(scope="module")
def migration_content() -> str:
    assert ALEMBIC_0036.exists(), "alembic 0036 missing"
    return ALEMBIC_0036.read_text(encoding="utf-8")


class TestAlembic0036Identifiers:
    """Migration MUST declare revision + down_revision identifiers."""

    def test_revision_string(self, migration_content: str) -> None:
        assert 'revision: str = "0036_phase_4_backup_strategy"' in migration_content

    def test_down_revision_is_0035(self, migration_content: str) -> None:
        assert (
            'down_revision: str | None = "0035_custom_access_token_hook"'
            in migration_content
        )


class TestAlembic0036TableDefinition:
    """Migration MUST create phase_4_backup_strategy with required columns."""

    def test_creates_phase_4_backup_strategy_table(
        self, migration_content: str
    ) -> None:
        assert 'op.create_table(\n        "phase_4_backup_strategy"' in migration_content

    def test_id_column_is_bigserial_primary_key(
        self, migration_content: str
    ) -> None:
        # BigInteger + Identity + primary_key=True
        assert "sa.BigInteger()" in migration_content
        assert "primary_key=True" in migration_content

    def test_backup_type_column_present(self, migration_content: str) -> None:
        assert '"backup_type"' in migration_content

    def test_started_at_column_present(self, migration_content: str) -> None:
        assert '"started_at"' in migration_content

    def test_completed_at_column_nullable(self, migration_content: str) -> None:
        assert '"completed_at"' in migration_content
        assert "nullable=True" in migration_content

    def test_size_bytes_column_present(self, migration_content: str) -> None:
        assert '"size_bytes"' in migration_content

    def test_checksum_sha256_column_present(
        self, migration_content: str
    ) -> None:
        assert '"checksum_sha256"' in migration_content

    def test_storage_url_column_present(self, migration_content: str) -> None:
        assert '"storage_url"' in migration_content

    def test_status_column_has_default_in_progress(
        self, migration_content: str
    ) -> None:
        assert '"status"' in migration_content
        assert "server_default=sa.text(\"'in_progress'\")" in migration_content

    def test_tenant_id_column_nullable_uuid(
        self, migration_content: str
    ) -> None:
        assert '"tenant_id"' in migration_content
        assert "sa.dialects.postgresql.UUID(as_uuid=True)" in migration_content
        assert "nullable=True" in migration_content


class TestAlembic0036CheckConstraints:
    """Migration MUST declare CHECK constraints for enum-like columns."""

    def test_backup_type_check_constraint(
        self, migration_content: str
    ) -> None:
        assert "ck_phase_4_backup_strategy_backup_type" in migration_content
        assert "auto_pitr" in migration_content
        assert "manual_admin" in migration_content
        assert "manual_export" in migration_content

    def test_status_check_constraint(self, migration_content: str) -> None:
        assert "ck_phase_4_backup_strategy_status" in migration_content
        assert "'in_progress'" in migration_content
        assert "'completed'" in migration_content
        assert "'failed'" in migration_content

    def test_completed_after_started_check(
        self, migration_content: str
    ) -> None:
        assert (
            "ck_phase_4_backup_strategy_completed_after_started"
            in migration_content
        )
        assert "completed_at IS NULL OR completed_at >= started_at" in migration_content


class TestAlembic0036Indexes:
    """Migration MUST declare supporting indexes."""

    def test_status_index(self, migration_content: str) -> None:
        assert "ix_phase_4_backup_strategy_status" in migration_content

    def test_started_at_desc_index(self, migration_content: str) -> None:
        assert "ix_phase_4_backup_strategy_started_at_desc" in migration_content

    def test_tenant_started_index(self, migration_content: str) -> None:
        assert "ix_phase_4_backup_strategy_tenant_started" in migration_content


class TestAlembic0036Downgrade:
    """Migration MUST have a working downgrade."""

    def test_downgrade_function_present(self, migration_content: str) -> None:
        assert "def downgrade() -> None:" in migration_content
        assert "op.drop_table(\"phase_4_backup_strategy\")" in migration_content
