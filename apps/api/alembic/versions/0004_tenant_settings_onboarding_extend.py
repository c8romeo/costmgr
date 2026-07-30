"""Onboarding wizard JSONB schema extension (Story 1.2 — Task 8.1).

The `tenant_settings.onboarding` JSONB namespace is schemaless — adding new
keys (`fiscal_year_start` / `currency` / `language` / `allocation_criteria`)
does NOT require a migration. This revision exists to:

  1. Anchor the wizard fields in the migration history (so the docs in
     `docs/onboarding-schema.md#5-migration-history` stay aligned).
  2. Provide a single forward-only commit point for the JSONB validator
     in `apps/api/core/jsonb_schemas.py` — application-level enforcement
     of `fiscal_year_start: YYYY-MM` and `currency ∈ {KRW, USD}`.

No DDL is required. The wizard writes are gated by:

  - Pydantic models in `apps/api/modules/m0_onboarding/schemas.py`
    (`FiscalYearStartField`, `CurrencyField`, `LanguageField`,
    `AllocationCriteriaUpdateRequest`) — rejects malformed values at the
    API boundary (422).
  - `enforce_onboarding_schema()` in `apps/api/core/jsonb_schemas.py`
    called from `SettingsService.update_onboarding_field` after every
    write — catches defensive regressions (400 JSONB_SCHEMA_VIOLATION).

Revision ID: 0004_tenant_settings_onboarding_extend
Revises: 0003_settings_version_bigint
Create Date: 2026-07-30
"""
from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "0004_tenant_settings_onboarding_extend"
down_revision = "0003_settings_version_bigint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No DDL — JSONB is schemaless. See module docstring."""
    pass


def downgrade() -> None:
    """No DDL — reverse migration is a no-op.

    Story 1.2 only ADDS wizard write endpoints and validation. Dropping them
    requires removing Pydantic models + service methods, not a DB rollback.
    """
    pass