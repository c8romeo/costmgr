"""Phase 25 wire — alembic 0057 phase_25_vendor_management.

Phase 25 wire (cj-style 173번째) — FinOps Vendor Management post-budget-
allocation layer territory (PRD §F41 + AD-53 (a)~(g) 7 sub-decisions).

This migration creates ONLY 1 NEW preview table for Phase 25 FinOps
Vendor Management wire. Phase 25 derives vendor management metrics
from Phase 14 optimization + Phase 18 commitment + Phase 19 pricing +
Phase 22 chargeback_settlement + Phase 23 unit_economics + Phase 24
budget_planning ledger data on-the-fly (no persistent per-vendor /
per-contract / per-scorecard tables beyond the preview snapshot).
The preview table stores idempotency-key UNIQUE snapshots of dry-run
results.

Phase 25 differs from Phase 24 in that:
- Phase 24 stores 1 preview only (pre-allocation layer computed on-the-fly)
- Phase 25 stores 1 preview only (post-budget-allocation layer
  computed on-the-fly)
- This minimizes storage footprint + aligns with D-FINOPS-14 honestly
  DEFER (vendor marketplace integration + auto-procurement + vendor
  consolidation + vendor ESG + AI-driven RFP + SLA auto-inforcement +
  multi-currency FX + invoice OCR + KYC + ML risk scoring all honestly
  DEFER to future Phase 25.x)

Tables:
1. phase_25_vendor_management_preview (preview snapshot for dry-run + idempotency)
   - preview_id (UUID PK)
   - tenant_id (UUID, indexed)
   - preview_type (TEXT, default='vendor_management_dry_run')
   - period_key (TEXT)
   - vendor_catalog_preview_data (JSONB)
   - vendor_selection_preview_data (JSONB)
   - vendor_contract_preview_data (JSONB)
   - vendor_performance_preview_data (JSONB)
   - vendor_spend_attribution_preview_data (JSONB)
   - audit_action (TEXT, default='vendor_dry_run_executed')
   - idempotency_key (TEXT, UNIQUE per tenant_id + period_key + preview_type)
   - source_attribution (JSONB, GIN-indexed for 5-dim source attribution
     queries from Phase 14 + Phase 18 + Phase 19 + Phase 22 + Phase 23 +
     Phase 24 ledger data)
   - computed_at (TIMESTAMPTZ, default NOW())
   - trace_id (TEXT)

5-NEW-module composition layer (vendor_catalog_engine +
vendor_selection_engine + vendor_contract_lifecycle_engine +
vendor_performance_evaluation + vendor_spend_attribution) derived
from Phase 14 + Phase 18 + Phase 19 + Phase 22 + Phase 23 + Phase 24
ledger data via 6 vendor_category taxonomy + 5-dim weighted scoring +
sequential lifecycle + Epic 12 2FA 챌린지 mandatory (high-value 10M
KRW/year) + 4 cadence schedule KST pytz (daily_lifecycle 04:00 +
monthly_performance 03:00 + monthly_spend 03:15 + quarterly_review
03:30) + dry-run mode + 12 NEW audit actions + 16 NEW typed
exceptions + D-FINOPS-14 honestly DEFER (vendor marketplace +
auto-procurement + vendor consolidation + vendor ESG + AI-driven RFP
+ SLA auto-inforcement + multi-currency FX + invoice OCR + KYC + ML
risk scoring).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~24 carry-over: phase_11_finops_* ~ phase_24_budget_planning_*
tables RLS 정합 보존.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0057_phase_25_vendor_management"
down_revision = "0056_phase_24_budget_planning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 1 NEW preview table with RLS + indexes.

    Phase 25 introduces ONLY 1 preview table — post-budget-allocation
    layer is computed on-the-fly from Phase 14 + Phase 18 + Phase 19 +
    Phase 22 + Phase 23 + Phase 24 ledger data. The preview table is
    for materialized snapshot caching + idempotency_key UNIQUE
    constraint + source_attribution GIN-indexed JSONB for 5-module
    composition source attribution queries.
    """

    # ── 1. phase_25_vendor_management_preview ──
    op.create_table(
        "phase_25_vendor_management_preview",
        sa.Column("preview_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "preview_type",
            sa.Text,
            nullable=False,
            server_default="vendor_management_dry_run",
        ),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column(
            "vendor_catalog_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "vendor_selection_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "vendor_contract_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "vendor_performance_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "vendor_spend_attribution_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "audit_action",
            sa.Text,
            nullable=False,
            server_default="vendor_dry_run_executed",
        ),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column(
            "source_attribution",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_phase_25_vendor_management_preview_tenant_idempotency",
        ),
        sa.CheckConstraint(
            "preview_type IN ("
            "'vendor_management_dry_run', "
            "'vendor_selection_dry_run', "
            "'vendor_contract_dry_run', "
            "'vendor_performance_dry_run', "
            "'vendor_spend_attribution_dry_run'"
            ")",
            name="ck_phase_25_vendor_management_preview_type",
        ),
        sa.CheckConstraint(
            "audit_action IN ("
            "'vendor_created', "
            "'vendor_updated', "
            "'vendor_status_changed', "
            "'vendor_blacklisted', "
            "'vendor_selection_executed', "
            "'vendor_contract_approved', "
            "'vendor_contract_renewed', "
            "'vendor_contract_terminated', "
            "'vendor_performance_evaluated', "
            "'vendor_spend_attributed', "
            "'vendor_risk_flagged', "
            "'vendor_dry_run_executed'"
            ")",
            name="ck_phase_25_vendor_management_preview_audit_action",
        ),
    )

    # ── Indexes (Phase 24 verbatim pattern) ──────────────────────────────
    op.create_index(
        "ix_phase_25_vendor_management_preview_tenant_period",
        "phase_25_vendor_management_preview",
        ["tenant_id", "period_key"],
        unique=False,
    )
    op.create_index(
        "ix_phase_25_vendor_management_preview_audit_action",
        "phase_25_vendor_management_preview",
        ["audit_action"],
        unique=False,
    )

    # ── JSONB GIN index for source_attribution (5-module composition ref) ──
    op.execute(
        "CREATE INDEX ix_phase_25_vendor_management_preview_source_attribution_gin "
        "ON phase_25_vendor_management_preview USING gin (source_attribution);"
    )

    # ── JSONB GIN index for vendor_selection_preview_data ───────────────
    op.execute(
        "CREATE INDEX ix_phase_25_vendor_management_preview_selection_data_gin "
        "ON phase_25_vendor_management_preview USING gin (vendor_selection_preview_data);"
    )

    # ── Composite index for fast tenant+period+preview_type lookups ──────
    op.create_index(
        "ix_phase_25_vendor_management_preview_tenant_period_type",
        "phase_25_vendor_management_preview",
        ["tenant_id", "period_key", "preview_type"],
        unique=False,
    )

    # ── RLS policy (CR 0-2 verbatim) ─────────────────────────────────────
    op.execute("ALTER TABLE phase_25_vendor_management_preview ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_phase_25_vendor_management_preview "
        "ON phase_25_vendor_management_preview USING ("
        "tenant_id = current_setting('app.tenant_id', true)::uuid"
        ");"
    )


def downgrade() -> None:
    """Drop RLS policy + 1 preview table."""
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_phase_25_vendor_management_preview "
        "ON phase_25_vendor_management_preview;"
    )
    op.execute("ALTER TABLE phase_25_vendor_management_preview DISABLE ROW LEVEL SECURITY;")
    op.drop_index(
        "ix_phase_25_vendor_management_preview_tenant_period_type",
        table_name="phase_25_vendor_management_preview",
    )
    op.drop_index(
        "ix_phase_25_vendor_management_preview_selection_data_gin",
        table_name="phase_25_vendor_management_preview",
    )
    op.drop_index(
        "ix_phase_25_vendor_management_preview_source_attribution_gin",
        table_name="phase_25_vendor_management_preview",
    )
    op.drop_index(
        "ix_phase_25_vendor_management_preview_audit_action",
        table_name="phase_25_vendor_management_preview",
    )
    op.drop_index(
        "ix_phase_25_vendor_management_preview_tenant_period",
        table_name="phase_25_vendor_management_preview",
    )
    op.drop_table("phase_25_vendor_management_preview")
