"""A5 3-way drift fix — verification_log CHECK constraint expansion.

Story 4.4 forward-lock: `verify_v8_golden_match` action was added to
`apps/api/core/audit_action.py` `_ActionRegistry._REGISTRY[VERIFICATION_LOG]`
in the V8 골든 byte-identical CI gate commit (80f4494). However, the
original Alembic 0013 (`0013_verification_log.py`) CHECK constraint only
allowed 3 values:

    action IN ('verification_passed', 'verification_failed', 'verification_skipped')

This migration expands the CHECK constraint to include the 4th value
required by the registry:

    action IN ('verification_passed', 'verification_failed',
               'verification_skipped', 'verify_v8_golden_match')

3-way drift detector (`tests/integration/test_audit_action_consistency.py`)
caught this drift at A5 close-out. Without this migration, future inserts
of `verify_v8_golden_match` would fail with DB CHECK constraint violation
— but the registry would silently accept the action (TypeError on
production write).

Audit-first pattern (CR 1.1): the orchestrator's V8 골든 mismatch path
writes `_ActionRegistry.validate(action_class=ActionClass.VERIFICATION_LOG,
action='verify_v8_golden_match')` BEFORE the INSERT. The DB CHECK is the
production gate; the registry is the early-fail guard.

Migration strategy:
- DROP the existing CHECK constraint
- ADD a new CHECK constraint with the 4-value enum
- This is safe because no production data exists yet (CI shim mode)

If a tenant has production data with `verify_v8_golden_match` rows, the
DROP will fail — handle via data-driven migration in production. Since
Epic 4 close-out is the first time this drift is caught, the production
data path is deferred to Epic 5+ when real tenants onboard.

Revision ID: 0014_verification_log_v8_audit
Revises:    0013_verification_log
Create Date: 2026-08-03
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0014_verification_log_v8_audit"
down_revision: str | Sequence[str] | None = "0013_verification_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── A5 3-way drift fix: expand verification_log CHECK constraint ──
    # The constraint was created in 0013 with 3 values. Story 4.4 added
    # `verify_v8_golden_match` to the registry but did NOT update the DB
    # CHECK constraint. This migration closes the 3-way drift.
    #
    # DROPPING + ADDING a named constraint is the idiomatic Alembic
    # pattern. The constraint name `verification_log_action_check` is
    # PostgreSQL's auto-generated name for the inline CHECK in 0013.
    op.execute("ALTER TABLE verification_log DROP CONSTRAINT IF EXISTS verification_log_action_check")
    op.execute(
        """
        ALTER TABLE verification_log
        ADD CONSTRAINT verification_log_action_check
        CHECK (action IN (
            'verification_passed',
            'verification_failed',
            'verification_skipped',
            'verify_v8_golden_match'
        ))
        """
    )
    # Update the table comment to reflect the 4-value enum
    op.execute(
        """
        COMMENT ON TABLE verification_log IS
        'Story 4.3 AD-12 verification-first audit ledger. Written by '
        'CalcOrchestrator._write_verification_log in the same REPEATABLE READ '
        'transaction as calc_log + fiscal_period_snapshots. action CHECK '
        'constraint matches apps/api/core/audit_action.py registry '
        'ActionClass.VERIFICATION_LOG accepted set (4-value enum: '
        'verification_passed, verification_failed, verification_skipped, '
        'verify_v8_golden_match — Story 4.4 V8 forward-lock).'
        """
    )


def downgrade() -> None:
    # Restore the original 3-value CHECK constraint
    op.execute("ALTER TABLE verification_log DROP CONSTRAINT IF EXISTS verification_log_action_check")
    op.execute(
        """
        ALTER TABLE verification_log
        ADD CONSTRAINT verification_log_action_check
        CHECK (action IN (
            'verification_passed',
            'verification_failed',
            'verification_skipped'
        ))
        """
    )
    # Note: downgrade will fail if any rows have action='verify_v8_golden_match'.
    # This is intentional — the 4th value is part of Story 4.4 forward-lock.
