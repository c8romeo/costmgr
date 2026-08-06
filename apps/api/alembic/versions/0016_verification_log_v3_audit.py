"""A5 3-way drift fix — verification_log CHECK constraint expansion for V3.

Story 5.3 (T7 — Alembic 0016) — closing ≥ 0 invariant V3 verification.

Story 5.3 introduces `ActionClass.VERIFICATION` in
`apps/api/core/audit_action.py` with 1 action value:

    'verify_v3_closing_invariant'

This action routes to the `verification_log` destination (shared with
`ActionClass.VERIFICATION_LOG` — distinct action_class but same
destination table). Alembic 0014 expanded the verification_log CHECK
constraint to 4 values (verification_passed, verification_failed,
verification_skipped, verify_v8_golden_match). This migration expands
it to 5 values to include `verify_v3_closing_invariant`.

3-way drift detector (`tests/integration/test_audit_action_consistency.py`)
pins this expansion. Without this migration, future inserts of
`verify_v3_closing_invariant` would fail with DB CHECK constraint
violation — but the registry would silently accept the action
(TypeError on production write).

Audit-first pattern (CR 1.1): the ClosingGuardService emits
`v3_closing_invariant_verified` (audit_logs destination, ActionClass.CLOSING_GUARD)
AND `verify_v3_closing_invariant` (verification_log destination,
ActionClass.VERIFICATION) in sequence. The audit_logs destination has
NO CHECK constraint (text field); verification_log CHECK is the
production gate for the V3 verifier marker.

audit_logs table has NO `action` CHECK constraint (free-form text —
the registry is the only validation gate), so no migration is needed
for the new closing_guard actions (closing_guard_violated,
closing_guard_passed, v3_closing_invariant_verified). The 3-way drift
detector does NOT apply to audit_logs.

Migration strategy:
- DROP the existing CHECK constraint
- ADD a new CHECK constraint with the 5-value enum
- This is safe because no production data exists yet (CI shim mode)

If a tenant has production data with `verify_v3_closing_invariant` rows,
the DROP will fail — handle via data-driven migration in production.

Revision ID: 0016_verification_log_v3_audit
Revises:    0015_inventory_ledger
Create Date: 2026-08-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0016_verification_log_v3_audit"
down_revision: str | Sequence[str] | None = "0015_inventory_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── A5 3-way drift fix: expand verification_log CHECK constraint ──
    # The constraint was created in 0013 with 3 values, expanded in 0014
    # to 4 values (V8 forward-lock). Story 5.3 adds `verify_v3_closing_invariant`
    # (5th value) for V3 closing ≥ 0 invariant verifier. This migration
    # closes the 3-way drift.
    #
    # DROPPING + ADDING a named constraint is the idiomatic Alembic
    # pattern. The constraint name `verification_log_action_check` is
    # PostgreSQL's auto-generated name for the inline CHECK in 0013/0014.
    op.execute(
        "ALTER TABLE verification_log " "DROP CONSTRAINT IF EXISTS verification_log_action_check"
    )
    op.execute(
        """
        ALTER TABLE verification_log
        ADD CONSTRAINT verification_log_action_check
        CHECK (action IN (
            'verification_passed',
            'verification_failed',
            'verification_skipped',
            'verify_v8_golden_match',
            'verify_v3_closing_invariant'
        ))
        """
    )
    # Update the table comment to reflect the 5-value enum
    op.execute(
        """
        COMMENT ON TABLE verification_log IS
        'Story 4.3 AD-12 verification-first audit ledger. Written by '
        'CalcOrchestrator._write_verification_log in the same REPEATABLE READ '
        'transaction as calc_log + fiscal_period_snapshots. action CHECK '
        'constraint matches apps/api/core/audit_action.py registry '
        'ActionClass.VERIFICATION_LOG (4-value enum) + ActionClass.VERIFICATION '
        '(1-value enum: verify_v3_closing_invariant — Story 5.3 V3 forward-lock). '
        'Total 5-value enum: verification_passed, verification_failed, '
        'verification_skipped, verify_v8_golden_match, verify_v3_closing_invariant.'
        """
    )

    # ── Story 5.3 P3 review patch — closing-guard infrastructure ──
    # (1) monthly_input_rows.created_via + manual-edit reject CHECK.
    #     Story 5.1 manual_edit_reject already exists at the service
    #     layer, but a bulk-import SQL path can bypass the service.
    #     The CHECK constraint closes the L8 deferred-work bypass.
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS created_via VARCHAR(32) NOT NULL DEFAULT 'user_save'
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD CONSTRAINT chk_opening_inventory_manual_reject
        CHECK (stream != 'opening_inventory' OR (stream = 'opening_inventory' AND created_via = 'auto_carry'))
        """
    )
    # (2) idx_closing_guard_audit — tenant-scoped period_key lookup
    #     for the audit-trail route. `period_key` lives in payload JSONB
    #     (audit_logs table has no `period_key` / `created_at` columns),
    #     so the index extracts it via JSONB expression.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_closing_guard_audit
        ON audit_logs (tenant_id, (payload->>'period_key'), occurred_at DESC)
        """
    )


def downgrade() -> None:
    # Restore the 4-value CHECK constraint (Alembic 0014 state)
    op.execute(
        "ALTER TABLE verification_log " "DROP CONSTRAINT IF EXISTS verification_log_action_check"
    )
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
    op.execute(
        """
        COMMENT ON TABLE verification_log IS
        'Story 4.3 AD-12 verification-first audit ledger. action CHECK '
        'constraint matches apps/api/core/audit_action.py registry '
        'ActionClass.VERIFICATION_LOG accepted set (4-value enum: '
        'verification_passed, verification_failed, verification_skipped, '
        'verify_v8_golden_match — Story 4.4 V8 forward-lock).'
        """
    )
    # Drop the Story 5.3 closing-guard additions.
    op.execute("DROP INDEX IF EXISTS idx_closing_guard_audit")
    op.execute(
        "ALTER TABLE monthly_input_rows "
        "DROP CONSTRAINT IF EXISTS chk_opening_inventory_manual_reject"
    )
    op.execute(
        "ALTER TABLE monthly_input_rows " "DROP COLUMN IF EXISTS created_via"
    )
