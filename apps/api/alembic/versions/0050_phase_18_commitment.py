"""Phase 18 wire — alembic 0050 phase_18_finops_commitment.

Phase 18 wire (cj-style 135번째) — FinOps Cloud Commitment Management
(RIs/SPs/CUDs) territory (PRD §F34.7 + AD-45 (g) decision).

This migration creates 6 NEW tables + 4 preview tables for Phase 18
FinOps Cloud Commitment Management wire. All tables carry tenant_id
selector + RLS policies + CHECK constraints + UNIQUE indexes.

Tables:
1. phase_18_finops_commitment_inventory_rollup (18 cols, UNIQUE per scope)
2. phase_18_finops_commitment_kpi (12 cols, INDEX per period)
3. phase_18_finops_commitment_report (15 cols, INDEX per status)
4. phase_18_finops_scheduled_commitment_dispatch (11 cols, INDEX per schedule)
5. phase_18_finops_commitment_viewer (8 cols, UNIQUE per user)
6. phase_18_finops_commitment_purchase_order (12 cols, INDEX per renewal)
+ 4 preview tables:
7. phase_18_finops_commitment_inventory_rollup_preview
8. phase_18_finops_commitment_kpi_preview
9. phase_18_finops_commitment_report_preview
10. phase_18_finops_scheduled_commitment_dispatch_preview

CR lessons applied:
- CR 0-2 RLS — every table tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~17 carry-over: phase_11_finops_* ~ phase_17_finops_* tables
RLS 정합 보존.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0050_phase_18_finops_commitment"
down_revision = "0049_phase_17_finops_sustainability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 6 NEW tables + 4 preview tables with RLS + indexes."""

    # ── 1. phase_18_finops_commitment_inventory_rollup ──
    op.create_table(
        "phase_18_finops_commitment_inventory_rollup",
        sa.Column("commitment_rollup_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="{}"),
        sa.Column("total_commitment_value_krw", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("coverage_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("utilization_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("expiring_commitments_30d", sa.Integer, nullable=False, server_default="0"),
        sa.Column("recommended_purchase_krw", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("savings_realized_krw", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("idle_commitment_krw", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("renewal_decision_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cache_key", sa.Text, nullable=False),
        sa.Column(
            "computed_at",
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
            name="uq_phase_18_finops_commitment_inventory_rollup_scope_period",
        ),
        sa.CheckConstraint(
            "scope_type IN ('tenant', 'department', 'cost_center', 'product_line')",
            name="ck_phase_18_finops_commitment_inventory_rollup_scope_type",
        ),
    )
    op.create_index(
        "ix_phase_18_finops_commitment_inventory_rollup_tenant_period",
        "phase_18_finops_commitment_inventory_rollup",
        ["tenant_id", "period_key"],
    )

    # ── 2. phase_18_finops_commitment_kpi ──
    op.create_table(
        "phase_18_finops_commitment_kpi",
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
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "kpi_trend IN ('up', 'down', 'flat')",
            name="ck_phase_18_finops_commitment_kpi_trend",
        ),
        sa.CheckConstraint(
            "kpi_threshold_status IN ('on_track', 'warning', 'critical')",
            name="ck_phase_18_finops_commitment_kpi_threshold_status",
        ),
    )
    op.create_index(
        "ix_phase_18_finops_commitment_kpi_tenant_period",
        "phase_18_finops_commitment_kpi",
        ["tenant_id", "period_key"],
    )
    op.create_index(
        "ix_phase_18_finops_commitment_kpi_name",
        "phase_18_finops_commitment_kpi",
        ["kpi_name"],
    )

    # ── 3. phase_18_finops_commitment_report ──
    op.create_table(
        "phase_18_finops_commitment_report",
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
            name="ck_phase_18_finops_commitment_report_cadence",
        ),
        sa.CheckConstraint(
            "framework IN ('finops_foundation', 'aws_cost_optimization', 'azure_cost_optimization', 'gcp_cost_optimization', 'korea_procurement')",
            name="ck_phase_18_finops_commitment_report_framework",
        ),
        sa.CheckConstraint(
            "export_format IN ('pdf', 'csv', 'excel')",
            name="ck_phase_18_finops_commitment_report_export_format",
        ),
        sa.CheckConstraint(
            "status IN ('generating', 'completed', 'failed', 'expired')",
            name="ck_phase_18_finops_commitment_report_status",
        ),
    )
    op.create_index(
        "ix_phase_18_finops_commitment_report_tenant_status",
        "phase_18_finops_commitment_report",
        ["tenant_id", "status"],
    )

    # ── 4. phase_18_finops_scheduled_commitment_dispatch ──
    op.create_table(
        "phase_18_finops_scheduled_commitment_dispatch",
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
            name="ck_phase_18_finops_scheduled_commitment_dispatch_schedule",
        ),
        sa.CheckConstraint(
            "recipient_strategy IN ('owner_only', 'commitment_team', 'finance_team', 'custom_recipients')",
            # D-CI-FUNC-9 cj-239 fix: original name was 67 chars, exceeds
            # Postgres NAMEDATALEN-1=63 and trips SQLAlchemy's
            # `dialect.validate_identifier` BEFORE Postgres ever sees it.
            # Shortened to
            # `ck_phase_18_finops_scheduled_commitment_dispatch_recipient`
            # (58 chars) — drops the redundant `_strategy` suffix because
            # the table name + recipient already conveys intent. CHECK
            # expression unchanged.
            name="ck_phase_18_finops_scheduled_commitment_dispatch_recipient",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_phase_18_finops_scheduled_commitment_dispatch_status",
        ),
    )
    op.create_index(
        # D-CI-FUNC-9 cj-239 fix: original name was 64 chars, exceeds
        # Postgres NAMEDATALEN-1=63. Shortened
        # `..._dispatch_tenant_schedule` → `..._dispatch_tenant_idx`
        # (59 chars). Columns unchanged. Single `_idx` suffix is
        # conventional for indexes (mirrors cj-238 fix in 0049).
        "ix_phase_18_finops_scheduled_commitment_dispatch_tenant_idx",
        "phase_18_finops_scheduled_commitment_dispatch",
        ["tenant_id", "dispatch_schedule"],
    )

    # ── 5. phase_18_finops_commitment_viewer ──
    op.create_table(
        "phase_18_finops_commitment_viewer",
        sa.Column("viewer_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text, nullable=False, server_default="commitment_viewer"),
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
            name="uq_phase_18_finops_commitment_viewer_tenant_user",
        ),
        sa.CheckConstraint(
            "role IN ('commitment_viewer')",
            name="ck_phase_18_finops_commitment_viewer_role",
        ),
    )

    # ── 6. phase_18_finops_commitment_purchase_order ──
    op.create_table(
        "phase_18_finops_commitment_purchase_order",
        sa.Column("purchase_order_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("commitment_type", sa.Text, nullable=False),
        sa.Column("commitment_term", sa.Text, nullable=False),
        sa.Column("cloud_provider", sa.Text, nullable=False),
        sa.Column("order_value_krw", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("order_status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("renewal_decision_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("ordered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "commitment_type IN ('ec2_ri', 'rds_ri', 'ec2_sp', 's3_sp', 'redshift_sp', 'dynamodb_sp')",
            name="ck_phase_18_finops_commitment_purchase_order_type",
        ),
        sa.CheckConstraint(
            "commitment_term IN ('1_year', '3_year')",
            name="ck_phase_18_finops_commitment_purchase_order_term",
        ),
        sa.CheckConstraint(
            "cloud_provider IN ('aws', 'azure', 'gcp', 'naver', 'kt')",
            name="ck_phase_18_finops_commitment_purchase_order_provider",
        ),
        sa.CheckConstraint(
            "order_status IN ('pending', 'approved', 'purchased', 'active', 'expired', 'cancelled')",
            name="ck_phase_18_finops_commitment_purchase_order_status",
        ),
    )
    op.create_index(
        "ix_phase_18_finops_commitment_purchase_order_tenant_renewal",
        "phase_18_finops_commitment_purchase_order",
        ["tenant_id", "renewal_decision_score"],
    )

    # ── 7-10. 4 preview tables (dry-run output) ──
    for preview_table_name in (
        "phase_18_finops_commitment_inventory_rollup_preview",
        "phase_18_finops_commitment_kpi_preview",
        "phase_18_finops_commitment_report_preview",
        "phase_18_finops_scheduled_commitment_dispatch_preview",
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
        "phase_18_finops_commitment_inventory_rollup",
        "phase_18_finops_commitment_kpi",
        "phase_18_finops_commitment_report",
        "phase_18_finops_scheduled_commitment_dispatch",
        "phase_18_finops_commitment_viewer",
        "phase_18_finops_commitment_purchase_order",
        "phase_18_finops_commitment_inventory_rollup_preview",
        "phase_18_finops_commitment_kpi_preview",
        "phase_18_finops_commitment_report_preview",
        "phase_18_finops_scheduled_commitment_dispatch_preview",
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
        "phase_18_finops_commitment_inventory_rollup",
        "phase_18_finops_commitment_kpi",
        "phase_18_finops_commitment_report",
        "phase_18_finops_scheduled_commitment_dispatch",
        "phase_18_finops_commitment_viewer",
        "phase_18_finops_commitment_purchase_order",
        "phase_18_finops_commitment_inventory_rollup_preview",
        "phase_18_finops_commitment_kpi_preview",
        "phase_18_finops_commitment_report_preview",
        "phase_18_finops_scheduled_commitment_dispatch_preview",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")
        op.drop_table(table_name)
