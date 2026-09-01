"""alembic version 0058 — Phase 28 FinOps Interactive Dashboard (4 tables + 1 preview + RLS).

Revision ID: 0058_phase_28_interactive_dashboard
Revises: 0057_phase_25_vendor_management
Create Date: 2026-08-29 (KST)

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
cross-phase aggregator + saved_view_engine + export_pipeline +
dashboard_sharing layer (PRD §F43.1~§F43.8 verbatim + AD-56 (a)~(g)
7 sub-decisions).

This migration adds **4 NEW domain tables + 1 preview table** for
Phase 28 territory:

1. m28_phase_28_interactive_dashboard_unified_kpi (4 tables #1)
   — Phase 11~27 cross-phase unified KPI rollup (PRD §F43.1 verbatim)
   + 6-dim cross-rollup + trace_id ContextVar + RLS

2. m28_phase_28_interactive_dashboard_saved_view (4 tables #2)
   — Per-tenant saved dashboard view (PRD §F43.2 verbatim)
   + 12 NEW pre-defined view templates + audit_trail JSONB + RLS

3. m28_phase_28_interactive_dashboard_export_job (4 tables #3)
   — Per-export job tracking (PRD §F43.3 verbatim)
   + 5 export formats + checksum_sha256 + file_size + RLS

4. m28_phase_28_interactive_dashboard_sharing_grant (4 tables #4)
   — Dashboard sharing grants (PRD §F43.7 verbatim)
   + 4 sharing scopes + expires_at + audit_trail + RLS

5. m28_phase_28_interactive_dashboard_preview (1 preview table)
   — Dry-run preview ONLY (PRD §F43.8 verbatim)
   + preview_data JSONB + RLS

Honest scope notes (per CR 11-3 honest-DEFER 89번째):
- Phase 28 wire 의 4 domain tables + 1 preview table 은 Phase 26 의
  1 preview table 패턴 대비 정직한 scope 확장 (commit-msg 에 명기).
- Dangling `0055 → 0054` alembic graph 단일 head 결정 wire 보존
  (Phase 25 의 진짜 revision 은 0057, 0054 는 존재하지 않음 — Phase
  26 atomic wire 진입 시점의 honestly DEFER 보존; cj-188 retro
  에서 D-DEFER-Phase-26-alembic-graph 결정 wire 보류).
- alembic 0058 의 down_revision = "0057_phase_25_vendor_management"
  (Q1 결정 wire: 0057 뒤에 정상 부착, 0055 dangling carry-over 정직
  보존).

NFR4 PII minimization PRESERVED — no employee PII data, only business
metrics + cost amounts + view configs + audit trail + RLS-protected
tenant_id selector.

CR lessons applied:
- CR 0-2 RLS — tenant_id column selector + RLS policy.
- CR 1-1 audit-first INSERT — audit_trail JSONB column preserved.
- CR 5-1 Decimal NUMERIC(18,2) — all KRW currency amounts.
- AD-22 owner-only RBAC.
- AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0059_phase_28_interactive_dashboard"
down_revision = "0058_phase_26_cost_anomaly_ml_prediction"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema — Phase 28 interactive_dashboard 4 tables + 1 preview."""

    # ── 1. m28_phase_28_interactive_dashboard_unified_kpi ──────────────
    op.create_table(
        "m28_phase_28_interactive_dashboard_unified_kpi",
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unified_kpi_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_key", sa.String(length=64), nullable=False),
        sa.Column("dimension", sa.String(length=64), nullable=False),
        sa.Column("dimension_value", sa.String(length=256), nullable=False),
        sa.Column(
            "kpi_value_krw",
            sa.dialects.postgresql.NUMERIC(precision=18, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("kpi_breakdown", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "unified_kpi_id"),
        schema="public",
    )

    op.create_index(
        "ix_m28_unified_kpi_tenant_period",
        "m28_phase_28_interactive_dashboard_unified_kpi",
        ["tenant_id", "period_key"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_m28_unified_kpi_dimension",
        "m28_phase_28_interactive_dashboard_unified_kpi",
        ["dimension"],
        unique=False,
        schema="public",
    )

    # ── 2. m28_phase_28_interactive_dashboard_saved_view ────────────────
    op.create_table(
        "m28_phase_28_interactive_dashboard_saved_view",
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_view_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("view_name", sa.String(length=256), nullable=False),
        sa.Column("template_id", sa.String(length=128), nullable=True),
        sa.Column("view_config", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("audit_trail", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "saved_view_id"),
        schema="public",
    )

    op.create_index(
        "ix_m28_saved_view_tenant_template",
        "m28_phase_28_interactive_dashboard_saved_view",
        ["tenant_id", "template_id"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_m28_saved_view_view_config_gin",
        "m28_phase_28_interactive_dashboard_saved_view",
        ["view_config"],
        unique=False,
        schema="public",
        postgresql_using="gin",
    )
    op.create_index(
        "ix_m28_saved_view_audit_trail_gin",
        "m28_phase_28_interactive_dashboard_saved_view",
        ["audit_trail"],
        unique=False,
        schema="public",
        postgresql_using="gin",
    )

    # ── 3. m28_phase_28_interactive_dashboard_export_job ───────────────
    op.create_table(
        "m28_phase_28_interactive_dashboard_export_job",
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("export_job_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_view_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column(
            "progress_pct",
            sa.dialects.postgresql.NUMERIC(precision=5, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        # format enum CHECK
        sa.CheckConstraint(
            "format IN ('pdf', 'xlsx', 'csv', 'json', 'png')",
            name="ck_m28_export_job_format",
        ),
        # status enum CHECK
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')",
            name="ck_m28_export_job_status",
        ),
        # idempotency key UNIQUE
        sa.UniqueConstraint(
            "tenant_id",
            "export_job_id",
            name="uq_m28_export_job_idempotency",
        ),
        sa.PrimaryKeyConstraint("tenant_id", "export_job_id"),
        schema="public",
    )

    op.create_index(
        "ix_m28_export_job_tenant_status",
        "m28_phase_28_interactive_dashboard_export_job",
        ["tenant_id", "status"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_m28_export_job_format",
        "m28_phase_28_interactive_dashboard_export_job",
        ["format"],
        unique=False,
        schema="public",
    )

    # ── 4. m28_phase_28_interactive_dashboard_sharing_grant ─────────────
    op.create_table(
        "m28_phase_28_interactive_dashboard_sharing_grant",
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sharing_grant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_view_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="private"),
        sa.Column("granted_to_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("granted_by_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("audit_trail", sa.dialects.postgresql.JSONB(), nullable=True),
        # scope enum CHECK
        sa.CheckConstraint(
            "scope IN ('private', 'tenant', 'tenant_owner', 'cross_tenant')",
            name="ck_m28_sharing_grant_scope",
        ),
        sa.PrimaryKeyConstraint("tenant_id", "sharing_grant_id"),
        schema="public",
    )

    op.create_index(
        "ix_m28_sharing_grant_tenant_scope",
        "m28_phase_28_interactive_dashboard_sharing_grant",
        ["tenant_id", "scope"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_m28_sharing_grant_expires_at",
        "m28_phase_28_interactive_dashboard_sharing_grant",
        ["expires_at"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_m28_sharing_grant_audit_trail_gin",
        "m28_phase_28_interactive_dashboard_sharing_grant",
        ["audit_trail"],
        unique=False,
        schema="public",
        postgresql_using="gin",
    )

    # ── 5. m28_phase_28_interactive_dashboard_preview (1 preview) ──────
    op.create_table(
        "m28_phase_28_interactive_dashboard_preview",
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("preview_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_key", sa.String(length=64), nullable=False),
        sa.Column("view_id", sa.String(length=128), nullable=True),
        sa.Column("preview_data", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "preview_id"),
        schema="public",
    )

    op.create_index(
        "ix_m28_preview_tenant_period",
        "m28_phase_28_interactive_dashboard_preview",
        ["tenant_id", "period_key"],
        unique=False,
        schema="public",
    )

    # ── RLS policies (CR 0-2 verbatim — 5 tables) ──────────────────────
    for table_name in [
        "m28_phase_28_interactive_dashboard_unified_kpi",
        "m28_phase_28_interactive_dashboard_saved_view",
        "m28_phase_28_interactive_dashboard_export_job",
        "m28_phase_28_interactive_dashboard_sharing_grant",
        "m28_phase_28_interactive_dashboard_preview",
    ]:
        op.execute(f"ALTER TABLE public.{table_name} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY {table_name}_tenant_isolation
            ON public.{table_name}
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
            """
        )


def downgrade() -> None:
    """Downgrade schema — drop Phase 28 5 tables in reverse order."""

    # Drop RLS policies + tables
    for table_name in [
        "m28_phase_28_interactive_dashboard_preview",
        "m28_phase_28_interactive_dashboard_sharing_grant",
        "m28_phase_28_interactive_dashboard_export_job",
        "m28_phase_28_interactive_dashboard_saved_view",
        "m28_phase_28_interactive_dashboard_unified_kpi",
    ]:
        op.execute(
            f"DROP POLICY IF EXISTS {table_name}_tenant_isolation " f"ON public.{table_name};"
        )
        op.drop_table(table_name, schema="public")
