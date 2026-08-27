"""Phase 23 wire — alembic 0055 phase_23_unit_economics.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics derived metric
layer territory (PRD §F39 + AD-51 (a)~(g) 7 sub-decisions).

This migration creates ONLY 1 NEW preview table for Phase 23 FinOps
Unit Economics wire. Phase 23 derives unit_economics metrics from
Phase 22 settlement_id → allocation_lines ledger data on-the-fly
(no persistent per-business-unit/per-transaction/per-margin tables).
The preview table stores idempotency-key UNIQUE snapshots of dry-run
results.

Phase 23 differs from Phase 22 in that:
- Phase 22 stores 9 tables + 1 preview (full persistence layer)
- Phase 23 stores 1 preview only (derived metrics computed on-the-fly)
- This minimizes storage footprint + aligns with D-FINOPS-12 honestly
  DEFER (cost_per_customer CRM + multi-currency FX + real-time stream
  all honestly DEFER to future Phase 23.x)

Tables:
1. phase_23_unit_economics_preview (preview snapshot for dry-run + idempotency)
   - preview_id (UUID PK)
   - tenant_id (UUID, indexed)
   - preview_type (TEXT, default='unit_economics_dry_run')
   - period_key (TEXT)
   - unit_economics_preview_data (JSONB)
   - cost_per_business_unit_preview_data (JSONB)
   - cost_per_transaction_preview_data (JSONB)
   - margin_analysis_preview_data (JSONB)
   - audit_action (TEXT, default='unit_economics_dry_run_executed')
   - idempotency_key (TEXT, UNIQUE per tenant_id + period_key + preview_type)
   - tag_propagation (JSONB, GIN-indexed for filter queries)
   - computed_at (TIMESTAMPTZ, default NOW())
   - trace_id (TEXT)

4-NEW-module composition layer (unit_economics_engine +
cost_per_business_unit + cost_per_transaction + margin_analysis)
derived from Phase 22 settlement_id → allocation_lines ledger via
5-dim cross-join + ledger-key dedup.

5-dim cross-join (cost_center 0.30 + department 0.25 + business_unit
0.20 + tag 0.15 + tenant 0.10) + 4 cadence schedule KST pytz (daily
03:30 + weekly 04:00 + monthly 04:30 + quarterly 05:00) + dry-run
mode + Epic 12 2FA �린지 mandatory (high-value 10M KRW/year) +
7 NEW audit actions + 15 NEW typed exceptions + D-FINOPS-12 honestly
DEFER (cost_per_customer CRM + multi-currency FX + real-time stream).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~22 carry-over: phase_11_finops_* ~ phase_22_chargeback_*
tables RLS 정합 보존.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0055_phase_23_unit_economics"
down_revision = "0054_phase_22_chargeback_settlement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 1 NEW preview table with RLS + indexes.

    Phase 23 introduces ONLY 1 preview table — derived metrics are
    computed on-the-fly from Phase 22 ledger data. The preview table
    is for materialized snapshot caching + idempotency_key UNIQUE
    constraint + tag_propagation GIN-indexed JSONB for filter queries.
    """

    # ── 1. phase_23_unit_economics_preview ──
    op.create_table(
        "phase_23_unit_economics_preview",
        sa.Column("preview_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "preview_type",
            sa.Text,
            nullable=False,
            server_default="unit_economics_dry_run",
        ),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column(
            "unit_economics_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "cost_per_business_unit_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "cost_per_transaction_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "margin_analysis_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "audit_action",
            sa.Text,
            nullable=False,
            server_default="unit_economics_dry_run_executed",
        ),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("tag_propagation", JSONB, nullable=False, server_default="{}"),
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
            name="uq_phase_23_unit_economics_preview_tenant_idempotency",
        ),
        sa.CheckConstraint(
            "preview_type IN ("
            "'unit_economics_dry_run', "
            "'cost_per_business_unit_dry_run', "
            "'cost_per_transaction_dry_run', "
            "'margin_analysis_dry_run'"
            ")",
            name="ck_phase_23_unit_economics_preview_type",
        ),
        sa.CheckConstraint(
            "audit_action IN ("
            "'unit_economics_dry_run_executed', "
            "'cost_per_business_unit_refreshed', "
            "'cost_per_transaction_computed', "
            "'margin_analysis_executed', "
            "'unit_economics_margin_alert', "
            "'unit_economics_margin_negative_alert'"
            ")",
            name="ck_phase_23_unit_economics_preview_audit_action",
        ),
    )

    # ── Indexes (Phase 22 verbatim pattern) ──────────────────────────────
    op.create_index(
        "ix_phase_23_unit_economics_preview_tenant_period",
        "phase_23_unit_economics_preview",
        ["tenant_id", "period_key"],
        unique=False,
    )
    op.create_index(
        "ix_phase_23_unit_economics_preview_audit_action",
        "phase_23_unit_economics_preview",
        ["audit_action"],
        unique=False,
    )

    # ── JSONB GIN index for tag_propagation (CR 12-5 D-14 verbatim) ──────
    op.execute(
        "CREATE INDEX ix_phase_23_unit_economics_preview_tag_propagation_gin "
        "ON phase_23_unit_economics_preview USING gin (tag_propagation);"
    )

    # ── JSONB GIN index for margin_analysis_preview_data ─────────────────
    op.execute(
        "CREATE INDEX ix_phase_23_unit_economics_preview_margin_data_gin "
        "ON phase_23_unit_economics_preview USING gin (margin_analysis_preview_data);"
    )

    # ── Composite index for fast tenant+period+preview_type lookups ──────
    op.create_index(
        "ix_phase_23_unit_economics_preview_tenant_period_type",
        "phase_23_unit_economics_preview",
        ["tenant_id", "period_key", "preview_type"],
        unique=False,
    )

    # ── RLS policy (CR 0-2 verbatim) ─────────────────────────────────────
    op.execute(
        "ALTER TABLE phase_23_unit_economics_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        "CREATE POLICY tenant_isolation_phase_23_unit_economics_preview "
        "ON phase_23_unit_economics_preview USING ("
        "tenant_id = current_setting('app.tenant_id', true)::uuid"
        ");"
    )


def downgrade() -> None:
    """Drop RLS policy + 1 preview table."""
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_phase_23_unit_economics_preview "
        "ON phase_23_unit_economics_preview;"
    )
    op.execute(
        "ALTER TABLE phase_23_unit_economics_preview DISABLE ROW LEVEL SECURITY;"
    )
    op.drop_index(
        "ix_phase_23_unit_economics_preview_tenant_period_type",
        table_name="phase_23_unit_economics_preview",
    )
    op.drop_index(
        "ix_phase_23_unit_economics_preview_margin_data_gin",
        table_name="phase_23_unit_economics_preview",
    )
    op.drop_index(
        "ix_phase_23_unit_economics_preview_tag_propagation_gin",
        table_name="phase_23_unit_economics_preview",
    )
    op.drop_index(
        "ix_phase_23_unit_economics_preview_audit_action",
        table_name="phase_23_unit_economics_preview",
    )
    op.drop_index(
        "ix_phase_23_unit_economics_preview_tenant_period",
        table_name="phase_23_unit_economics_preview",
    )
    op.drop_table("phase_23_unit_economics_preview")
