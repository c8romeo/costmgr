"""Story Phase 15 — phase_15 FinOps Tag Governance & Cost Allocation tables.

Phase 15 (cj-style 123번째 wire) — AD-42 (a)~(g) verbatim +
§F31.1 + §F31.2 + §F31.3 + §F31.4 + §F31.5 + §F31.6 + §F31.7 + §F31.8.

Background:
- Phase 14 wire (cj-style 119번째) shipped FinOps Optimization & Rightsizing
  territory (6 tables). Phase 15 territory carries the COST ALLOCATION
  governance layer EXTENSION — tag policy DSL + untagged resource detector
  + allocation rules engine + compliance + chargeback reconciliation.
- §F31.1 tag policy DSL + §F31.2 untagged resource detector +
  §F31.3 allocation rules engine + §F31.4 allocation audit + compliance +
  §F31.5 chargeback allocation reconciliation + §F31.6 dashboard UI +
  §F31.7 capability matrix v1.41 EXTENSION + §F31.8 dry-run + Tests:
  - 6 main tables + 4 preview tables (preview for dry-run mode)
    with RLS policies.
- §F31.1 TagPolicy TypedDict 11 fields (F31.1.2 verbatim).
- §F31.2 UntaggedResource TypedDict 13 fields (F31.2.2 verbatim).
- §F31.3 AllocationRule TypedDict 12 fields (F31.3.3 verbatim).
- §F31.4 ComplianceReport TypedDict 12 fields (F31.4.3 verbatim).
- §F31.5 Reconciliation TypedDict 13 fields (F31.5.3 verbatim).
- 8 ACs PRD §F31.1~§F31.8 verbatim → 92 sub-ACs.

Schema (PRD §F31.1~§F31.5 verbatim + AD-42 verbatim):

1. phase_15_finops_tag_policy (PRD §F31.1.2 verbatim, 12 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
   - policy_id: TEXT UNIQUE
   - resource_type: TEXT (6 options CHECK)
   - tag_key: TEXT
   - enforcement_level: TEXT (4 options CHECK)
   - default_value: TEXT
   - compliance_threshold_pct: NUMERIC(8, 4)
   - remediation_action: TEXT (3 options CHECK)
   - status: TEXT (3 statuses CHECK)
   - metadata: JSONB (per-tenant override EXTENSION)
   - created_at: TIMESTAMPTZ DEFAULT NOW()
   - updated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT
   - UNIQUE (tenant_id, resource_type, tag_key)

2. phase_15_finops_untagged_resource (PRD §F31.2.2 verbatim, 14 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - detection_id: TEXT UNIQUE
   - resource_id: TEXT
   - resource_arn: TEXT
   - resource_type: TEXT (6 options CHECK)
   - untagged_tags: JSONB
   - detection_window: TEXT (3 options CHECK)
   - detection_method: TEXT (3 options CHECK)
   - severity: TEXT (4 options CHECK)
   - action_recommendation: TEXT (4 options CHECK)
   - remediation_sla_hours: INTEGER
   - detected_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

3. phase_15_finops_allocation_rule (PRD §F31.3.3 verbatim, 13 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - rule_id: TEXT UNIQUE
   - rule_type: TEXT (5 options CHECK)
   - scope_resource_types: JSONB
   - precedence: INTEGER (0-9999 CHECK)
   - parameters: JSONB
   - effective_from: DATE
   - effective_to: DATE (nullable)
   - audit_required: BOOLEAN DEFAULT TRUE
   - status: TEXT (4 statuses CHECK)
   - created_at: TIMESTAMPTZ DEFAULT NOW()
   - updated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

4. phase_15_finops_compliance_report (PRD §F31.4.3 verbatim, 13 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - report_id: TEXT UNIQUE
   - report_type: TEXT (4 options CHECK)
   - period_start: DATE
   - period_end: DATE
   - total_resources_scanned: INTEGER
   - compliant_resources: INTEGER
   - non_compliant_resources: INTEGER
   - compliance_pct: NUMERIC(8, 4)
   - status: TEXT (4 options CHECK)
   - export_format: TEXT (3 options CHECK)
   - retention_until: DATE
   - trace_id: TEXT

5. phase_15_finops_chargeback_reconciliation (PRD §F31.5.3 verbatim, 14 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - reconciliation_id: TEXT UNIQUE
   - strategy: TEXT (3 options CHECK)
   - period_start: DATE
   - period_end: DATE
   - chargeback_amount_usd: NUMERIC(20, 2)
   - tag_allocation_amount_usd: NUMERIC(20, 2)
   - variance_amount_usd: NUMERIC(20, 2)
   - variance_pct: NUMERIC(8, 4)
   - delta_threshold_pct: NUMERIC(8, 4)
   - auto_approve_below_pct: NUMERIC(8, 4)
   - status: TEXT (4 statuses CHECK)
   - trace_id: TEXT

6. phase_15_finops_allocation_audit (PRD §F31.4 verbatim, audit log):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - audit_id: TEXT UNIQUE
   - action: TEXT (10 NEW action types CHECK)
   - resource_type: TEXT
   - resource_id: TEXT
   - actor_user_id: UUID
   - audit_metadata: JSONB
   - retention_until: DATE
   - created_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

Plus 4 preview tables for dry-run:
- phase_15_finops_tag_policy_preview
- phase_15_finops_untagged_resource_preview
- phase_15_finops_allocation_rule_preview
- phase_15_finops_chargeback_reconciliation_preview

CR lessons applied:
- CR 0-2 RLS — every table has tenant_id + RLS policy.
- CR 1-1 audit-first INSERT — companion audit log table.
- CR 11-4 P-015 — pure validator pattern (CHECK constraints enforce
  enum values).
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0047_phase_15_tag_governance"
down_revision = "0046_phase_14_optimization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. phase_15_finops_tag_policy (PRD §F31.1.2 verbatim) ──────
    op.create_table(
        "phase_15_finops_tag_policy",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("policy_id", sa.Text(), nullable=False, unique=True),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("tag_key", sa.Text(), nullable=False),
        sa.Column("enforcement_level", sa.Text(), nullable=False),
        sa.Column("default_value", sa.Text(), nullable=False),
        sa.Column("compliance_threshold_pct", sa.dialects.postgresql.NUMERIC(8, 4), nullable=False),
        sa.Column("remediation_action", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "phase_15_finops_tag_policy_resource_type_check",
        "phase_15_finops_tag_policy",
        "resource_type IN ('ec2','rds','s3','lambda','eks','vpc')",
    )
    op.create_check_constraint(
        "phase_15_finops_tag_policy_enforcement_level_check",
        "phase_15_finops_tag_policy",
        "enforcement_level IN ('required','recommended','optional','blocked')",
    )
    op.create_check_constraint(
        "phase_15_finops_tag_policy_remediation_action_check",
        "phase_15_finops_tag_policy",
        "remediation_action IN ('notify_only','auto_remediate','block_provisioning')",
    )
    op.create_check_constraint(
        "phase_15_finops_tag_policy_status_check",
        "phase_15_finops_tag_policy",
        "status IN ('active','paused','expired')",
    )
    op.create_unique_constraint(
        "phase_15_finops_tag_policy_tenant_resource_tag_key_uniq",
        "phase_15_finops_tag_policy",
        ["tenant_id", "resource_type", "tag_key"],
    )
    op.create_index(
        "phase_15_finops_tag_policy_tenant_idx",
        "phase_15_finops_tag_policy",
        ["tenant_id"],
    )
    op.execute(
        "ALTER TABLE phase_15_finops_tag_policy ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_tag_policy_tenant_isolation
        ON phase_15_finops_tag_policy
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # ── 2. phase_15_finops_untagged_resource (PRD §F31.2.2 verbatim)
    op.create_table(
        "phase_15_finops_untagged_resource",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("detection_id", sa.Text(), nullable=False, unique=True),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("resource_arn", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("untagged_tags", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("detection_window", sa.Text(), nullable=False),
        sa.Column("detection_method", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("action_recommendation", sa.Text(), nullable=False),
        sa.Column("remediation_sla_hours", sa.Integer(), nullable=False),
        sa.Column("detected_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "phase_15_finops_untagged_resource_resource_type_check",
        "phase_15_finops_untagged_resource",
        "resource_type IN ('ec2','rds','s3','lambda','eks','vpc')",
    )
    op.create_check_constraint(
        "phase_15_finops_untagged_resource_detection_window_check",
        "phase_15_finops_untagged_resource",
        "detection_window IN ('7d','30d','90d')",
    )
    op.create_check_constraint(
        "phase_15_finops_untagged_resource_detection_method_check",
        "phase_15_finops_untagged_resource",
        "detection_method IN ('z_score','threshold','heuristic')",
    )
    op.create_check_constraint(
        "phase_15_finops_untagged_resource_severity_check",
        "phase_15_finops_untagged_resource",
        "severity IN ('low','medium','high','critical')",
    )
    op.create_check_constraint(
        "phase_15_finops_untagged_resource_action_recommendation_check",
        "phase_15_finops_untagged_resource",
        "action_recommendation IN ('notify_only','auto_remediate','block_provisioning','manual_review')",
    )
    op.create_index(
        "phase_15_finops_untagged_resource_tenant_idx",
        "phase_15_finops_untagged_resource",
        ["tenant_id"],
    )
    op.execute(
        "ALTER TABLE phase_15_finops_untagged_resource ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_untagged_resource_tenant_isolation
        ON phase_15_finops_untagged_resource
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # ── 3. phase_15_finops_allocation_rule (PRD §F31.3.3 verbatim) ──
    op.create_table(
        "phase_15_finops_allocation_rule",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("rule_id", sa.Text(), nullable=False, unique=True),
        sa.Column("rule_type", sa.Text(), nullable=False),
        sa.Column("scope_resource_types", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("precedence", sa.Integer(), nullable=False),
        sa.Column("parameters", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("audit_required", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "phase_15_finops_allocation_rule_rule_type_check",
        "phase_15_finops_allocation_rule",
        "rule_type IN ('tag_match','percentage_split','weighted','conditional','fallback')",
    )
    op.create_check_constraint(
        "phase_15_finops_allocation_rule_precedence_check",
        "phase_15_finops_allocation_rule",
        "precedence BETWEEN 0 AND 9999",
    )
    op.create_check_constraint(
        "phase_15_finops_allocation_rule_status_check",
        "phase_15_finops_allocation_rule",
        "status IN ('active','paused','expired','draft')",
    )
    op.create_index(
        "phase_15_finops_allocation_rule_tenant_idx",
        "phase_15_finops_allocation_rule",
        ["tenant_id"],
    )
    op.create_index(
        "phase_15_finops_allocation_rule_precedence_idx",
        "phase_15_finops_allocation_rule",
        ["tenant_id", "precedence"],
    )
    op.execute(
        "ALTER TABLE phase_15_finops_allocation_rule ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_allocation_rule_tenant_isolation
        ON phase_15_finops_allocation_rule
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # ── 4. phase_15_finops_compliance_report (PRD §F31.4.3 verbatim)
    op.create_table(
        "phase_15_finops_compliance_report",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("report_id", sa.Text(), nullable=False, unique=True),
        sa.Column("report_type", sa.Text(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("total_resources_scanned", sa.Integer(), nullable=False),
        sa.Column("compliant_resources", sa.Integer(), nullable=False),
        sa.Column("non_compliant_resources", sa.Integer(), nullable=False),
        sa.Column("compliance_pct", sa.dialects.postgresql.NUMERIC(8, 4), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("export_format", sa.Text(), nullable=False),
        sa.Column("retention_until", sa.Date(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "phase_15_finops_compliance_report_report_type_check",
        "phase_15_finops_compliance_report",
        "report_type IN ('tag_policy_compliance','untagged_resource_summary','allocation_rule_audit','chargeback_reconciliation')",
    )
    op.create_check_constraint(
        "phase_15_finops_compliance_report_status_check",
        "phase_15_finops_compliance_report",
        "status IN ('ok','warning','breach','remediating')",
    )
    op.create_check_constraint(
        "phase_15_finops_compliance_report_export_format_check",
        "phase_15_finops_compliance_report",
        "export_format IN ('csv','pdf','json')",
    )
    op.create_index(
        "phase_15_finops_compliance_report_tenant_idx",
        "phase_15_finops_compliance_report",
        ["tenant_id"],
    )
    op.execute(
        "ALTER TABLE phase_15_finops_compliance_report ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_compliance_report_tenant_isolation
        ON phase_15_finops_compliance_report
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # ── 5. phase_15_finops_chargeback_reconciliation (PRD §F31.5.3)
    op.create_table(
        "phase_15_finops_chargeback_reconciliation",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("reconciliation_id", sa.Text(), nullable=False, unique=True),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("chargeback_amount_usd", sa.dialects.postgresql.NUMERIC(20, 2), nullable=False),
        sa.Column("tag_allocation_amount_usd", sa.dialects.postgresql.NUMERIC(20, 2), nullable=False),
        sa.Column("variance_amount_usd", sa.dialects.postgresql.NUMERIC(20, 2), nullable=False),
        sa.Column("variance_pct", sa.dialects.postgresql.NUMERIC(8, 4), nullable=False),
        sa.Column("delta_threshold_pct", sa.dialects.postgresql.NUMERIC(8, 4), nullable=False),
        sa.Column("auto_approve_below_pct", sa.dialects.postgresql.NUMERIC(8, 4), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "phase_15_finops_chargeback_reconciliation_strategy_check",
        "phase_15_finops_chargeback_reconciliation",
        "strategy IN ('chargeback_only','tag_allocation_only','hybrid_blended')",
    )
    op.create_check_constraint(
        "phase_15_finops_chargeback_reconciliation_status_check",
        "phase_15_finops_chargeback_reconciliation",
        "status IN ('pending','investigating','approved','resolved')",
    )
    op.create_index(
        "phase_15_finops_chargeback_reconciliation_tenant_idx",
        "phase_15_finops_chargeback_reconciliation",
        ["tenant_id"],
    )
    op.execute(
        "ALTER TABLE phase_15_finops_chargeback_reconciliation ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_chargeback_reconciliation_tenant_isolation
        ON phase_15_finops_chargeback_reconciliation
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # ── 6. phase_15_finops_allocation_audit (PRD §F31.4 verbatim) ──
    op.create_table(
        "phase_15_finops_allocation_audit",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("audit_id", sa.Text(), nullable=False, unique=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column("audit_metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("retention_until", sa.Date(), nullable=False),
        sa.Column("created_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "phase_15_finops_allocation_audit_action_check",
        "phase_15_finops_allocation_audit",
        "action IN ('tag_policy_updated','untagged_resource_detected','allocation_rule_evaluated','allocation_rule_updated','compliance_report_generated','compliance_alert_sent','compliance_remediation_initiated','reconciliation_initiated','reconciliation_report_generated','reconciliation_investigation_triggered','reconciliation_approved','reconciliation_resolved','finops_tag_governance_dry_run')",
    )
    op.create_index(
        "phase_15_finops_allocation_audit_tenant_idx",
        "phase_15_finops_allocation_audit",
        ["tenant_id"],
    )
    op.create_index(
        "phase_15_finops_allocation_audit_action_idx",
        "phase_15_finops_allocation_audit",
        ["tenant_id", "action"],
    )
    op.execute(
        "ALTER TABLE phase_15_finops_allocation_audit ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_allocation_audit_tenant_isolation
        ON phase_15_finops_allocation_audit
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # ── 7-10. Preview tables (dry-run mode) ──────────────────────
    # Tag policy preview
    op.create_table(
        "phase_15_finops_tag_policy_preview",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("dry_run_id", sa.Text(), nullable=False, unique=True),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("tag_key", sa.Text(), nullable=False),
        sa.Column("enforcement_level", sa.Text(), nullable=False),
        sa.Column("preview_metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.execute(
        "ALTER TABLE phase_15_finops_tag_policy_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_tag_policy_preview_tenant_isolation
        ON phase_15_finops_tag_policy_preview
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # Untagged resource preview
    op.create_table(
        "phase_15_finops_untagged_resource_preview",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("dry_run_id", sa.Text(), nullable=False, unique=True),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("preview_metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.execute(
        "ALTER TABLE phase_15_finops_untagged_resource_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_untagged_resource_preview_tenant_isolation
        ON phase_15_finops_untagged_resource_preview
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # Allocation rule preview
    op.create_table(
        "phase_15_finops_allocation_rule_preview",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("dry_run_id", sa.Text(), nullable=False, unique=True),
        sa.Column("rule_type", sa.Text(), nullable=False),
        sa.Column("preview_metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.execute(
        "ALTER TABLE phase_15_finops_allocation_rule_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_allocation_rule_preview_tenant_isolation
        ON phase_15_finops_allocation_rule_preview
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )

    # Chargeback reconciliation preview
    op.create_table(
        "phase_15_finops_chargeback_reconciliation_preview",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("dry_run_id", sa.Text(), nullable=False, unique=True),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column("preview_metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.dialects.postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.execute(
        "ALTER TABLE phase_15_finops_chargeback_reconciliation_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_15_finops_chargeback_reconciliation_preview_tenant_isolation
        ON phase_15_finops_chargeback_reconciliation_preview
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    # Drop preview tables first (reverse order)
    op.execute("DROP POLICY IF EXISTS phase_15_finops_chargeback_reconciliation_preview_tenant_isolation ON phase_15_finops_chargeback_reconciliation_preview;")
    op.drop_table("phase_15_finops_chargeback_reconciliation_preview")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_allocation_rule_preview_tenant_isolation ON phase_15_finops_allocation_rule_preview;")
    op.drop_table("phase_15_finops_allocation_rule_preview")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_untagged_resource_preview_tenant_isolation ON phase_15_finops_untagged_resource_preview;")
    op.drop_table("phase_15_finops_untagged_resource_preview")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_tag_policy_preview_tenant_isolation ON phase_15_finops_tag_policy_preview;")
    op.drop_table("phase_15_finops_tag_policy_preview")

    # Drop main tables (reverse order)
    op.execute("DROP POLICY IF EXISTS phase_15_finops_allocation_audit_tenant_isolation ON phase_15_finops_allocation_audit;")
    op.drop_table("phase_15_finops_allocation_audit")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_chargeback_reconciliation_tenant_isolation ON phase_15_finops_chargeback_reconciliation;")
    op.drop_table("phase_15_finops_chargeback_reconciliation")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_compliance_report_tenant_isolation ON phase_15_finops_compliance_report;")
    op.drop_table("phase_15_finops_compliance_report")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_allocation_rule_tenant_isolation ON phase_15_finops_allocation_rule;")
    op.drop_table("phase_15_finops_allocation_rule")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_untagged_resource_tenant_isolation ON phase_15_finops_untagged_resource;")
    op.drop_table("phase_15_finops_untagged_resource")
    op.execute("DROP POLICY IF EXISTS phase_15_finops_tag_policy_tenant_isolation ON phase_15_finops_tag_policy;")
    op.drop_table("phase_15_finops_tag_policy")