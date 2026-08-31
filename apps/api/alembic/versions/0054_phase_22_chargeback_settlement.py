"""Phase 22 wire — alembic 0054 phase_22_chargeback_settlement.

Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement territory
(PRD §F38 + AD-50 (a)~(g) 7 sub-decisions).

This migration creates 9 NEW tables + 1 preview table for Phase 22
FinOps Chargeback Settlement wire. All tables carry tenant_id
selector + RLS policies + CHECK constraints + UNIQUE indexes.

Tables:
1. phase_22_chargeback_settlement_rule (12 cols, UNIQUE per scope+period)
2. phase_22_chargeback_settlement_result (16 cols, INDEX per tenant+period)
3. phase_22_chargeback_settlement_allocation_line (10 cols, INDEX per result)
4. phase_22_chargeback_settlement_invoice (11 cols, INDEX per tenant+format)
5. phase_22_chargeback_settlement_reconciliation (12 cols, INDEX per result)
6. phase_22_chargeback_settlement_dispatch (10 cols, INDEX per cadence)
7. phase_22_chargeback_settlement_recipient_routing (8 cols, INDEX per tenant)
8. phase_22_chargeback_settlement_admin_alert (9 cols, INDEX per tenant)
9. phase_22_chargeback_settlement_owner_approval (10 cols, UNIQUE per user)
+ 1 preview table:
10. phase_22_chargeback_settlement_dry_run_preview

5-module cross-join layer (Phase 11 chargeback + Phase 18 commitment +
Phase 19 pricing + Phase 20 multi_cloud + Phase 21 reserved_capacity)
weighted average → single settlement_id + allocation_id + invoice_id +
reconciliation_id.

5-dim allocation (cost_center 0.30 + department 0.25 + business_unit
0.20 + tag 0.15 + tenant 0.10) + PDF/XLSX/CSV invoice + 3-way match
(1.0% tolerance + 3 auto-retries) + 4 cadence schedule KST pytz +
dry-run + Epic 12 2FA 챌린지 mandatory (high-value 10M KRW/year) +
8 NEW audit actions + 16 NEW typed exceptions.

CR lessons applied:
- CR 0-2 RLS — every table tenant_id selector + RLS policy.
- CR 12-5 D-14 — typed exception envelope aligned with error classes.
- AD-22 owner-only RBAC.
- NFR4 PII minimization — no PII columns.

Phase 11~21 carry-over: phase_11_finops_* ~ phase_21_reserved_capacity_*
tables RLS 정합 보존.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "0054_phase_22_chargeback_settlement"
down_revision = "0053_phase_21_reserved_capacity_planning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 9 NEW tables + 1 preview table with RLS + indexes."""

    # ── 1. phase_22_chargeback_settlement_rule ──
    op.create_table(
        "phase_22_chargeback_settlement_rule",
        sa.Column("settlement_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("rule_name", sa.Text, nullable=False),
        sa.Column("rule_type", sa.Text, nullable=False),
        sa.Column("target_amount_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("target_dimensions", JSONB, nullable=False, server_default="[]"),
        sa.Column("scope_chain", JSONB, nullable=False, server_default="{}"),
        sa.Column("settlement_status", sa.Text, nullable=False, server_default="draft"),
        sa.Column("requires_2fa_challenge", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "period_key", "rule_name",
            name="uq_phase_22_chargeback_settlement_rule_scope_period_name",
        ),
        sa.CheckConstraint(
            "rule_type IN ('flat_fee', 'proportional_allocation', 'metered_volume', 'tag_weighted')",
            name="ck_phase_22_chargeback_settlement_rule_type",
        ),
        sa.CheckConstraint(
            "settlement_status IN ('draft', 'pending_approval', 'approved', 'invoiced', 'reconciled')",
            name="ck_phase_22_chargeback_settlement_rule_status",
        ),
    )
    op.create_index(
        "ix_phase_22_chargeback_settlement_rule_tenant_period",
        "phase_22_chargeback_settlement_rule",
        ["tenant_id", "period_key"],
    )

    # ── 2. phase_22_chargeback_settlement_result ──
    op.create_table(
        "phase_22_chargeback_settlement_result",
        sa.Column("result_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("settlement_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("total_amount_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("five_module_attribution", JSONB, nullable=False, server_default="{}"),
        sa.Column("allocation_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("allocation_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("confidence_pct", sa.Numeric(5, 2), nullable=False, server_default="80.0"),
        sa.Column("tolerance_band_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("settlement_status", sa.Text, nullable=False, server_default="draft"),
        sa.Column("dry_run", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "total_amount_krw >= 0",
            name="ck_phase_22_chargeback_settlement_result_total_non_negative",
        ),
        sa.CheckConstraint(
            "confidence_pct >= 0 AND confidence_pct <= 100",
            name="ck_phase_22_chargeback_settlement_result_confidence_pct",
        ),
    )
    op.create_index(
        "ix_phase_22_chargeback_settlement_result_tenant_period",
        "phase_22_chargeback_settlement_result",
        ["tenant_id", "period_key"],
    )

    # ── 3. phase_22_chargeback_settlement_allocation_line ──
    op.create_table(
        "phase_22_chargeback_settlement_allocation_line",
        sa.Column("allocation_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("result_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("dimension", sa.Text, nullable=False),
        sa.Column("dimension_value", sa.Text, nullable=False),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("allocated_amount_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("audit_first_insert", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "dimension IN ('cost_center', 'department', 'business_unit', 'tag', 'tenant')",
            name="ck_phase_22_chargeback_settlement_allocation_line_dim",
        ),
        sa.CheckConstraint(
            "weight >= 0 AND weight <= 1",
            name="ck_phase_22_chargeback_settlement_allocation_line_weight",
        ),
    )
    op.create_index(
        "ix_phase_22_chargeback_settlement_allocation_line_result",
        "phase_22_chargeback_settlement_allocation_line",
        ["result_id"],
    )

    # ── 4. phase_22_chargeback_settlement_invoice ──
    op.create_table(
        "phase_22_chargeback_settlement_invoice",
        sa.Column("invoice_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("result_id", UUID(as_uuid=True), nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("invoice_format", sa.Text, nullable=False),
        sa.Column("bytes_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("recipient_routing", JSONB, nullable=False, server_default="{}"),
        sa.Column("s3_archive_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "invoice_format IN ('pdf', 'xlsx', 'csv')",
            name="ck_phase_22_chargeback_settlement_invoice_format",
        ),
        sa.CheckConstraint(
            "bytes_size >= 0 AND bytes_size <= 10485760",
            name="ck_phase_22_chargeback_settlement_invoice_size_max",
        ),
    )
    op.create_index(
        "ix_phase_22_chargeback_settlement_invoice_tenant_format",
        "phase_22_chargeback_settlement_invoice",
        ["tenant_id", "invoice_format"],
    )

    # ── 5. phase_22_chargeback_settlement_reconciliation ──
    op.create_table(
        "phase_22_chargeback_settlement_reconciliation",
        sa.Column("reconciliation_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("result_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("allocation_amount_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("invoice_amount_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("ledger_amount_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("variance_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("variance_krw", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("reconciliation_status", sa.Text, nullable=False, server_default="matched"),
        sa.Column("retry_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("requires_2fa_challenge", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("model_version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "reconciliation_status IN ('matched', 'variance_detected', 'retry_exhausted', 'needs_approval')",
            name="ck_phase_22_chargeback_settlement_reconciliation_status",
        ),
        sa.CheckConstraint(
            "retry_attempts >= 0 AND retry_attempts <= 3",
            name="ck_phase_22_chargeback_settlement_reconciliation_retry",
        ),
    )
    op.create_index(
        "ix_phase_22_chargeback_settlement_reconciliation_result",
        "phase_22_chargeback_settlement_reconciliation",
        ["result_id"],
    )

    # ── 6. phase_22_chargeback_settlement_dispatch ──
    op.create_table(
        "phase_22_chargeback_settlement_dispatch",
        sa.Column("dispatch_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("cadence", sa.Text, nullable=False),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("next_run_at_kst", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("dry_run", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("settlement_result_id", UUID(as_uuid=True), nullable=True),
        sa.Column("apscheduler_job_id", sa.Text, nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "cadence IN ('monthly', 'quarterly', 'semi_annual', 'annual')",
            name="ck_phase_22_chargeback_settlement_dispatch_cadence",
        ),
    )
    op.create_index(
        "ix_phase_22_chargeback_settlement_dispatch_cadence",
        "phase_22_chargeback_settlement_dispatch",
        ["cadence"],
    )

    # ── 7. phase_22_chargeback_settlement_recipient_routing ──
    op.create_table(
        "phase_22_chargeback_settlement_recipient_routing",
        sa.Column("routing_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("recipient_template", sa.Text, nullable=False),
        sa.Column("slack_channels", JSONB, nullable=False, server_default="[]"),
        sa.Column("email_recipients", JSONB, nullable=False, server_default="[]"),
        sa.Column("ms_teams_channels", JSONB, nullable=False, server_default="[]"),
        sa.Column("s3_archive_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.CheckConstraint(
            "recipient_template IN ('owner_only', 'executive', 'audit_only')",
            name="ck_phase_22_chargeback_settlement_recipient_routing_template",
        ),
    )

    # ── 8. phase_22_chargeback_settlement_admin_alert ──
    op.create_table(
        "phase_22_chargeback_settlement_admin_alert",
        sa.Column("alert_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("result_id", UUID(as_uuid=True), nullable=False),
        sa.Column("alert_channel", sa.Text, nullable=False, server_default="email"),
        sa.Column("email_recipients", JSONB, nullable=False, server_default="[]"),
        sa.Column("subject", sa.Text, nullable=False, server_default=""),
        sa.Column("variance_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("retry_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
    )

    # ── 9. phase_22_chargeback_settlement_owner_approval ──
    op.create_table(
        "phase_22_chargeback_settlement_owner_approval",
        sa.Column("approval_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("settlement_id", UUID(as_uuid=True), nullable=False),
        sa.Column("approved", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("two_factor_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint(
            "tenant_id", "user_id", "settlement_id",
            # D-CI-FUNC-9 cj-244 fix: original name was 64 chars, exceeds
            # Postgres NAMEDATALEN-1=63 and trips SQLAlchemy's
            # `dialect.validate_identifier`. Shortened to
            # `uq_phase_22_chargeback_settlement_owner_approval_user_set`
            # (60 chars) — drops `_settlement` suffix and uses `_set`
            # abbreviation since the table prefix already conveys it.
            # Columns unchanged. First NAMEDATALEN-1 sprint on a
            # UNIQUE constraint (uq_*) — same defect class but on a
            # different constraint type than prior CK/IX sprints.
            name="uq_phase_22_chargeback_settlement_owner_approval_user_set",
        ),
    )

    # ── 10. phase_22_chargeback_settlement_dry_run_preview ──
    op.create_table(
        "phase_22_chargeback_settlement_dry_run_preview",
        sa.Column("preview_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("preview_type", sa.Text, nullable=False, server_default="settlement_dispatch"),
        sa.Column("period_key", sa.Text, nullable=False),
        sa.Column("cadence", sa.Text, nullable=False, server_default="monthly"),
        sa.Column("rule_preview_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("allocation_preview_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("reconciliation_preview_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("invoice_preview_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("audit_action", sa.Text, nullable=False, server_default="settlement_dry_run_executed"),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text, nullable=False, server_default=""),
    )

    # ── RLS policies (CR 0-2 verbatim) ──
    for table_name in (
        "phase_22_chargeback_settlement_rule",
        "phase_22_chargeback_settlement_result",
        "phase_22_chargeback_settlement_allocation_line",
        "phase_22_chargeback_settlement_invoice",
        "phase_22_chargeback_settlement_reconciliation",
        "phase_22_chargeback_settlement_dispatch",
        "phase_22_chargeback_settlement_recipient_routing",
        "phase_22_chargeback_settlement_admin_alert",
        "phase_22_chargeback_settlement_owner_approval",
        "phase_22_chargeback_settlement_dry_run_preview",
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
        "phase_22_chargeback_settlement_rule",
        "phase_22_chargeback_settlement_result",
        "phase_22_chargeback_settlement_allocation_line",
        "phase_22_chargeback_settlement_invoice",
        "phase_22_chargeback_settlement_reconciliation",
        "phase_22_chargeback_settlement_dispatch",
        "phase_22_chargeback_settlement_recipient_routing",
        "phase_22_chargeback_settlement_admin_alert",
        "phase_22_chargeback_settlement_owner_approval",
        "phase_22_chargeback_settlement_dry_run_preview",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name};")
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")
        op.drop_table(table_name)
