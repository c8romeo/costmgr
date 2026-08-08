"""Story 11.2 — fiscal_periods + 4-stage close sequence state.

AD-6 close lock + 4-stage close_sequence_state (divisions → manufacturing
→ abc → common → confirmed) + partial close guard (PRD §F11.1 +
PRD §8.M11(a)).

down_revision: 0019_m11_reversal_ledger (Story 11.1 wire tip).

Per AD-6 (Architecture Spine):
  "rows bounded by `fiscal_periods.status='closed'` reject business-data
  INSERTs except AD-22 reversal/correction events"

Per AD-22 (Architecture Spine):
  "sign-negating + corrected row INSERT + correction_group_id link"
  (11-1 wire already established; 11-2 wire adds the fiscal_periods
  status gate that reverse-direction reversal INSERTs must also clear).

Per AD-24 (typed period-key): period_key = 'YYYY-MM' SSOT.

Revision ID: 0020_fiscal_periods_close_sequence
Revises:    0019_m11_reversal_ledger
Create Date: 2026-08-08
"""

from __future__ import annotations

from alembic import op

revision = "0020_fiscal_periods_close_sequence"
down_revision = "0019_m11_reversal_ledger"
branch_labels = None
depends_on = None


# Close sequence state values (mirror of TS/CloseSequenceState).
_CLOSE_SEQUENCE_STATES: tuple[str, ...] = (
    "divisions",
    "manufacturing",
    "abc",
    "common",
    "confirmed",
)
# fiscal_periods.status values.
_STATUS_VALUES: tuple[str, ...] = ("open", "closing", "closed", "reversed")


def upgrade() -> None:
    """Story 11.2 — fiscal_periods greenfield + 4-stage state machine.

    1. CREATE TABLE fiscal_periods with PK + 11 columns.
    2. CHECK constraints: status (4-state) + close_sequence_state (5-state)
       + 3 stage-ordering checks + 2 consistency checks.
    3. UNIQUE (tenant_id, period_key).
    4. INDEX x2 (tenant_period + close_sequence_state).
    """
    # ── 1. CREATE TABLE fiscal_periods ──────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fiscal_periods (
            id                              UUID PRIMARY KEY
                                              DEFAULT gen_random_uuid(),
            tenant_id                       UUID NOT NULL
                                              REFERENCES tenants(id)
                                              ON DELETE RESTRICT,
            period_key                      TEXT NOT NULL
                                              CHECK (period_key ~ '^\\d{4}-(0[1-9]|1[0-2])$'),
            status                          TEXT NOT NULL DEFAULT 'open',
            divisions_completed_at          TIMESTAMPTZ NULL,
            manufacturing_completed_at      TIMESTAMPTZ NULL,
            abc_completed_at                TIMESTAMPTZ NULL,
            common_completed_at             TIMESTAMPTZ NULL,
            close_sequence_state            TEXT NOT NULL DEFAULT 'divisions',
            close_sequence_blocked_reason_ko TEXT NULL,
            closed_at                       TIMESTAMPTZ NULL,
            closed_by_actor_id              UUID NULL
                                              REFERENCES users(id)
                                              ON DELETE SET NULL,
            created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT fiscal_periods_status_check
                CHECK (status IN ('open', 'closing', 'closed', 'reversed')),
            CONSTRAINT fiscal_periods_close_sequence_state_check
                CHECK (close_sequence_state IN
                       ('divisions', 'manufacturing', 'abc', 'common', 'confirmed')),
            -- Defense-in-depth stage ordering checks (mirror
            -- close_sequence_order.py pure-kernel invariants). The
            -- service-layer pure kernel is the SSOT — these checks
            -- catch direct-SQL regressions that bypass the service.
            CONSTRAINT fiscal_periods_divisions_ordering_check
                CHECK (divisions_completed_at IS NOT NULL
                       OR manufacturing_completed_at IS NULL),
            CONSTRAINT fiscal_periods_manufacturing_ordering_check
                CHECK (manufacturing_completed_at IS NOT NULL
                       OR abc_completed_at IS NULL),
            CONSTRAINT fiscal_periods_abc_ordering_check
                CHECK (abc_completed_at IS NOT NULL
                       OR common_completed_at IS NULL),
            -- close_sequence_state='confirmed' requires status='closed'
            -- (PRD §F11.1 — confirmed = final state).
            CONSTRAINT fiscal_periods_confirmed_requires_closed_check
                CHECK (close_sequence_state != 'confirmed' OR status = 'closed'),
            -- status='closed' requires closed_at populated (audit trail).
            CONSTRAINT fiscal_periods_closed_requires_closed_at_check
                CHECK (status != 'closed' OR closed_at IS NOT NULL),
            CONSTRAINT fiscal_periods_tenant_period_unique
                UNIQUE (tenant_id, period_key)
        )
        """
    )

    # ── 2. INDEX for RLS-scoped lookup (tenant_id, period_key) ──
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fiscal_periods_tenant_period
        ON fiscal_periods (tenant_id, period_key)
        """
    )

    # ── 3. INDEX for partial close detection (tenant_id, state) ──
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fiscal_periods_close_sequence_state
        ON fiscal_periods (tenant_id, close_sequence_state)
        """
    )


def downgrade() -> None:
    """Reverse Story 11.2 schema changes."""
    op.execute("DROP INDEX IF EXISTS idx_fiscal_periods_close_sequence_state")
    op.execute("DROP INDEX IF EXISTS idx_fiscal_periods_tenant_period")
    op.execute("DROP TABLE IF EXISTS fiscal_periods")
