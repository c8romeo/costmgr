"""A5 3-way drift fix — verification_log CHECK constraint expansion for V4.

Story 6.1 (T6 follow-up) — closing_period V4 verification verifier.

Story 6.1 introduces `verify_v4_closing_period_consistency` in
`ActionClass.VERIFICATION` (audit_action.py extension from 1 → 2 values).

This action routes to the `verification_log` destination. Alembic 0016
expanded the verification_log CHECK constraint to 5 values to include
`verify_v3_closing_invariant`. This migration expands it to 6 values
to include `verify_v4_closing_period_consistency`.

3-way drift detector (`tests/integration/test_audit_action_consistency.py`)
pins this expansion. Without this migration, future inserts of
`verify_v4_closing_period_consistency` would fail with DB CHECK
constraint violation.

Revision ID: 0018_verification_log_v4_audit
Revises:    0017_closing_period_service
Create Date: 2026-08-07
"""

from __future__ import annotations

from alembic import op

revision = "0018_verification_log_v4_audit"
down_revision = "0017_closing_period_service"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Expand verification_log CHECK constraint to 6-value enum (V4)."""
    op.execute("ALTER TABLE verification_log DROP CONSTRAINT IF EXISTS chk_verification_log_action")
    op.execute(
        """
        ALTER TABLE verification_log
        ADD CONSTRAINT chk_verification_log_action
        CHECK (action IN (
            'verification_passed',
            'verification_failed',
            'verification_skipped',
            'verify_v8_golden_match',
            'verify_v3_closing_invariant',
            'verify_v4_closing_period_consistency'
        ))
        """
    )


def downgrade() -> None:
    """Restore the 5-value CHECK constraint (Alembic 0016 state)."""
    op.execute("ALTER TABLE verification_log DROP CONSTRAINT IF EXISTS chk_verification_log_action")
    op.execute(
        """
        ALTER TABLE verification_log
        ADD CONSTRAINT chk_verification_log_action
        CHECK (action IN (
            'verification_passed',
            'verification_failed',
            'verification_skipped',
            'verify_v8_golden_match',
            'verify_v3_closing_invariant'
        ))
        """
    )
