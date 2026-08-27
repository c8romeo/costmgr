"""Phase 24 wire — alembic 0056 phase_24_budget_planning.

Phase 24 wire (cj-style 169번째) — FinOps Budget Planning pre-allocation
layer territory (PRD §F40 + AD-52 (a)~(g) 7 sub-decisions).

This migration creates ONLY 1 NEW preview table for Phase 24 FinOps
Budget Planning wire. Phase 24 derives budget_planning metrics from
Phase 22 allocation_lines + Phase 23 unit_economics_results ledger
data on-the-fly (no persistent per-plan/per-allocation/per-approval
tables). The preview table stores idempotency-key UNIQUE snapshots of
dry-run results.

Phase 24 differs from Phase 23 in that:
- Phase 23 stores 1 preview only (derived metrics computed on-the-fly)
- Phase 24 stores 1 preview only (pre-allocation layer computed on-the-fly)
- This minimizes storage footprint + aligns with D-FINOPS-13 honestly
  DEFER (multi-currency FX + zero-based budgeting + incremental budgeting
  + envelope budgeting + scenario A/B testing + per-budget approval
  override all honestly DEFER to future Phase 24.x)

Tables:
1. phase_24_budget_planning_preview (preview snapshot for dry-run + idempotency)
   - preview_id (UUID PK)
   - tenant_id (UUID, indexed)
   - preview_type (TEXT, default='budget_planning_dry_run')
   - period_key (TEXT)
   - budget_plan_preview_data (JSONB)
   - budget_allocation_preview_data (JSONB)
   - budget_vs_actual_preview_data (JSONB)
   - budget_alert_preview_data (JSONB)
   - audit_action (TEXT, default='budget_planning_dry_run_executed')
   - idempotency_key (TEXT, UNIQUE per tenant_id + period_key + preview_type)
   - source_attribution (JSONB, GIN-indexed for 5-dim source attribution
     queries from Phase 22 allocation_lines + Phase 23
     unit_economics_results ledger data)
   - computed_at (TIMESTAMPTZ, default NOW())
   - trace_id (TEXT)

5-NEW-module composition layer (budget_plan_engine + budget_allocation +
budget_approval_workflow + budget_vs_actual + budget_alert) derived
from Phase 22 allocation_lines + Phase 23 unit_economics_results ledger
data via 5-dim cross-join + 5-dim weighted allocation + sequential
approval chain + Epic 12 2FA 챌린지 mandatory (high-value 10M KRW/year).

5-dim cross-join (cost_center 0.30 + department 0.25 + business_unit
0.20 + tag 0.15 + tenant 0.10) + 4 cadence schedule KST pytz
(daily_lifecycle 04:00 + weekly_variance 04:30 + monthly_rollover
05:00 + quarterly_review 05:30) + dry-run mode + Epic 12 2FA 챌린지
mandatory (high-value 10M KRW/year) + 8 NEW audit actions + 16 NEW
typed exceptions + D-FINOPS-13 honestly DEFER (multi-currency FX +
zero-based budgeting + incremental budgeting + envelope budgeting +
scenario A/B testing + per-budget approval override).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~23 carry-over: phase_11_finops_* ~ phase_23_unit_economics_*
tables RLS 정합 보존.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0056_phase_24_budget_planning"
down_revision = "0055_phase_23_unit_economics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 1 NEW preview table with RLS + indexes.

    Phase 24 introduces ONLY 1 preview table — pre-allocation layer is
    computed on-the-fly from Phase 22 allocation_lines + Phase 23
    unit_economics_results ledger data. The preview table is for
    materialized snapshot caching + idempotency_key UNIQUE constraint +
    source_attribution GIN-indexed JSONB for 5-dim cross-join source
    attribution queries.
    """

    # ── 1. phase_24_budget_planning_preview ──
    op.create_table(
        "phase_24_budget_planning_preview",
        sa.Column("preview_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "preview_type",
            sa.Text,
            nullable=False,
            server_default="budget_planning_dry_run",
        ),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column(
            "budget_plan_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "budget_allocation_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "budget_vs_actual_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "budget_alert_preview_data",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "audit_action",
            sa.Text,
            nullable=False,
            server_default="budget_planning_dry_run_executed",
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
            name="uq_phase_24_budget_planning_preview_tenant_idempotency",
        ),
        sa.CheckConstraint(
            "preview_type IN ("
            "'budget_planning_dry_run', "
            "'budget_allocation_dry_run', "
            "'budget_vs_actual_dry_run', "
            "'budget_alert_dry_run'"
            ")",
            name="ck_phase_24_budget_planning_preview_type",
        ),
        sa.CheckConstraint(
            "audit_action IN ("
            "'budget_plan_created', "
            "'budget_plan_updated', "
            "'budget_plan_submitted_for_approval', "
            "'budget_plan_approved', "
            "'budget_plan_rejected', "
            "'budget_allocation_verified', "
            "'budget_alert_triggered', "
            "'budget_planning_dry_run_executed'"
            ")",
            name="ck_phase_24_budget_planning_preview_audit_action",
        ),
    )

    # ── Indexes (Phase 23 verbatim pattern) ──────────────────────────────
    op.create_index(
        "ix_phase_24_budget_planning_preview_tenant_period",
        "phase_24_budget_planning_preview",
        ["tenant_id", "period_key"],
        unique=False,
    )
    op.create_index(
        "ix_phase_24_budget_planning_preview_audit_action",
        "phase_24_budget_planning_preview",
        ["audit_action"],
        unique=False,
    )

    # ── JSONB GIN index for source_attribution (5-dim cross-join ref) ────
    op.execute(
        "CREATE INDEX ix_phase_24_budget_planning_preview_source_attribution_gin "
        "ON phase_24_budget_planning_preview USING gin (source_attribution);"
    )

    # ── JSONB GIN index for budget_vs_actual_preview_data ────────────────
    op.execute(
        "CREATE INDEX ix_phase_24_budget_planning_preview_vs_actual_data_gin "
        "ON phase_24_budget_planning_preview USING gin (budget_vs_actual_preview_data);"
    )

    # ── Composite index for fast tenant+period+preview_type lookups ──────
    op.create_index(
        "ix_phase_24_budget_planning_preview_tenant_period_type",
        "phase_24_budget_planning_preview",
        ["tenant_id", "period_key", "preview_type"],
        unique=False,
    )

    # ── RLS policy (CR 0-2 verbatim) ─────────────────────────────────────
    op.execute(
        "ALTER TABLE phase_24_budget_planning_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        "CREATE POLICY tenant_isolation_phase_24_budget_planning_preview "
        "ON phase_24_budget_planning_preview USING ("
        "tenant_id = current_setting('app.tenant_id', true)::uuid"
        ");"
    )


def downgrade() -> None:
    """Drop RLS policy + 1 preview table."""
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_phase_24_budget_planning_preview "
        "ON phase_24_budget_planning_preview;"
    )
    op.execute(
        "ALTER TABLE phase_24_budget_planning_preview DISABLE ROW LEVEL SECURITY;"
    )
    op.drop_index(
        "ix_phase_24_budget_planning_preview_tenant_period_type",
        table_name="phase_24_budget_planning_preview",
    )
    op.drop_index(
        "ix_phase_24_budget_planning_preview_vs_actual_data_gin",
        table_name="phase_24_budget_planning_preview",
    )
    op.drop_index(
        "ix_phase_24_budget_planning_preview_source_attribution_gin",
        table_name="phase_24_budget_planning_preview",
    )
    op.drop_index(
        "ix_phase_24_budget_planning_preview_audit_action",
        table_name="phase_24_budget_planning_preview",
    )
    op.drop_index(
        "ix_phase_24_budget_planning_preview_tenant_period",
        table_name="phase_24_budget_planning_preview",
    )
    op.drop_table("phase_24_budget_planning_preview")
