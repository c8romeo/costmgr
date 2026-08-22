"""tests.api.core.test_epic_15_alembic_0037_external_identities — migration tests.

Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire) — AC #7.6.
Tests the alembic 0037 migration code-shape (table + indexes + RLS + CHECK
+ down_revision chain).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_0037 = (
    REPO_ROOT
    / "apps"
    / "api"
    / "alembic"
    / "versions"
    / "0037_epic_15_sso_external_identities.py"
)


@pytest.fixture(scope="module")
def migration_content() -> str:
    assert ALEMBIC_0037.exists(), "alembic 0037 missing"
    return ALEMBIC_0037.read_text(encoding="utf-8")


class TestMigrationShape:
    def test_revision_id(self, migration_content: str) -> None:
        assert 'revision: str = "0037_epic_15_sso_external_identities"' in migration_content

    def test_down_revision_chain(self, migration_content: str) -> None:
        # down_revision must equal Phase 4 alembic 0036.
        assert 'down_revision: str | None = "0036_phase_4_backup_strategy"' in migration_content

    def test_table_creation(self, migration_content: str) -> None:
        assert "external_identities" in migration_content
        assert "create_table" in migration_content

    def test_provider_column(self, migration_content: str) -> None:
        assert "provider" in migration_content
        # All 8 enum values from AD-28 must be declared.
        for value in [
            "magic_link",
            "google",
            "naver",
            "kakao",
            "saml_okta",
            "saml_azure_ad",
            "saml_google_workspace",
            "saml_custom",
        ]:
            assert f"'{value}'" in migration_content

    def test_provider_user_id_column(self, migration_content: str) -> None:
        assert "provider_user_id" in migration_content
        assert "NOT NULL" in migration_content.upper() or "nullable=False" in migration_content

    def test_tenant_id_column(self, migration_content: str) -> None:
        assert "tenant_id" in migration_content
        assert "UUID" in migration_content

    def test_user_id_column(self, migration_content: str) -> None:
        assert "user_id" in migration_content
        assert "UUID" in migration_content

    def test_linked_at_column(self, migration_content: str) -> None:
        assert "linked_at" in migration_content

    def test_last_used_at_column(self, migration_content: str) -> None:
        assert "last_used_at" in migration_content

    def test_metadata_jsonb(self, migration_content: str) -> None:
        assert "JSONB" in migration_content or "jsonb" in migration_content


class TestIndexes:
    def test_provider_puid_unique(self, migration_content: str) -> None:
        assert "ix_external_identities_provider_puid" in migration_content
        assert "unique=True" in migration_content

    def test_user_provider_index(self, migration_content: str) -> None:
        assert "ix_external_identities_user_provider" in migration_content

    def test_tenant_provider_index(self, migration_content: str) -> None:
        assert "ix_external_identities_tenant_provider" in migration_content

    def test_last_used_at_desc_index(self, migration_content: str) -> None:
        assert "ix_external_identities_last_used_at_desc" in migration_content


class TestCheckConstraints:
    def test_provider_check(self, migration_content: str) -> None:
        assert "ck_external_identities_provider" in migration_content

    def test_puid_not_empty_check(self, migration_content: str) -> None:
        assert "ck_external_identities_puid_not_empty" in migration_content


class TestRLSPolicies:
    def test_rls_enabled(self, migration_content: str) -> None:
        assert "ENABLE ROW LEVEL SECURITY" in migration_content
        assert "FORCE ROW LEVEL SECURITY" in migration_content

    def test_tenant_isolation_policy(self, migration_content: str) -> None:
        # CR 0-2 RLS lesson: tenant_id = current_setting('app.tenant_id').
        assert "tenant_id" in migration_content
        assert "current_setting" in migration_content
        assert "app.tenant_id" in migration_content

    def test_service_role_bypass(self, migration_content: str) -> None:
        assert "service_role" in migration_content

    def test_anon_block(self, migration_content: str) -> None:
        assert "anon" in migration_content
        assert "USING (false)" in migration_content or "USING(false)" in migration_content


class TestDowngrade:
    def test_drop_table(self, migration_content: str) -> None:
        assert "def downgrade" in migration_content
        assert "drop_table" in migration_content

    def test_drop_rls(self, migration_content: str) -> None:
        assert "DISABLE ROW LEVEL SECURITY" in migration_content
        assert "DROP POLICY" in migration_content
