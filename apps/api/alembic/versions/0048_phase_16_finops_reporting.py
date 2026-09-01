"""Phase 16 wire — alembic 0048 phase_16_finops_reporting.

Phase 16 wire (cj-style 127번째) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.7 + AD-43 (g) decision).

This migration creates 6 NEW tables + 4 preview tables for Phase 16
FinOps Reporting & Executive Dashboard wire. All tables carry
tenant_id selector + RLS policies + CHECK constraints + UNIQUE indexes.

Tables:
1. phase_16_finops_executive_rollup (17 cols, UNIQUE per scope)
2. phase_16_finops_cross_module_kpi (12 cols, INDEX per period)
3. phase_16_finops_executive_report (13 cols, INDEX per status)
4. phase_16_finops_scheduled_dispatch (11 cols, INDEX per schedule)
5. phase_16_finops_executive_viewer (8 cols, UNIQUE per user)
6. phase_16_finops_recipient_strategy (9 cols, UNIQUE per strategy)
+ 4 preview tables:
7. phase_16_finops_executive_rollup_preview
8. phase_16_finops_cross_module_kpi_preview
9. phase_16_finops_executive_report_preview
10. phase_16_finops_scheduled_dispatch_preview

CR lessons applied:
- CR 0-2 RLS — every table tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~15 carry-over: phase_11_finops_* ~ phase_15_finops_* tables
RLS 정합 보존.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0048_phase_16_finops_reporting"
down_revision = "0047_phase_15_tag_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 6 NEW tables + 4 preview tables with RLS + indexes."""

    # ── 1. phase_16_finops_executive_rollup ──
    op.create_table(
        "phase_16_finops_executive_rollup",
        sa.Column("rollup_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("showback_total_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("anomaly_count_30d", sa.Integer, nullable=False, server_default="0"),
        sa.Column("forecast_projection_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column(
            "optimization_savings_krw", sa.Numeric(20, 2), nullable=False, server_default="0"
        ),
        sa.Column("tag_compliance_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("idle_cost_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("department_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("cost_center_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("resource_type_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("cache_key", sa.Text, nullable=False),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id",
            "scope_type",
            "scope_id",
            "period_key",
            name="uq_phase_16_finops_executive_rollup_scope_period",
        ),
        sa.CheckConstraint(
            "scope_type IN ('tenant', 'department', 'cost_center', 'product_line')",
            name="ck_phase_16_finops_executive_rollup_scope_type",
        ),
    )
    op.create_index(
        "ix_phase_16_finops_executive_rollup_tenant_period",
        "phase_16_finops_executive_rollup",
        ["tenant_id", "period_key"],
    )

    # ── 2. phase_16_finops_cross_module_kpi ──
    op.create_table(
        "phase_16_finops_cross_module_kpi",
        sa.Column("kpi_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("kpi_name", sa.Text, nullable=False),
        sa.Column("kpi_value", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("kpi_unit", sa.Text, nullable=False, server_default=""),
        sa.Column("kpi_delta", sa.Numeric(20, 2), nullable=True),
        sa.Column("kpi_trend", sa.Text, nullable=False, server_default="flat"),
        sa.Column("kpi_threshold_status", sa.Text, nullable=False, server_default="on_track"),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "kpi_trend IN ('up', 'down', 'flat')",
            name="ck_phase_16_finops_cross_module_kpi_trend",
        ),
        sa.CheckConstraint(
            "kpi_threshold_status IN ('on_track', 'warning', 'critical')",
            name="ck_phase_16_finops_cross_module_kpi_threshold_status",
        ),
    )
    op.create_index(
        "ix_phase_16_finops_cross_module_kpi_tenant_period",
        "phase_16_finops_cross_module_kpi",
        ["tenant_id", "period_key"],
    )
    op.create_index(
        "ix_phase_16_finops_cross_module_kpi_name",
        "phase_16_finops_cross_module_kpi",
        ["kpi_name"],
    )

    # ── 3. phase_16_finops_executive_report ──
    op.create_table(
        "phase_16_finops_executive_report",
        sa.Column("report_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("cadence", sa.Text, nullable=False),
        sa.Column("export_format", sa.Text, nullable=False),
        sa.Column("report_file_url", sa.Text, nullable=False, server_default=""),
        sa.Column("report_size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column(
            "report_generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("generated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="generating"),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "cadence IN ('monthly', 'quarterly', 'annual')",
            name="ck_phase_16_finops_executive_report_cadence",
        ),
        sa.CheckConstraint(
            "export_format IN ('pdf', 'csv', 'excel')",
            name="ck_phase_16_finops_executive_report_export_format",
        ),
        sa.CheckConstraint(
            "status IN ('generating', 'completed', 'failed', 'expired')",
            name="ck_phase_16_finops_executive_report_status",
        ),
    )
    op.create_index(
        "ix_phase_16_finops_executive_report_tenant_status",
        "phase_16_finops_executive_report",
        ["tenant_id", "status"],
    )

    # ── 4. phase_16_finops_scheduled_dispatch ──
    op.create_table(
        "phase_16_finops_scheduled_dispatch",
        sa.Column("dispatch_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("dispatch_schedule", sa.Text, nullable=False),
        sa.Column("cron_expression", sa.Text, nullable=False),
        sa.Column("recipient_strategy", sa.Text, nullable=False),
        sa.Column("recipient_list", JSONB, nullable=False, server_default="{}"),
        sa.Column("report_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="scheduled"),
        sa.Column(
            "scheduled_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("last_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "dispatch_schedule IN ('weekly', 'monthly', 'quarterly', 'annual')",
            name="ck_phase_16_finops_scheduled_dispatch_schedule",
        ),
        sa.CheckConstraint(
            "recipient_strategy IN ('owner_only', 'executive_team', 'board_observers', 'custom_recipients')",
            name="ck_phase_16_finops_scheduled_dispatch_recipient_strategy",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_phase_16_finops_scheduled_dispatch_status",
        ),
    )
    op.create_index(
        "ix_phase_16_finops_scheduled_dispatch_tenant_schedule",
        "phase_16_finops_scheduled_dispatch",
        ["tenant_id", "dispatch_schedule"],
    )

    # ── 5. phase_16_finops_executive_viewer ──
    op.create_table(
        "phase_16_finops_executive_viewer",
        sa.Column("viewer_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text, nullable=False, server_default="executive_viewer"),
        sa.Column("granted_by", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "granted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id",
            "user_id",
            name="uq_phase_16_finops_executive_viewer_tenant_user",
        ),
        sa.CheckConstraint(
            "role IN ('executive_viewer')",
            name="ck_phase_16_finops_executive_viewer_role",
        ),
    )

    # ── 6. phase_16_finops_recipient_strategy ──
    op.create_table(
        "phase_16_finops_recipient_strategy",
        sa.Column("recipient_strategy_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("strategy_name", sa.Text, nullable=False),
        sa.Column("recipient_list", JSONB, nullable=False, server_default="{}"),
        sa.Column("delivery_targets", JSONB, nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id",
            "strategy_name",
            name="uq_phase_16_finops_recipient_strategy_tenant_strategy",
        ),
        sa.CheckConstraint(
            "strategy_name IN ('owner_only', 'executive_team', 'board_observers', 'custom_recipients')",
            name="ck_phase_16_finops_recipient_strategy_name",
        ),
    )

    # ── 7-10. 4 preview tables (dry-run output) ──
    for preview_table_name in (
        "phase_16_finops_executive_rollup_preview",
        "phase_16_finops_cross_module_kpi_preview",
        "phase_16_finops_executive_report_preview",
        "phase_16_finops_scheduled_dispatch_preview",
    ):
        op.create_table(
            preview_table_name,
            sa.Column("preview_id", UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("preview_type", sa.Text, nullable=False),
            sa.Column("period_key", sa.Text, nullable=False),
            sa.Column("preview_data", JSONB, nullable=False, server_default="{}"),
            sa.Column(
                "computed_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        )

    # ── RLS policies (CR 0-2 verbatim) ──
    for table_name in (
        "phase_16_finops_executive_rollup",
        "phase_16_finops_cross_module_kpi",
        "phase_16_finops_executive_report",
        "phase_16_finops_scheduled_dispatch",
        "phase_16_finops_executive_viewer",
        "phase_16_finops_recipient_strategy",
        "phase_16_finops_executive_rollup_preview",
        "phase_16_finops_cross_module_kpi_preview",
        "phase_16_finops_executive_report_preview",
        "phase_16_finops_scheduled_dispatch_preview",
    ):
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY tenant_isolation_{table_name} "
            f"ON {table_name} USING ("
            f"tenant_id = current_setting('app.tenant_id', true)::uuid"
            f");"
        )


def downgrade() -> None:
    """Drop RLS policies + 10 tables."""
    for table_name in (
        "phase_16_finops_executive_rollup",
        "phase_16_finops_cross_module_kpi",
        "phase_16_finops_executive_report",
        "phase_16_finops_scheduled_dispatch",
        "phase_16_finops_executive_viewer",
        "phase_16_finops_recipient_strategy",
        "phase_16_finops_executive_rollup_preview",
        "phase_16_finops_cross_module_kpi_preview",
        "phase_16_finops_executive_report_preview",
        "phase_16_finops_scheduled_dispatch_preview",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")
        op.drop_table(table_name)
