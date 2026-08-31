"""Phase 17 wire — alembic 0049 phase_17_finops_sustainability.

Phase 17 wire (cj-style 131번째) — FinOps Sustainability & Carbon Reporting
territory (PRD §F33.7 + AD-44 (g) decision).

This migration creates 6 NEW tables + 4 preview tables for Phase 17
FinOps Sustainability & Carbon Reporting wire. All tables carry
tenant_id selector + RLS policies + CHECK constraints + UNIQUE indexes.

Tables:
1. phase_17_finops_carbon_emissions_rollup (15 cols, UNIQUE per scope)
2. phase_17_finops_sustainability_kpi (12 cols, INDEX per period)
3. phase_17_finops_sustainability_report (15 cols, INDEX per status)
4. phase_17_finops_scheduled_sustainability_dispatch (11 cols, INDEX per schedule)
5. phase_17_finops_sustainability_viewer (8 cols, UNIQUE per user)
6. phase_17_finops_carbon_offset_registry (10 cols, INDEX per registry)
+ 4 preview tables:
7. phase_17_finops_carbon_emissions_rollup_preview
8. phase_17_finops_sustainability_kpi_preview
9. phase_17_finops_sustainability_report_preview
10. phase_17_finops_scheduled_sustainability_dispatch_preview

CR lessons applied:
- CR 0-2 RLS — every table tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~16 carry-over: phase_11_finops_* ~ phase_16_finops_* tables
RLS 정합 보존.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0049_phase_17_finops_sustainability"
down_revision = "0048_phase_16_finops_reporting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 6 NEW tables + 4 preview tables with RLS + indexes."""

    # ── 1. phase_17_finops_carbon_emissions_rollup ──
    op.create_table(
        "phase_17_finops_carbon_emissions_rollup",
        sa.Column("carbon_rollup_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="{}"),
        sa.Column("total_carbon_emissions_kgco2e", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("scope1_emissions_kgco2e", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("scope2_emissions_kgco2e", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("scope3_emissions_kgco2e", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("carbon_offset_kgco2e", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("net_carbon_emissions_kgco2e", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("renewable_energy_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("cache_key", sa.Text, nullable=False),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "scope_type", "scope_id", "period_key",
            name="uq_phase_17_finops_carbon_emissions_rollup_scope_period",
        ),
        sa.CheckConstraint(
            "scope_type IN ('tenant', 'department', 'cost_center', 'product_line')",
            name="ck_phase_17_finops_carbon_emissions_rollup_scope_type",
        ),
    )
    op.create_index(
        "ix_phase_17_finops_carbon_emissions_rollup_tenant_period",
        "phase_17_finops_carbon_emissions_rollup",
        ["tenant_id", "period_key"],
    )

    # ── 2. phase_17_finops_sustainability_kpi ──
    op.create_table(
        "phase_17_finops_sustainability_kpi",
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
            name="ck_phase_17_finops_sustainability_kpi_trend",
        ),
        sa.CheckConstraint(
            "kpi_threshold_status IN ('on_track', 'warning', 'critical')",
            name="ck_phase_17_finops_sustainability_kpi_threshold_status",
        ),
    )
    op.create_index(
        "ix_phase_17_finops_sustainability_kpi_tenant_period",
        "phase_17_finops_sustainability_kpi",
        ["tenant_id", "period_key"],
    )
    op.create_index(
        "ix_phase_17_finops_sustainability_kpi_name",
        "phase_17_finops_sustainability_kpi",
        ["kpi_name"],
    )

    # ── 3. phase_17_finops_sustainability_report ──
    op.create_table(
        "phase_17_finops_sustainability_report",
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
            name="ck_phase_17_finops_sustainability_report_cadence",
        ),
        sa.CheckConstraint(
            "framework IN ('csrd', 'sec_climate', 'eu_taxonomy', 'ifrs_s2', 'kssb')",
            name="ck_phase_17_finops_sustainability_report_framework",
        ),
        sa.CheckConstraint(
            "export_format IN ('pdf', 'csv', 'excel')",
            name="ck_phase_17_finops_sustainability_report_export_format",
        ),
        sa.CheckConstraint(
            "status IN ('generating', 'completed', 'failed', 'expired')",
            name="ck_phase_17_finops_sustainability_report_status",
        ),
    )
    op.create_index(
        "ix_phase_17_finops_sustainability_report_tenant_status",
        "phase_17_finops_sustainability_report",
        ["tenant_id", "status"],
    )

    # ── 4. phase_17_finops_scheduled_sustainability_dispatch ──
    op.create_table(
        "phase_17_finops_scheduled_sustainability_dispatch",
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
            name="ck_phase_17_finops_scheduled_sustainability_dispatch_schedule",
        ),
        sa.CheckConstraint(
            "recipient_strategy IN ('owner_only', 'sustainability_team', 'board_observers', 'custom_recipients')",
            # D-CI-FUNC-9 cj-238 fix: original name was 71 chars, exceeds
            # Postgres NAMEDATALEN-1=63. Shortened to
            # `ck_phase_17_finops_scheduled_sustainability_dispatch_recipient`
            # (62 chars) — drops the redundant `_strategy` suffix because
            # the table name + recipient already conveys intent. CHECK
            # expression unchanged.
            name="ck_phase_17_finops_scheduled_sustainability_dispatch_recipient",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_phase_17_finops_scheduled_sustainability_dispatch_status",
        ),
    )
    op.create_index(
        # D-CI-FUNC-9 cj-238 fix: original name was 68 chars, exceeds
        # Postgres NAMEDATALEN-1=63. Shortened `..._dispatch_tenant_schedule`
        # → `..._dispatch_tenant_idx` (63 chars, exactly at limit). Columns
        # unchanged. Single `_idx` suffix is conventional for indexes.
        "ix_phase_17_finops_scheduled_sustainability_dispatch_tenant_idx",
        "phase_17_finops_scheduled_sustainability_dispatch",
        ["tenant_id", "dispatch_schedule"],
    )

    # ── 5. phase_17_finops_sustainability_viewer ──
    op.create_table(
        "phase_17_finops_sustainability_viewer",
        sa.Column("viewer_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text, nullable=False, server_default="sustainability_viewer"),
        sa.Column("granted_by", UUID(as_uuid=True), nullable=True),
        sa.Column("granted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "user_id",
            name="uq_phase_17_finops_sustainability_viewer_tenant_user",
        ),
        sa.CheckConstraint(
            "role IN ('sustainability_viewer')",
            name="ck_phase_17_finops_sustainability_viewer_role",
        ),
    )

    # ── 6. phase_17_finops_carbon_offset_registry ──
    op.create_table(
        "phase_17_finops_carbon_offset_registry",
        sa.Column("offset_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("registry_type", sa.Text, nullable=False),
        sa.Column("serial_number", sa.Text, nullable=False),
        sa.Column("vintage_year", sa.Integer, nullable=False),
        sa.Column("quantity_kgco2e", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("retired_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("retirement_reason", sa.Text, nullable=True),
        sa.Column("project_type", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "registry_type IN ('vcu', 'cer', 'kcu')",
            name="ck_phase_17_finops_carbon_offset_registry_type",
        ),
    )
    op.create_index(
        "ix_phase_17_finops_carbon_offset_registry_tenant_type",
        "phase_17_finops_carbon_offset_registry",
        ["tenant_id", "registry_type"],
    )

    # ── 7-10. 4 preview tables (dry-run output) ──
    for preview_table_name in (
        "phase_17_finops_carbon_emissions_rollup_preview",
        "phase_17_finops_sustainability_kpi_preview",
        "phase_17_finops_sustainability_report_preview",
        "phase_17_finops_scheduled_sustainability_dispatch_preview",
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
        "phase_17_finops_carbon_emissions_rollup",
        "phase_17_finops_sustainability_kpi",
        "phase_17_finops_sustainability_report",
        "phase_17_finops_scheduled_sustainability_dispatch",
        "phase_17_finops_sustainability_viewer",
        "phase_17_finops_carbon_offset_registry",
        "phase_17_finops_carbon_emissions_rollup_preview",
        "phase_17_finops_sustainability_kpi_preview",
        "phase_17_finops_sustainability_report_preview",
        "phase_17_finops_scheduled_sustainability_dispatch_preview",
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
        "phase_17_finops_carbon_emissions_rollup",
        "phase_17_finops_sustainability_kpi",
        "phase_17_finops_sustainability_report",
        "phase_17_finops_scheduled_sustainability_dispatch",
        "phase_17_finops_sustainability_viewer",
        "phase_17_finops_carbon_offset_registry",
        "phase_17_finops_carbon_emissions_rollup_preview",
        "phase_17_finops_sustainability_kpi_preview",
        "phase_17_finops_sustainability_report_preview",
        "phase_17_finops_scheduled_sustainability_dispatch_preview",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")
        op.drop_table(table_name)
