"""Verification Log — Epic 4 Story 4.3

Story 4.3 (Task 4.1) — AD-12 verification_log INSERT for V1·V4·V7·V8
verification-first invariant.

Adds ONE table to back the verification surface for `POST /api/v1/calc`:

1. ``verification_log`` — auditing the AD-12 verification-first invariant.
   Written by `CalcOrchestrator._write_verification_log` in the same
   REPEATABLE READ transaction as `calc_log` (audit-first, CR 1.1 lesson).
   `action` is `verification_passed` (all V1·V4·V7·V8 fired rules passed),
   `verification_failed` (first-failed V-row triggered ROLLBACK), or
   `verification_skipped` (no rule fired for the industry — e.g. service
   tenants where V7 is the only applicable; reserved for future use).

   AD-8: KRW fields are NOT applicable — verification_log is metadata
   only (no monetary columns). AD-16: `result_hash` is the same
   deterministic SHA-256 64-hex carried by the engine's CalcResult.

   This is the SECOND table in the M3 module to use a DB CHECK constraint
   on `action` (the first was `calc_log` in 0012). The CHECK is the
   contract surface that `apps/api/core/audit_action.py` registry
   validates against in production writes — drift detector (Phase 4) will
   enforce 3-way consistency (registry vs DB CHECK vs call sites).

RLS scope (CR 0.2 lesson) — `app.tenant_id` GUC pattern, same as 0012.

Revision ID: 0013_verification_log
Revises:    0012_fiscal_period_snapshots
Create Date: 2026-08-02
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0013_verification_log"
down_revision: str | Sequence[str] | None = "0012_fiscal_period_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── verification_log (Story 4.3 — Task 4.1) ─────────────────
    # Audit-first ledger (CR 1.1 lesson) for AD-12 verification surface.
    # Written by `CalcOrchestrator._write_verification_log` IN THE SAME
    # REPEATABLE READ transaction as `calc_log` (and BEFORE
    # `fiscal_period_snapshots` INSERT). For verification_failed, the
    # orchestrator still writes this row before ROLLBACK — audit row
    # surviving the rollback is NOT expected; the row is part of the
    # same transaction and gets rolled back with the snapshot.
    #
    # IMPORTANT: For verification_failed, the audit row is REVERTED by
    # the rollback. The PURPOSE of writing it before rollback is so that
    # if the rollback itself fails (e.g. constraint violation), the
    # audit trail captures the failure attempt. For verification_passed,
    # the row is committed alongside the snapshot.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS verification_log (
            verification_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            period_key TEXT NOT NULL,
            baseline_revision INTEGER NOT NULL,
            action TEXT NOT NULL CHECK (
                action IN ('verification_passed', 'verification_failed', 'verification_skipped')
            ),
            top_failure_code TEXT,
            top_failure_message_ko TEXT,
            result_hash TEXT NOT NULL,
            trace_id TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_verification_log_tenant_period
            ON verification_log(tenant_id, period_key, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_verification_log_result_hash
            ON verification_log(result_hash)
        """
    )
    op.execute(
        """
        COMMENT ON TABLE verification_log IS
        'Story 4.3 AD-12 verification-first audit ledger. Written by '
        'CalcOrchestrator._write_verification_log in the same REPEATABLE READ '
        'transaction as calc_log + fiscal_period_snapshots. action CHECK '
        'constraint matches apps/api/core/audit_action.py registry '
        'ActionClass.VERIFICATION_LOG accepted set (3-value enum).'
        """
    )

    # ── RLS policies (CR 0.2 lesson) ─────────────────────────────
    op.execute("ALTER TABLE verification_log ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE verification_log FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY verification_log_tenant_isolation ON verification_log
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS verification_log_tenant_isolation ON verification_log")
    op.execute("DROP TABLE IF EXISTS verification_log")
