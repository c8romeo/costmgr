"""Phase 21 wire — alembic 0053 phase_21_reserved_capacity_planning.

Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
territory (PRD §F37 + AD-49 (g) decision).

This migration creates 8 NEW tables + 1 preview table for Phase 21
FinOps Reserved Capacity Planning wire. All tables carry tenant_id
selector + RLS policies + CHECK constraints + UNIQUE indexes.

Tables:
1. phase_21_reserved_capacity_demand_forecast (16 cols, UNIQUE per scope+period)
2. phase_21_reserved_capacity_plan (18 cols, INDEX per period)
3. phase_21_commitment_recommendation (17 cols, INDEX per tenant+status)
4. phase_21_reserved_capacity_orchestration (19 cols, INDEX per cadence)
5. phase_21_scheduled_reserved_capacity_dispatch (11 cols, INDEX per schedule)
6. phase_21_reserved_capacity_kpi_refresh (12 cols, INDEX per tenant+period)
7. phase_21_reserved_capacity_commitment_log (12 cols, INDEX per tenant)
8. phase_21_reserved_capacity_viewer (8 cols, UNIQUE per user)
+ 1 preview table:
9. phase_21_orchestration_preview

5-module composition layer (Phase 13 forecast + Phase 14 optimization +
Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud) →
single demand_forecast_id + capacity_plan_id +
commitment_recommendation_id + orchestration_id.

6 reserved_capacity_tier (1y_no_upfront + 1y_partial_upfront +
1y_all_upfront + 3y_no_upfront + 3y_partial_upfront +
3y_all_upfront) + 4 execution_strategy + 4 cadence schedule KST
pytz (daily 02:00 + weekly Mon 03:00 + monthly 1st-day 04:00 +
quarterly 1st-day 05:00).

CR lessons applied:
- CR 0-2 RLS — every table tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~20 carry-over: phase_11_finops_* ~ phase_20_finops_* tables
RLS 정합 보존.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0053_phase_21_reserved_capacity_planning"
down_revision = "0052_phase_20_multi_cloud_unified_reconciliation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 8 NEW tables + 1 preview table with RLS + indexes."""

    # ── 1. phase_21_reserved_capacity_demand_forecast ──
    op.create_table(
        "phase_21_reserved_capacity_demand_forecast",
        sa.Column("demand_forecast_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("industry", sa.Text, nullable=False),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="{}"),
        sa.Column("forecasted_demand_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("confidence_interval_low_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("confidence_interval_high_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("seasonal_factor", sa.Numeric(5, 2), nullable=False, server_default="1.0"),
        sa.Column("growth_rate_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("five_module_attribution", JSONB, nullable=False, server_default="{}"),
        sa.Column("confidence_pct", sa.Numeric(5, 2), nullable=False, server_default="80.0"),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "period_key", "industry",
            name="uq_phase_21_reserved_capacity_demand_forecast_scope_period",
        ),
        sa.CheckConstraint(
            "industry IN ('manufacturing', 'service', 'manufacturing_service', 'manufacturing_service_other')",
            name="ck_phase_21_reserved_capacity_demand_forecast_industry",
        ),
    )
    op.create_index(
        "ix_phase_21_reserved_capacity_demand_forecast_tenant_period",
        "phase_21_reserved_capacity_demand_forecast",
        ["tenant_id", "period_key"],
    )

    # ── 2. phase_21_reserved_capacity_plan ──
    op.create_table(
        "phase_21_reserved_capacity_plan",
        sa.Column("capacity_plan_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("demand_forecast_id", UUID(as_uuid=True), nullable=False),
        sa.Column("industry", sa.Text, nullable=False),
        sa.Column("recommended_tier", sa.Text, nullable=False),
        sa.Column("break_even_utilization_pct", sa.Numeric(5, 2), nullable=False, server_default="70.0"),
        sa.Column("capacity_headroom_pct", sa.Numeric(5, 2), nullable=False, server_default="15.0"),
        sa.Column("target_reserved_capacity_units", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estimated_savings_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("estimated_savings_pct", sa.Numeric(5, 2), nullable=False, server_default="5.0"),
        sa.Column("minimum_savings_krw_threshold", sa.Numeric(20, 2), nullable=False, server_default="1000000"),
        sa.Column("commitment_term_months", sa.Integer, nullable=False, server_default="12"),
        sa.Column("upfront_payment_option", sa.Text, nullable=False, server_default="no_upfront"),
        sa.Column("capacity_plan_status", sa.Text, nullable=False, server_default="proposed"),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "recommended_tier IN ('1y_no_upfront', '1y_partial_upfront', '1y_all_upfront', '3y_no_upfront', '3y_partial_upfront', '3y_all_upfront')",
            name="ck_phase_21_reserved_capacity_plan_tier",
        ),
        sa.CheckConstraint(
            "upfront_payment_option IN ('no_upfront', 'partial_upfront', 'all_upfront')",
            name="ck_phase_21_reserved_capacity_plan_upfront",
        ),
        sa.CheckConstraint(
            "capacity_plan_status IN ('proposed', 'approved', 'executed', 'rejected')",
            name="ck_phase_21_reserved_capacity_plan_status",
        ),
        sa.CheckConstraint(
            "commitment_term_months IN (12, 36)",
            name="ck_phase_21_reserved_capacity_plan_term",
        ),
    )
    op.create_index(
        "ix_phase_21_reserved_capacity_plan_tenant_period",
        "phase_21_reserved_capacity_plan",
        ["tenant_id", "period_key"],
    )
    op.create_index(
        "ix_phase_21_reserved_capacity_plan_demand_forecast_id",
        "phase_21_reserved_capacity_plan",
        ["demand_forecast_id"],
    )

    # ── 3. phase_21_commitment_recommendation ──
    op.create_table(
        "phase_21_commitment_recommendation",
        sa.Column("commitment_recommendation_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("capacity_plan_id", UUID(as_uuid=True), nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("industry", sa.Text, nullable=False),
        sa.Column("recommended_tier", sa.Text, nullable=False),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("execution_strategy", sa.Text, nullable=False, server_default="manual_review_required"),
        sa.Column("high_value_flag", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("requires_2fa_challenge", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("estimated_annual_savings_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("estimated_annual_savings_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("confidence_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("risk_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "execution_strategy IN ('auto_execute_ready', 'manual_review_required', 'owner_approval_required', 'low_confidence')",
            name="ck_phase_21_commitment_recommendation_strategy",
        ),
    )
    op.create_index(
        "ix_phase_21_commitment_recommendation_tenant_period",
        "phase_21_commitment_recommendation",
        ["tenant_id", "period_key"],
    )
    op.create_index(
        "ix_phase_21_commitment_recommendation_capacity_plan_id",
        "phase_21_commitment_recommendation",
        ["capacity_plan_id"],
    )

    # ── 4. phase_21_reserved_capacity_orchestration ──
    op.create_table(
        "phase_21_reserved_capacity_orchestration",
        sa.Column("orchestration_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="[]"),
        sa.Column("composition_step_chain", JSONB, nullable=False, server_default="[]"),
        sa.Column("composition_step_results", JSONB, nullable=False, server_default="{}"),
        sa.Column("cadence", sa.Text, nullable=False, server_default="weekly"),
        sa.Column("cadence_hour_kst", sa.Integer, nullable=False, server_default="3"),
        sa.Column("cadence_minute_kst", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("dry_run", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("commitment_recommendation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("capacity_plan_id", UUID(as_uuid=True), nullable=True),
        sa.Column("demand_forecast_id", UUID(as_uuid=True), nullable=True),
        sa.Column("orchestration_status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("high_value_flag", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("owner_approval_required", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "cadence IN ('daily', 'weekly', 'monthly', 'quarterly')",
            name="ck_phase_21_reserved_capacity_orchestration_cadence",
        ),
        sa.CheckConstraint(
            "orchestration_status IN ('pending', 'running', 'completed', 'failed', 'dry_run')",
            name="ck_phase_21_reserved_capacity_orchestration_status",
        ),
    )
    op.create_index(
        "ix_phase_21_reserved_capacity_orchestration_tenant_cadence",
        "phase_21_reserved_capacity_orchestration",
        ["tenant_id", "cadence"],
    )
    op.create_index(
        "ix_phase_21_reserved_capacity_orchestration_tenant_period",
        "phase_21_reserved_capacity_orchestration",
        ["tenant_id", "period_key"],
    )

    # ── 5. phase_21_scheduled_reserved_capacity_dispatch ──
    op.create_table(
        "phase_21_scheduled_reserved_capacity_dispatch",
        sa.Column("dispatch_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("dispatch_schedule", sa.Text, nullable=False),
        sa.Column("cron_expression", sa.Text, nullable=False),
        sa.Column("recipient_strategy", sa.Text, nullable=False),
        sa.Column("recipient_list", JSONB, nullable=False, server_default="{}"),
        sa.Column("orchestration_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="scheduled"),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "dispatch_schedule IN ('daily', 'weekly', 'monthly', 'quarterly')",
            name="ck_phase_21_scheduled_reserved_capacity_dispatch_schedule",
        ),
        sa.CheckConstraint(
            "recipient_strategy IN ('owner_only', 'executive', 'finops_team', 'custom_recipients')",
            name="ck_phase_21_scheduled_reserved_capacity_dispatch_recipient_strategy",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_phase_21_scheduled_reserved_capacity_dispatch_status",
        ),
    )
    op.create_index(
        "ix_phase_21_scheduled_reserved_capacity_dispatch_tenant_schedule",
        "phase_21_scheduled_reserved_capacity_dispatch",
        ["tenant_id", "dispatch_schedule"],
    )

    # ── 6. phase_21_reserved_capacity_kpi_refresh ──
    op.create_table(
        "phase_21_reserved_capacity_kpi_refresh",
        sa.Column("kpi_refresh_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("industry", sa.Text, nullable=False),
        sa.Column("total_reserved_capacity_units", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_estimated_savings_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("average_break_even_utilization_pct", sa.Numeric(5, 2), nullable=False, server_default="70.0"),
        sa.Column("high_value_commitment_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("low_confidence_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("refresh_status", sa.Text, nullable=False, server_default="success"),
        sa.Column("refreshed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
    )
    op.create_index(
        "ix_phase_21_reserved_capacity_kpi_refresh_tenant_period",
        "phase_21_reserved_capacity_kpi_refresh",
        ["tenant_id", "period_key"],
    )

    # ── 7. phase_21_reserved_capacity_commitment_log ──
    op.create_table(
        "phase_21_reserved_capacity_commitment_log",
        sa.Column("log_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("commitment_recommendation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("industry", sa.Text, nullable=False),
        sa.Column("trigger_type", sa.Text, nullable=False, server_default="auto"),
        sa.Column("trigger_status", sa.Text, nullable=False, server_default="triggered"),
        sa.Column("execution_strategy", sa.Text, nullable=False),
        sa.Column("dispatched_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("commitment_savings_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("monthly_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("expired_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "trigger_type IN ('auto', 'manual', 'override', 'dry_run')",
            name="ck_phase_21_reserved_capacity_commitment_log_trigger_type",
        ),
        sa.CheckConstraint(
            "trigger_status IN ('triggered', 'completed', 'failed', 'guard_rejected', 'dry_run_previewed')",
            name="ck_phase_21_reserved_capacity_commitment_log_trigger_status",
        ),
    )
    op.create_index(
        "ix_phase_21_reserved_capacity_commitment_log_tenant_status",
        "phase_21_reserved_capacity_commitment_log",
        ["tenant_id", "trigger_status"],
    )

    # ── 8. phase_21_reserved_capacity_viewer ──
    op.create_table(
        "phase_21_reserved_capacity_viewer",
        sa.Column("viewer_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text, nullable=False, server_default="reserved_capacity_viewer"),
        sa.Column("granted_by", UUID(as_uuid=True), nullable=True),
        sa.Column("granted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "user_id",
            name="uq_phase_21_reserved_capacity_viewer_tenant_user",
        ),
        sa.CheckConstraint(
            "role IN ('reserved_capacity_viewer')",
            name="ck_phase_21_reserved_capacity_viewer_role",
        ),
    )

    # ── 9. phase_21_orchestration_preview (dry-run output) ──
    op.create_table(
        "phase_21_orchestration_preview",
        sa.Column("preview_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("preview_type", sa.Text, nullable=False, server_default="orchestration"),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("cadence", sa.Text, nullable=False, server_default="weekly"),
        sa.Column("composition_step_chain", JSONB, nullable=False, server_default="[]"),
        sa.Column("composition_step_results", JSONB, nullable=False, server_default="{}"),
        sa.Column("preview_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("audit_action", sa.Text, nullable=False, server_default="reserved_capacity_dry_run_executed"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
    )

    # ── RLS policies (CR 0-2 verbatim) ──
    for table_name in (
        "phase_21_reserved_capacity_demand_forecast",
        "phase_21_reserved_capacity_plan",
        "phase_21_commitment_recommendation",
        "phase_21_reserved_capacity_orchestration",
        "phase_21_scheduled_reserved_capacity_dispatch",
        "phase_21_reserved_capacity_kpi_refresh",
        "phase_21_reserved_capacity_commitment_log",
        "phase_21_reserved_capacity_viewer",
        "phase_21_orchestration_preview",
    ):
        op.execute(
            f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"
        )
        op.execute(
            f"CREATE POLICY tenant_isolation_{table_name} "
            f"ON {table_name} USING ("
            f"tenant_id = current_setting('app.tenant_id', true)::uuid"
            f");"
        )


def downgrade() -> None:
    """Drop RLS policies + 9 tables."""
    for table_name in (
        "phase_21_reserved_capacity_demand_forecast",
        "phase_21_reserved_capacity_plan",
        "phase_21_commitment_recommendation",
        "phase_21_reserved_capacity_orchestration",
        "phase_21_scheduled_reserved_capacity_dispatch",
        "phase_21_reserved_capacity_kpi_refresh",
        "phase_21_reserved_capacity_commitment_log",
        "phase_21_reserved_capacity_viewer",
        "phase_21_orchestration_preview",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")
        op.drop_table(table_name)
