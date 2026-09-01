"""Story 11.1 — M11 reversal sequence + AD-25 cache invalidation column.

This migration adds the `reversal_of_period_key` column to the
`inventory_ledger` table for AD-22 reversal sequence.

Per AD-22:
- reversal_negating row's `period_key` = the current period where
  the new row lives.
- `reversal_of_period_key` = the original event's period_key (may
  differ if the corrected row crosses periods).

This allows the GET reversal_history endpoint to read the original
period_key for cross-period corrections (e.g., correction that
moves a row from 2026-08 to 2026-09).

Also adds:
- A new `reversal_log` table for AD-22 reversal history observability
  (Future Epic 11-3 expansion; 11-1 ship is 0-row by default).
- A new `cache_invalidation_log` table for AD-25 receipt audit
  (1-channel: ai_cache).
- (tenant_id, reverses_event_id) PARTIAL UNIQUE INDEX to prevent
  re-reversal of the same target (Alembic 0015 forward-fill).

Revision ID: 0019_m11_reversal_ledger
Revises:    0018_verification_log_v4_audit
Create Date: 2026-08-08
"""

from __future__ import annotations

from alembic import op

revision = "0019_m11_reversal_ledger"
down_revision = "0018_verification_log_v4_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Story 11.1 — AD-22 reversal + AD-25 cache invalidation wire.

    1. Add `reversal_of_period_key` column to `inventory_ledger` (AD-22).
    2. Create `reversal_log` table (AD-22 history observability).
    3. Create `cache_invalidation_log` table (AD-25 receipt audit).
    4. Add (tenant_id, reverses_event_id) PARTIAL UNIQUE INDEX to
       prevent re-reversal of the same target.
    """
    # ── 1. Add `reversal_of_period_key` column ─────────────────
    op.execute(
        """
        ALTER TABLE inventory_ledger
        ADD COLUMN IF NOT EXISTS reversal_of_period_key TEXT NULL
        """
    )

    # ── 1.1. AD-24 typed period_key CHECK (reversal_of_period_key) ─
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'inventory_ledger_reversal_of_period_key_format_check'
            ) THEN
                ALTER TABLE inventory_ledger
                ADD CONSTRAINT inventory_ledger_reversal_of_period_key_format_check
                CHECK (
                    reversal_of_period_key IS NULL
                    OR reversal_of_period_key ~ '^\\d{4}-(0[1-9]|1[0-2])$'
                );
            END IF;
        END$$;
        """
    )

    # ── 2. AD-22 (tenant_id, reverses_event_id) PARTIAL UNIQUE INDEX ─
    # D4 — REMOVED. Alembic 0015_inventory_ledger already created this
    # PARTIAL UNIQUE INDEX. Re-creating here would fail with
    # `relation already exists`. The 0015 wire is the SSOT.

    # ── 3. Create `reversal_log` table (AD-22 history) ─────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS reversal_log (
            reversal_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id            UUID NOT NULL
                                 REFERENCES tenants(id) ON DELETE RESTRICT,
            correction_group_id  UUID NOT NULL,
            target_event_id      UUID NOT NULL,
            negating_event_id    UUID NOT NULL,
            corrected_event_id   UUID NULL,
            actor_id             UUID NOT NULL,
            reason               TEXT NOT NULL,
            period_key           TEXT NOT NULL,
            reversal_of_period_key TEXT NULL,
            payload              JSONB NOT NULL DEFAULT '{}'::jsonb,
            trace_id             UUID NOT NULL,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    # AD-22 reversal_log info only (NO action CHECK — this is a
    # bookkeeping table, not an audit_log action destination).
    # Index for correction_group_id lookup.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_reversal_log_correction_group_id
        ON reversal_log (correction_group_id)
        """
    )

    # ── 4. Create `cache_invalidation_log` table (AD-25 audit) ──
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cache_invalidation_log (
            receipt_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id            UUID NOT NULL
                                 REFERENCES tenants(id) ON DELETE RESTRICT,
            channel              TEXT NOT NULL
                                 CHECK (channel IN ('ai_cache')),
            target_event_id      UUID NOT NULL,
            correction_group_id  UUID NULL,
            trace_id             UUID NOT NULL,
            published_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    # AD-25 1-channel publisher audit log index.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_cache_invalidation_log_correction_group_id
        ON cache_invalidation_log (correction_group_id)
        """
    )


def downgrade() -> None:
    """Reverse all 11.1 schema changes."""
    op.execute("DROP TABLE IF EXISTS cache_invalidation_log")
    op.execute("DROP TABLE IF EXISTS reversal_log")
    op.execute("DROP INDEX IF EXISTS uq_inventory_ledger_reverses_event_id")
    op.execute(
        """
        ALTER TABLE inventory_ledger
        DROP CONSTRAINT IF EXISTS inventory_ledger_reversal_of_period_key_format_check
        """
    )
    op.execute(
        """
        ALTER TABLE inventory_ledger
        DROP COLUMN IF EXISTS reversal_of_period_key
        """
    )
