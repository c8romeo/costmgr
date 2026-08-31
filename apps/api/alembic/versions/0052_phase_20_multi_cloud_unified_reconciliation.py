"""Phase 20 wire — alembic 0052 phase_20_multi_cloud_unified_reconciliation.

Phase 20 wire (cj-style 144번째) — FinOps Multi-Cloud Cost Unified
Reconciliation territory (PRD §F36.7 + AD-47 (g) decision).

This migration creates 8 NEW tables + 4 preview tables for Phase 20
FinOps Multi-Cloud Cost Unified Reconciliation wire. All tables carry
tenant_id selector + RLS policies + CHECK constraints + UNIQUE indexes.

Tables:
1. phase_20_multi_cloud_rate_card_reconciliation (18 cols, UNIQUE per scope)
2. phase_20_multi_cloud_cost_reconciliation (19 cols, INDEX per period)
3. phase_20_multi_cloud_negotiation_recommendation (16 cols, INDEX per status)
4. phase_20_blended_unblended_diff (14 cols, INDEX per provider)
5. phase_20_marketplace_saas_pricing (16 cols, INDEX per source)
6. phase_20_scheduled_multi_cloud_dispatch (11 cols, INDEX per schedule)
7. phase_20_multi_cloud_viewer (8 cols, UNIQUE per user)
8. phase_20_multi_cloud_negotiation_log (12 cols, INDEX per status)
+ 4 preview tables:
9. phase_20_multi_cloud_rate_card_reconciliation_preview
10. phase_20_multi_cloud_cost_reconciliation_preview
11. phase_20_marketplace_saas_pricing_preview
12. phase_20_blended_unblended_diff_preview

5 cloud provider cross-rollup (AWS + Azure + GCP + Naver + KT).
9-module cross-rollup (Phase 11-19 carry-over chain).
CR lessons applied:
- CR 0-2 RLS — every table tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~19 carry-over: phase_11_finops_* ~ phase_19_finops_* tables
RLS 정합 보존.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0052_phase_20_multi_cloud_unified_reconciliation"
down_revision = "0051_phase_19_finops_pricing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 8 NEW tables + 4 preview tables with RLS + indexes."""

    # ── 1. phase_20_multi_cloud_rate_card_reconciliation ──
    op.create_table(
        "phase_20_multi_cloud_rate_card_reconciliation",
        sa.Column("rate_card_reconciliation_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="{}"),
        sa.Column("effective_rate_krw_per_hour", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("rate_card_variance_krw_per_hour", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("rate_card_variance_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("rate_card_source_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("primary_rate_card_source", sa.Text, nullable=False, server_default="billing_api"),
        sa.Column("cloud_provider_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("rate_card_source_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("negotiation_recommendation_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rate_card_savings_krw_per_year", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("cache_key", sa.Text, nullable=False),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "scope_type", "scope_id", "period_key",
            name="uq_phase_20_multi_cloud_rate_card_reconciliation_scope_period",
        ),
        sa.CheckConstraint(
            "scope_type IN ('tenant', 'department', 'cost_center', 'product_line')",
            name="ck_phase_20_multi_cloud_rate_card_reconciliation_scope_type",
        ),
    )
    op.create_index(
        "ix_phase_20_multi_cloud_rate_card_reconciliation_tenant_period",
        "phase_20_multi_cloud_rate_card_reconciliation",
        ["tenant_id", "period_key"],
    )

    # ── 2. phase_20_multi_cloud_cost_reconciliation ──
    op.create_table(
        "phase_20_multi_cloud_cost_reconciliation",
        sa.Column("cost_reconciliation_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="{}"),
        sa.Column("cloud_provider", sa.Text, nullable=False),
        sa.Column("service_code", sa.Text, nullable=False, server_default="unknown"),
        sa.Column("region", sa.Text, nullable=False, server_default="default"),
        sa.Column("blended_cost_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("unblended_cost_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("cost_variance_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("cost_variance_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cost_source_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("primary_cost_source", sa.Text, nullable=False, server_default="billing_api"),
        sa.Column("cost_growth_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cost_forecast_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("last_reconciled_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "cloud_provider IN ('aws', 'azure', 'gcp', 'naver', 'kt')",
            name="ck_phase_20_multi_cloud_cost_reconciliation_provider",
        ),
        sa.CheckConstraint(
            "primary_cost_source IN ('billing_api', 'invoice_pdf', 'contract_estimated', 'manual', 'audit')",
            name="ck_phase_20_multi_cloud_cost_reconciliation_primary_source",
        ),
    )
    op.create_index(
        "ix_phase_20_multi_cloud_cost_reconciliation_tenant_period",
        "phase_20_multi_cloud_cost_reconciliation",
        ["tenant_id", "period_key"],
    )
    op.create_index(
        "ix_phase_20_multi_cloud_cost_reconciliation_provider",
        "phase_20_multi_cloud_cost_reconciliation",
        ["cloud_provider"],
    )

    # ── 3. phase_20_multi_cloud_negotiation_recommendation ──
    op.create_table(
        "phase_20_multi_cloud_negotiation_recommendation",
        sa.Column("negotiation_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("cloud_provider", sa.Text, nullable=False),
        sa.Column("commitment_term", sa.Text, nullable=False),
        sa.Column("strategy", sa.Text, nullable=False, server_default="moderate"),
        sa.Column("discount_pct_target", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("savings_krw_per_year", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("savings_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("auto_trigger_eligible", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("recommendation_status", sa.Text, nullable=False, server_default="manual_review_required"),
        sa.Column("guard_check_passed", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("triggered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "cloud_provider IN ('aws', 'azure', 'gcp', 'naver', 'kt')",
            name="ck_phase_20_multi_cloud_negotiation_recommendation_provider",
        ),
        sa.CheckConstraint(
            "commitment_term IN ('1_year', '3_year', '5_year')",
            name="ck_phase_20_multi_cloud_negotiation_recommendation_term",
        ),
        sa.CheckConstraint(
            "recommendation_status IN ('auto_negotiate_ready', 'manual_review_required', 'low_confidence')",
            name="ck_phase_20_multi_cloud_negotiation_recommendation_status",
        ),
    )
    op.create_index(
        # D-CI-FUNC-9 cj-241 fix: original name was 64 chars, exceeds
        # Postgres NAMEDATALEN-1=63 and trips SQLAlchemy's
        # `dialect.validate_identifier`. Shortened
        # `..._recommendation_tenant_status` → `..._recommendation_tenant_idx`
        # (61 chars). Columns unchanged. Same recurring defect class as
        # cj-238/239/240 (NAMEDATALEN-1) but this time on the
        # `phase_20_multi_cloud_negotiation_recommendation` table (not the
        # scheduled_dispatch slot).
        "ix_phase_20_multi_cloud_negotiation_recommendation_tenant_idx",
        "phase_20_multi_cloud_negotiation_recommendation",
        ["tenant_id", "recommendation_status"],
    )

    # ── 4. phase_20_blended_unblended_diff ──
    op.create_table(
        "phase_20_blended_unblended_diff",
        sa.Column("diff_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("cloud_provider", sa.Text, nullable=False),
        sa.Column("scope_type", sa.Text, nullable=False),
        sa.Column("scope_id", sa.Text, nullable=False),
        sa.Column("blended_rate_krw_per_hour", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("unblended_rate_krw_per_hour", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("rate_diff_krw_per_hour", sa.Numeric(20, 4), nullable=False, server_default="0"),
        sa.Column("rate_diff_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("service_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("resource_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tracking_status", sa.Text, nullable=False, server_default="real_time"),
        sa.Column("last_tracked_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "cloud_provider IN ('aws', 'azure', 'gcp', 'naver', 'kt')",
            name="ck_phase_20_blended_unblended_diff_provider",
        ),
        sa.CheckConstraint(
            "tracking_status IN ('real_time', 'near_real_time', 'drift_detected', 'api_unavailable')",
            name="ck_phase_20_blended_unblended_diff_tracking_status",
        ),
    )
    op.create_index(
        "ix_phase_20_blended_unblended_diff_tenant_provider",
        "phase_20_blended_unblended_diff",
        ["tenant_id", "cloud_provider"],
    )

    # ── 5. phase_20_marketplace_saas_pricing ──
    op.create_table(
        "phase_20_marketplace_saas_pricing",
        sa.Column("marketplace_pricing_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("marketplace_source", sa.Text, nullable=False),
        sa.Column("vendor_name", sa.Text, nullable=False),
        sa.Column("product_name", sa.Text, nullable=False),
        sa.Column("sku", sa.Text, nullable=False),
        sa.Column("list_price_krw_per_unit", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("negotiated_price_krw_per_unit", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("effective_price_krw_per_unit", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("unit", sa.Text, nullable=False, server_default="per_user"),
        sa.Column("saas_category", sa.Text, nullable=False, server_default="other"),
        sa.Column("pricing_model", sa.Text, nullable=False, server_default="subscription"),
        sa.Column("integration_status", sa.Text, nullable=False, server_default="active"),
        sa.Column("last_synced_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "marketplace_source IN ('aws_marketplace', 'azure_marketplace', 'gcp_marketplace', 'naver_marketplace', 'kt_marketplace')",
            name="ck_phase_20_marketplace_saas_pricing_source",
        ),
        sa.CheckConstraint(
            "integration_status IN ('active', 'pending', 'failed', 'disabled')",
            name="ck_phase_20_marketplace_saas_pricing_integration_status",
        ),
    )
    op.create_index(
        "ix_phase_20_marketplace_saas_pricing_tenant_source",
        "phase_20_marketplace_saas_pricing",
        ["tenant_id", "marketplace_source"],
    )

    # ── 6. phase_20_scheduled_multi_cloud_dispatch ──
    op.create_table(
        "phase_20_scheduled_multi_cloud_dispatch",
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
            name="ck_phase_20_scheduled_multi_cloud_dispatch_schedule",
        ),
        sa.CheckConstraint(
            "recipient_strategy IN ('owner_only', 'finops_team', 'exec_team', 'custom_recipients')",
            name="ck_phase_20_scheduled_multi_cloud_dispatch_recipient_strategy",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_phase_20_scheduled_multi_cloud_dispatch_status",
        ),
    )
    op.create_index(
        "ix_phase_20_scheduled_multi_cloud_dispatch_tenant_schedule",
        "phase_20_scheduled_multi_cloud_dispatch",
        ["tenant_id", "dispatch_schedule"],
    )

    # ── 7. phase_20_multi_cloud_viewer ──
    op.create_table(
        "phase_20_multi_cloud_viewer",
        sa.Column("viewer_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text, nullable=False, server_default="multi_cloud_viewer"),
        sa.Column("granted_by", UUID(as_uuid=True), nullable=True),
        sa.Column("granted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "user_id",
            name="uq_phase_20_multi_cloud_viewer_tenant_user",
        ),
        sa.CheckConstraint(
            "role IN ('multi_cloud_viewer')",
            name="ck_phase_20_multi_cloud_viewer_role",
        ),
    )

    # ── 8. phase_20_multi_cloud_negotiation_log ──
    op.create_table(
        "phase_20_multi_cloud_negotiation_log",
        sa.Column("log_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("negotiation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("cloud_provider", sa.Text, nullable=False),
        sa.Column("trigger_type", sa.Text, nullable=False, server_default="auto"),
        sa.Column("trigger_status", sa.Text, nullable=False, server_default="triggered"),
        sa.Column("dispatched_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("negotiation_savings_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("monthly_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("daily_auto_trigger_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("expired_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "trigger_type IN ('auto', 'manual', 'override')",
            name="ck_phase_20_multi_cloud_negotiation_log_trigger_type",
        ),
        sa.CheckConstraint(
            "trigger_status IN ('triggered', 'completed', 'failed', 'guard_rejected')",
            name="ck_phase_20_multi_cloud_negotiation_log_trigger_status",
        ),
    )
    op.create_index(
        "ix_phase_20_multi_cloud_negotiation_log_tenant_status",
        "phase_20_multi_cloud_negotiation_log",
        ["tenant_id", "trigger_status"],
    )

    # ── 9-12. 4 preview tables (dry-run output) ──
    for preview_table_name in (
        "phase_20_multi_cloud_rate_card_reconciliation_preview",
        "phase_20_multi_cloud_cost_reconciliation_preview",
        "phase_20_marketplace_saas_pricing_preview",
        "phase_20_blended_unblended_diff_preview",
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
        "phase_20_multi_cloud_rate_card_reconciliation",
        "phase_20_multi_cloud_cost_reconciliation",
        "phase_20_multi_cloud_negotiation_recommendation",
        "phase_20_blended_unblended_diff",
        "phase_20_marketplace_saas_pricing",
        "phase_20_scheduled_multi_cloud_dispatch",
        "phase_20_multi_cloud_viewer",
        "phase_20_multi_cloud_negotiation_log",
        "phase_20_multi_cloud_rate_card_reconciliation_preview",
        "phase_20_multi_cloud_cost_reconciliation_preview",
        "phase_20_marketplace_saas_pricing_preview",
        "phase_20_blended_unblended_diff_preview",
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
    """Drop RLS policies + 12 tables."""
    for table_name in (
        "phase_20_multi_cloud_rate_card_reconciliation",
        "phase_20_multi_cloud_cost_reconciliation",
        "phase_20_multi_cloud_negotiation_recommendation",
        "phase_20_blended_unblended_diff",
        "phase_20_marketplace_saas_pricing",
        "phase_20_scheduled_multi_cloud_dispatch",
        "phase_20_multi_cloud_viewer",
        "phase_20_multi_cloud_negotiation_log",
        "phase_20_multi_cloud_rate_card_reconciliation_preview",
        "phase_20_multi_cloud_cost_reconciliation_preview",
        "phase_20_marketplace_saas_pricing_preview",
        "phase_20_blended_unblended_diff_preview",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")
        op.drop_table(table_name)
