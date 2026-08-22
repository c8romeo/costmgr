"""tests.api.core.test_epic_16_alembic_0038_tenant_idps — migration tests.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — AC #7.3.
Tests the alembic 0038 migration code-shape (table + 13 columns + UNIQUE
+ RLS 3-policy + 3 CHECK constraints + index + trigger + down_revision
chain + acme seed data migration).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_0038 = (
    REPO_ROOT
    / "apps"
    / "api"
    / "alembic"
    / "versions"
    / "0038_epic_16_tenant_idps.py"
)


@pytest.fixture(scope="module")
def migration_content() -> str:
    assert ALEMBIC_0038.exists(), "alembic 0038 missing"
    return ALEMBIC_0038.read_text(encoding="utf-8")


class TestMigrationShape:
    def test_revision_id(self, migration_content: str) -> None:
        assert 'revision: str = "0038_epic_16_tenant_idps"' in migration_content

    def test_down_revision_chain(self, migration_content: str) -> None:
        # down_revision must equal Epic 15 alembic 0037.
        assert (
            'down_revision: str | None = "0037_epic_15_sso_external_identities"'
            in migration_content
        )

    def test_table_creation(self, migration_content: str) -> None:
        assert "tenant_idps" in migration_content
        assert "create_table" in migration_content


class TestColumns:
    """Verify all 13 columns from PRD §F19.1 + AC #1.1 verbatim are declared."""

    def test_id_column(self, migration_content: str) -> None:
        assert "gen_random_uuid()" in migration_content

    def test_tenant_id_column(self, migration_content: str) -> None:
        assert "tenant_id" in migration_content
        assert "ForeignKey" in migration_content
        assert "tenants.id" in migration_content

    def test_idp_entity_id_column(self, migration_content: str) -> None:
        assert "idp_entity_id" in migration_content

    def test_idp_sso_url_column(self, migration_content: str) -> None:
        assert "idp_sso_url" in migration_content

    def test_idp_slo_url_column_nullable(self, migration_content: str) -> None:
        assert "idp_slo_url" in migration_content
        # SLO URL is optional — nullable=True.
        assert "nullable=True" in migration_content

    def test_idp_x509_cert_column(self, migration_content: str) -> None:
        assert "idp_x509_cert" in migration_content

    def test_acs_url_column(self, migration_content: str) -> None:
        assert "acs_url" in migration_content

    def test_name_id_format_column(self, migration_content: str) -> None:
        assert "name_id_format" in migration_content

    def test_enabled_column(self, migration_content: str) -> None:
        assert "enabled" in migration_content
        assert "Boolean" in migration_content or "BOOLEAN" in migration_content

    def test_created_at_column(self, migration_content: str) -> None:
        assert "created_at" in migration_content

    def test_updated_at_column(self, migration_content: str) -> None:
        assert "updated_at" in migration_content

    def test_created_by_column(self, migration_content: str) -> None:
        assert "created_by" in migration_content
        # FK → users.id (AC #1.1 verbatim).
        assert "users.id" in migration_content

    def test_updated_by_column(self, migration_content: str) -> None:
        assert "updated_by" in migration_content


class TestConstraints:
    """AC #1.2 + AC #1.7 verbatim: UNIQUE + 3 CHECK constraints."""

    def test_unique_constraint_tenant_entity(self, migration_content: str) -> None:
        # UNIQUE (tenant_id, idp_entity_id) — AC #1.2.
        assert "UniqueConstraint" in migration_content
        assert '"tenant_id"' in migration_content
        assert '"idp_entity_id"' in migration_content
        assert "uq_tenant_idps_tenant_entity" in migration_content

    def test_check_entity_id_not_empty(self, migration_content: str) -> None:
        assert "ck_tenant_idps_entity_id_not_empty" in migration_content
        assert "length(btrim(idp_entity_id)) > 0" in migration_content

    def test_check_sso_url_https(self, migration_content: str) -> None:
        assert "ck_tenant_idps_sso_url_https" in migration_content
        assert "idp_sso_url LIKE 'https://%'" in migration_content

    def test_check_x509_cert_pem(self, migration_content: str) -> None:
        assert "ck_tenant_idps_x509_cert_pem" in migration_content
        assert "BEGIN CERTIFICATE" in migration_content
        assert "END CERTIFICATE" in migration_content


class TestIndex:
    def test_index_tenant_id(self, migration_content: str) -> None:
        assert "idx_tenant_idps_tenant_id" in migration_content
        assert "create_index" in migration_content


class TestTrigger:
    def test_updated_at_trigger(self, migration_content: str) -> None:
        assert "updated_at_auto_update_trg" in migration_content
        assert "CREATE TRIGGER" in migration_content
        assert "BEFORE UPDATE" in migration_content
        assert "set_updated_at" in migration_content


class TestRLS:
    """CR 0-2 RLS lesson verbatim: 3-policy split (Epic 15 pattern)."""

    def test_enable_row_level_security(self, migration_content: str) -> None:
        assert "ENABLE ROW LEVEL SECURITY" in migration_content

    def test_force_row_level_security(self, migration_content: str) -> None:
        assert "FORCE ROW LEVEL SECURITY" in migration_content

    def test_policy_tenant_isolation(self, migration_content: str) -> None:
        assert "tenant_idps_tenant_isolation" in migration_content
        assert "current_setting('app.tenant_id', true)" in migration_content

    def test_policy_service_role_bypass(self, migration_content: str) -> None:
        assert "tenant_idps_service_role_bypass" in migration_content
        assert "TO service_role" in migration_content

    def test_policy_anon_block(self, migration_content: str) -> None:
        assert "tenant_idps_anon_block" in migration_content
        assert "TO anon" in migration_content


class TestAcmeSeed:
    """PRD §F19.5 verbatim backward compatibility — Epic 15 acme row preserved."""

    def test_seed_insert(self, migration_content: str) -> None:
        assert "INSERT INTO public.tenant_idps" in migration_content

    def test_seed_entity_id(self, migration_content: str) -> None:
        # Mirrors saml_routes.py line 80 `idp.example.com` placeholder.
        assert "idp.example.com" in migration_content

    def test_seed_acme_slug(self, migration_content: str) -> None:
        assert "'acme'" in migration_content or "slug = 'acme'" in migration_content

    def test_seed_on_conflict_noop(self, migration_content: str) -> None:
        # Idempotent re-seed guard.
        assert "ON CONFLICT" in migration_content
        assert "DO NOTHING" in migration_content


class TestDowngrade:
    def test_drop_policies(self, migration_content: str) -> None:
        # All 3 RLS policies must be dropped on downgrade.
        assert "DROP POLICY IF EXISTS tenant_idps_anon_block" in migration_content
        assert (
            "DROP POLICY IF EXISTS tenant_idps_service_role_bypass"
            in migration_content
        )
        assert (
            "DROP POLICY IF EXISTS tenant_idps_tenant_isolation"
            in migration_content
        )

    def test_drop_trigger(self, migration_content: str) -> None:
        assert "DROP TRIGGER IF EXISTS updated_at_auto_update_trg" in migration_content

    def test_drop_index(self, migration_content: str) -> None:
        assert "drop_index" in migration_content

    def test_drop_table(self, migration_content: str) -> None:
        assert "drop_table" in migration_content
