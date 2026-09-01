"""alembic version 0058 — Phase 26 FinOps Cost Anomaly ML Prediction preview table.

Revision ID: 0058_phase_26_cost_anomaly_ml_prediction
Revises: 0057_phase_25_vendor_management
Create Date: 2026-08-28 (KST)

Phase 26 wire (cj-style 181번째) — FinOps Cost Anomaly ML Prediction
pre-detection layer (PRD §F42 + AD-55 (a)~(g) verbatim).

This migration adds 1 preview table for Phase 26:
- m34_phase_26_cost_anomaly_ml_prediction_preview (preview column-only,
  no actual INSERT semantics, returns None until wire cycle next sprint)

NFR4 PII minimization PRESERVED — no employee PII data, only business
metrics + cost amounts + model artifacts.

CR lessons applied:
- CR 0-2 RLS — tenant_id column selector + RLS policy.
- CR 1-1 audit-first INSERT — audit_action column preserved.
- CR 5-1 Decimal NUMERIC(18,2) — all KRW currency amounts.
- AD-22 owner-only RBAC.
- AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0058_phase_26_cost_anomaly_ml_prediction"
down_revision = "0057_phase_25_vendor_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema — Phase 26 cost_anomaly_ml_prediction preview table."""
    op.create_table(
        "m34_phase_26_cost_anomaly_ml_prediction_preview",
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prediction_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model_type", sa.String(length=32), nullable=False),
        sa.Column("period_key", sa.String(length=64), nullable=False),
        sa.Column(
            "predicted_cost_krw",
            sa.dialects.postgresql.NUMERIC(precision=18, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "predicted_anomaly_score",
            sa.dialects.postgresql.NUMERIC(precision=5, scale=4),
            nullable=False,
            server_default="0.0000",
        ),
        sa.Column("ml_anomaly_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("drift_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("inference_latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "prediction_id"),
        schema="public",
    )

    # Indexes
    op.create_index(
        "ix_m34_phase_26_cost_anomaly_ml_prediction_tenant_period",
        "m34_phase_26_cost_anomaly_ml_prediction_preview",
        ["tenant_id", "period_key"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_m34_phase_26_cost_anomaly_ml_prediction_model_type",
        "m34_phase_26_cost_anomaly_ml_prediction_preview",
        ["model_type"],
        unique=False,
        schema="public",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        """
        ALTER TABLE public.m34_phase_26_cost_anomaly_ml_prediction_preview
        ENABLE ROW LEVEL SECURITY;
        """
    )
    op.execute(
        """
        CREATE POLICY m34_phase_26_cost_anomaly_ml_prediction_tenant_isolation
        ON public.m34_phase_26_cost_anomaly_ml_prediction_preview
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
        """
    )


def downgrade() -> None:
    """Downgrade schema — drop Phase 26 preview table."""
    op.execute(
        "DROP POLICY IF EXISTS m34_phase_26_cost_anomaly_ml_prediction_tenant_isolation "
        "ON public.m34_phase_26_cost_anomaly_ml_prediction_preview;"
    )
    op.drop_index(
        "ix_m34_phase_26_cost_anomaly_ml_prediction_model_type",
        table_name="m34_phase_26_cost_anomaly_ml_prediction_preview",
        schema="public",
    )
    op.drop_index(
        "ix_m34_phase_26_cost_anomaly_ml_prediction_tenant_period",
        table_name="m34_phase_26_cost_anomaly_ml_prediction_preview",
        schema="public",
    )
    op.drop_table(
        "m34_phase_26_cost_anomaly_ml_prediction_preview",
        schema="public",
    )
