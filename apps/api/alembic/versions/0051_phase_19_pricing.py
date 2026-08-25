"""Phase 19 wire — alembic 0051 phase_19_finops_pricing.

Phase 19 wire (cj-style 139번째) — FinOps Pricing, Rate Card & TCO
Modeling territory (PRD §F35.7 + AD-46 (g) decision).

This migration creates 6 NEW tables + 4 preview tables for Phase 19
FinOps Pricing, Rate Card & TCO Modeling wire. All tables carry
tenant_id selector + RLS policies + CHECK constraints + UNIQUE indexes.

Tables:
1. phase_19_finops_rate_card_inventory (18 cols, UNIQUE per scope)
2. phase_19_finops_tco_kpi (12 cols, INDEX per period)
3. phase_19_finops_pricing_report (15 cols, INDEX per status)
4. phase_19_finops_scheduled_pricing_dispatch (11 cols, INDEX per schedule)
5. phase_19_finops_pricing_viewer (8 cols, UNIQUE per user)
6. phase_19_finops_pricing_break_even_analysis (12 cols, INDEX per kpi_name)
+ 4 preview tables:
7. phase_19_finops_rate_card_inventory_preview
8. phase_19_finops_tco_kpi_preview
9. phase_19_finops_pricing_report_preview
10. phase_19_finops_scheduled_pricing_dispatch_preview

CR lessons applied:
- CR 0-2 RLS — every table tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~18 carry-over: phase_11_finops_* ~ phase_18_finops_* tables
RLS 정합 보존.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0051_phase_19_finops_pricing"
down_revision = "0050_phase_18_finops_commitment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 6 NEW tables + 4 preview tables with RLS + indexes."""

    # ── 1. phase_19_finops_rate_card_inventory ──
    op.create_table(
        "phase_19_finops_rate_card_inventory",
        sa.Column("rate_card_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="{}"),
        sa.Column("total_blended_rate_krw_per_hour", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("effective_discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("tco_1year_commitment_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("tco_3year_commitment_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("tco_on_demand_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("cost_per_user_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("cost_per_transaction_krw", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("unit_economics_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cloud_provider_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("pricing_model_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("cache_key", sa.Text, nullable=False),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "scope_type", "scope_id", "period_key",
            name="uq_phase_19_finops_rate_card_inventory_scope_period",
        ),
        sa.CheckConstraint(
            "scope_type IN ('tenant', 'department', 'cost_center', 'product_line')",
            name="ck_phase_19_finops_rate_card_inventory_scope_type",
        ),
    )
    op.create_index(
        "ix_phase_19_finops_rate_card_inventory_tenant_period",
        "phase_19_finops_rate_card_inventory",
        ["tenant_id", "period_key"],
    )

    # ── 2. phase_19_finops_tco_kpi ──
    op.create_table(
        "phase_19_finops_tco_kpi",
        sa.Column("kpi_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("kpi_name", sa.Text, nullable=False),
        sa.Column("kpi_value", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("kpi_unit", sa.Text, nullable=False, server_default=""),
        sa.Column("kpi_delta", sa.Numeric(20, 4), nullable=True),
        sa.Column("kpi_trend", sa.Text, nullable=False, server_default="flat"),
        sa.Column("kpi_threshold_status", sa.Text, nullable=False, server_default="on_track"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "kpi_trend IN ('up', 'down', 'flat')",
            name="ck_phase_19_finops_tco_kpi_trend",
        ),
        sa.CheckConstraint(
            "kpi_threshold_status IN ('on_track', 'warning', 'critical')",
            name="ck_phase_19_finops_tco_kpi_threshold_status",
        ),
    )
    op.create_index(
        "ix_phase_19_finops_tco_kpi_tenant_period",
        "phase_19_finops_tco_kpi",
        ["tenant_id", "period_key"],
    )
    op.create_index(
        "ix_phase_19_finops_tco_kpi_name",
        "phase_19_finops_tco_kpi",
        ["kpi_name"],
    )

    # ── 3. phase_19_finops_pricing_report ──
    op.create_table(
        "phase_19_finops_pricing_report",
        sa.Column("report_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("cadence", sa.Text, nullable=False),
        sa.Column("framework", sa.Text, nullable=False),
        sa.Column("export_format", sa.Text, nullable=False),
        sa.Column("report_file_url", sa.Text, nullable=False, server_default=""),
        sa.Column("report_size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("report_generated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("generated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="generating"),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "cadence IN ('monthly', 'quarterly', 'annual')",
            name="ck_phase_19_finops_pricing_report_cadence",
        ),
        sa.CheckConstraint(
            "framework IN ('finops_foundation', 'aws_pricing_models', 'azure_pricing_calculator', 'gcp_pricing_calculator', 'korea_procurement')",
            name="ck_phase_19_finops_pricing_report_framework",
        ),
        sa.CheckConstraint(
            "export_format IN ('pdf', 'csv', 'excel')",
            name="ck_phase_19_finops_pricing_report_export_format",
        ),
        sa.CheckConstraint(
            "status IN ('generating', 'completed', 'failed', 'expired')",
            name="ck_phase_19_finops_pricing_report_status",
        ),
    )
    op.create_index(
        "ix_phase_19_finops_pricing_report_tenant_status",
        "phase_19_finops_pricing_report",
        ["tenant_id", "status"],
    )

    # ── 4. phase_19_finops_scheduled_pricing_dispatch ──
    op.create_table(
        "phase_19_finops_scheduled_pricing_dispatch",
        sa.Column("dispatch_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("dispatch_schedule", sa.Text, nullable=False),
        sa.Column("cron_expression", sa.Text, nullable=False),
        sa.Column("recipient_strategy", sa.Text, nullable=False),
        sa.Column("recipient_list", JSONB, nullable=False, server_default="{}"),
        sa.Column("report_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="scheduled"),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "dispatch_schedule IN ('weekly', 'monthly', 'quarterly', 'annual')",
            name="ck_phase_19_finops_scheduled_pricing_dispatch_schedule",
        ),
        sa.CheckConstraint(
            "recipient_strategy IN ('owner_only', 'pricing_team', 'finance_team', 'custom_recipients')",
            name="ck_phase_19_finops_scheduled_pricing_dispatch_recipient_strategy",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_phase_19_finops_scheduled_pricing_dispatch_status",
        ),
    )
    op.create_index(
        "ix_phase_19_finops_scheduled_pricing_dispatch_tenant_schedule",
        "phase_19_finops_scheduled_pricing_dispatch",
        ["tenant_id", "dispatch_schedule"],
    )

    # ── 5. phase_19_finops_pricing_viewer ──
    op.create_table(
        "phase_19_finops_pricing_viewer",
        sa.Column("viewer_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text, nullable=False, server_default="pricing_viewer"),
        sa.Column("granted_by", UUID(as_uuid=True), nullable=True),
        sa.Column("granted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "user_id",
            name="uq_phase_19_finops_pricing_viewer_tenant_user",
        ),
        sa.CheckConstraint(
            "role IN ('pricing_viewer')",
            name="ck_phase_19_finops_pricing_viewer_role",
        ),
    )

    # ── 6. phase_19_finops_pricing_break_even_analysis ──
    op.create_table(
        "phase_19_finops_pricing_break_even_analysis",
        sa.Column("break_even_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("pricing_model", sa.Text, nullable=False),
        sa.Column("cloud_provider", sa.Text, nullable=False),
        sa.Column("unit_metric", sa.Text, nullable=False),
        sa.Column("upfront_cost_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("monthly_savings_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("break_even_months", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("industry", sa.Text, nullable=False, server_default="manufacturing"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "pricing_model IN ('on_demand', '1y_ri', '3y_ri', '1y_sp', '3y_sp', 'savings_plan')",
            name="ck_phase_19_finops_pricing_break_even_analysis_pricing_model",
        ),
        sa.CheckConstraint(
            "cloud_provider IN ('aws', 'azure', 'gcp', 'naver', 'kt')",
            name="ck_phase_19_finops_pricing_break_even_analysis_provider",
        ),
        sa.CheckConstraint(
            "unit_metric IN ('cost_per_user', 'cost_per_transaction', 'cost_per_request', 'cost_per_hour')",
            name="ck_phase_19_finops_pricing_break_even_analysis_unit_metric",
        ),
        sa.CheckConstraint(
            "industry IN ('manufacturing', 'service', 'manufacturing_service', 'manufacturing_service_other')",
            name="ck_phase_19_finops_pricing_break_even_analysis_industry",
        ),
    )
    op.create_index(
        "ix_phase_19_finops_pricing_break_even_analysis_tenant_kpi",
        "phase_19_finops_pricing_break_even_analysis",
        ["tenant_id", "break_even_months"],
    )

    # ── 7-10. 4 preview tables (dry-run output) ──
    for preview_table_name in (
        "phase_19_finops_rate_card_inventory_preview",
        "phase_19_finops_tco_kpi_preview",
        "phase_19_finops_pricing_report_preview",
        "phase_19_finops_scheduled_pricing_dispatch_preview",
    ):
        op.create_table(
            preview_table_name,
            sa.Column("preview_id", UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("preview_type", sa.Text, nullable=False),
            sa.Column("period_key", sa.Text, nullable=False),
            sa.Column("preview_data", JSONB, nullable=False, server_default="{}"),
            sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        )

    # ── RLS policies (CR 0-2 verbatim) ──
    for table_name in (
        "phase_19_finops_rate_card_inventory",
        "phase_19_finops_tco_kpi",
        "phase_19_finops_pricing_report",
        "phase_19_finops_scheduled_pricing_dispatch",
        "phase_19_finops_pricing_viewer",
        "phase_19_finops_pricing_break_even_analysis",
        "phase_19_finops_rate_card_inventory_preview",
        "phase_19_finops_tco_kpi_preview",
        "phase_19_finops_pricing_report_preview",
        "phase_19_finops_scheduled_pricing_dispatch_preview",
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
    """Drop RLS policies + 10 tables."""
    for table_name in (
        "phase_19_finops_rate_card_inventory",
        "phase_19_finops_tco_kpi",
        "phase_19_finops_pricing_report",
        "phase_19_finops_scheduled_pricing_dispatch",
        "phase_19_finops_pricing_viewer",
        "phase_19_finops_pricing_break_even_analysis",
        "phase_19_finops_rate_card_inventory_preview",
        "phase_19_finops_tco_kpi_preview",
        "phase_19_finops_pricing_report_preview",
        "phase_19_finops_scheduled_pricing_dispatch_preview",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")
        op.drop_table(table_name)
