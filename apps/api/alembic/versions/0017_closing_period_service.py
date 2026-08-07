"""Alembic 0017 — Story 6.1 closing period service schema.

Story 6.1 (T6 — Alembic 0017) — Closing Period Service schema extension.

`monthly_input_periods` table extensions (AD-6 fiscal-period close lock):
- ADD COLUMN `finalized_at` TIMESTAMP WITH TIME ZONE NULL
- ADD COLUMN `closed_by_actor_id` UUID NULL REFERENCES users(id)
- ADD COLUMN `closing_snapshot_event_count` INTEGER NOT NULL DEFAULT 0
- ADD COLUMN `status` TEXT NOT NULL DEFAULT 'open' (3-state lifecycle:
  open → closing → closed per AC #4 spec)
- ADD CONSTRAINT `chk_closing_period_status`
  CHECK (status IN ('open', 'closing', 'closed'))
- ADD CONSTRAINT `chk_closing_snapshot_event_count_non_negative`
  CHECK (closing_snapshot_event_count >= 0)

`audit_logs` table index (5-3 P3 review patch mirror for closing period):
- ADD INDEX `idx_closing_period_audit` (tenant_id, payload->>'period_key',
  occurred_at DESC) — supports `GET /api/v1/inventory/closing-period/audit-trail`
  JSONB extraction filter (CR 1.1 observability).

`inventory_ledger` table CHECK constraint expansion (A5 3-way drift):
- DROP existing 11-value event_type CHECK constraint
- ADD new 11-value event_type CHECK constraint with `closing_snapshot`
  (already in 0015 — no expansion needed in 0017)

Alembic chain: 0015 → 0016 → 0017 → 0018 (V4 verifier extension).

Migration strategy:
- ADD COLUMN NULL → backfill (no backfill needed; CI shim mode) →
  NOT NULL with default 0 for closing_snapshot_event_count.
- ADD CONSTRAINT CHECK status IN ('open', 'closing', 'closed') — 3-value
  1-way state machine per spec AC #4.

Revision ID: 0017_closing_period_service
Revises:    0016_verification_log_v3_audit
Create Date: 2026-08-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_closing_period_service"
down_revision = "0016_verification_log_v3_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply Story 6.1 closing period service schema extensions."""
    # monthly_input_periods — AD-6 fiscal-period close lock extensions.
    op.add_column(
        "monthly_input_periods",
        sa.Column(
            "finalized_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "monthly_input_periods",
        sa.Column(
            "closed_by_actor_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "monthly_input_periods",
        sa.Column(
            "closing_snapshot_event_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "monthly_input_periods",
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="open",
        ),
    )
    # Status CHECK constraint — guard against invalid status values.
    # 3-value state machine per AC #4 spec (open → closing → closed).
    op.create_check_constraint(
        "chk_closing_period_status",
        "monthly_input_periods",
        "status IN ('open', 'closing', 'closed')",
    )
    # Defense-in-depth: closing_snapshot_event_count ≥ 0.
    op.create_check_constraint(
        "chk_closing_snapshot_event_count_non_negative",
        "monthly_input_periods",
        "closing_snapshot_event_count >= 0",
    )
    # Closing-period audit trail index — supports JSONB extraction
    # filter on `payload->>'period_key'` (CR 1.1 observability).
    op.create_index(
        "idx_closing_period_audit",
        "audit_logs",
        ["tenant_id", sa.text("(payload->>'period_key')"), sa.text("occurred_at DESC")],
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Revert Story 6.1 closing period service schema extensions."""
    op.drop_index("idx_closing_period_audit", table_name="audit_logs")
    op.drop_constraint(
        "chk_closing_snapshot_event_count_non_negative",
        "monthly_input_periods",
        type_="check",
    )
    op.drop_constraint(
        "chk_closing_period_status",
        "monthly_input_periods",
        type_="check",
    )
    op.drop_column("monthly_input_periods", "status")
    op.drop_column("monthly_input_periods", "closing_snapshot_event_count")
    op.drop_column("monthly_input_periods", "closed_by_actor_id")
    op.drop_column("monthly_input_periods", "finalized_at")
