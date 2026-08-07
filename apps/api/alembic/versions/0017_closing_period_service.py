"""Alembic 0017 — Story 6.1 closing period service schema.

Story 6.1 (T6 — Alembic 0017) — Closing Period Service schema extension.

`monthly_input_periods` table extensions:
- ADD COLUMN `finalized_at` TIMESTAMP WITH TIME ZONE NULL
- ADD COLUMN `closed_by_actor_id` UUID NULL REFERENCES users(id)
- ADD COLUMN `closing_snapshot_event_count` INTEGER NOT NULL DEFAULT 0
- ADD CONSTRAINT `chk_closing_period_status` CHECK (status IN ('open', 'closed'))

`inventory_ledger` table CHECK constraint expansion (A5 3-way drift):
- DROP existing 11-value event_type CHECK constraint
- ADD new 11-value event_type CHECK constraint with `closing_snapshot`
  (already in 0015 — no expansion needed in 0017)

`audit_logs` table: NO CHECK constraint (free-form text — registry is
the only validation gate). No migration needed for `closing_period_*`
3 actions (closing_period_confirmed, closing_period_blocked,
closing_period_snapshot_inconsistency) or V4 verifier extension
(verify_v4_closing_period_consistency) since `verify_*` actions route
to `verification_log` which already has its CHECK expanded by 0016.

Alembic chain: 0015 → 0016 → 0017 → (planned 0018 for 6-2 / 6-3).

Migration strategy:
- ADD COLUMN NULL → backfill (no backfill needed; CI shim mode) →
  NOT NULL with default 0 for closing_snapshot_event_count.
- ADD CONSTRAINT CHECK status IN ('open', 'closed').

Revision ID: 0017_closing_period_service
Revises:    0016_verification_log_v3_audit
Create Date: 2026-08-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ── Alembic migration metadata ──────────────────────────────────
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
    # Status CHECK constraint — guard against invalid status values.
    op.create_check_constraint(
        "chk_closing_period_status",
        "monthly_input_periods",
        "status IN ('open', 'closed')",
    )


def downgrade() -> None:
    """Revert Story 6.1 closing period service schema extensions."""
    op.drop_constraint(
        "chk_closing_period_status",
        "monthly_input_periods",
        type_="check",
    )
    op.drop_column("monthly_input_periods", "closing_snapshot_event_count")
    op.drop_column("monthly_input_periods", "closed_by_actor_id")
    op.drop_column("monthly_input_periods", "finalized_at")
