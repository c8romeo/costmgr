"""Story 11.3 — AD-25 cache invalidation multi-channel expansion.

Story 11.1 wire (`0019_m11_reversal_ledger`) introduced the
`cache_invalidation_log` table with a 1-channel CHECK constraint
(`channel IN ('ai_cache')`). Story 11.3 expands the channel set
to 4 channels for AD-25 multi-channel publisher wire:

  - `ai_cache`               — M10 AI cache invalidation (11-1 wire 보존)
  - `cost_engine_cache`      — M3 cost engine calculation result cache (11-3 NEW)
  - `fiscal_period_cache`    — M11 fiscal_periods + fiscal_period_snapshots
                                metadata cache (11-3 NEW)
  - `closing_snapshot_cache` — M11 closing_snapshot + ledger closing event
                                cache (11-3 NEW)

Down revision: 0020_fiscal_periods_close_sequence (Story 11.2 tip).

Per AD-25:
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Per AD-2: append-only ledger — `cache_invalidation_log` retains
insert-only semantics (no UPDATE/DELETE triggers added; receipt
record is immutable after publish).

Per AD-24: trace_id is UUID (not TEXT) to match 11-1 wire convention.

Revision ID: 0021_cache_invalidation_multi_channel
Revises:    0020_fiscal_periods_close_sequence
Create Date: 2026-08-09
"""

from __future__ import annotations

from alembic import op

revision = "0021_cache_invalidation_multi_channel"
down_revision = "0020_fiscal_periods_close_sequence"
branch_labels = None
depends_on = None


# Channel values (Story 11.3 multi-channel expansion).
# Mirrored in apps/api/core/cache_invalidation_publisher.py:ALLOWED_CHANNELS.
_ALLOWED_CHANNELS_11_3: tuple[str, ...] = (
    "ai_cache",
    "cost_engine_cache",
    "fiscal_period_cache",
    "closing_snapshot_cache",
)


def upgrade() -> None:
    """Story 11.3 — AD-25 multi-channel expansion.

    1. DROP the 1-channel CHECK constraint from `cache_invalidation_log`.
    2. ADD a new CHECK constraint that accepts all 4 channels.
    3. Add per-channel indexes for query performance
       (cache_invalidation_log lookup by channel + tenant_id).
    """
    # ── 1. Drop the 1-channel CHECK constraint (Story 11.1 wire) ──
    op.execute(
        """
        ALTER TABLE cache_invalidation_log
        DROP CONSTRAINT IF EXISTS cache_invalidation_log_channel_check
        """
    )

    # ── 2. Add the 4-channel CHECK constraint (Story 11.3 wire) ──
    # Build the IN-list dynamically from the tuple (frozen at migration
    # generation time; future channel additions require explicit migration).
    in_clause = ", ".join(f"'{c}'" for c in _ALLOWED_CHANNELS_11_3)
    op.execute(
        f"""
        ALTER TABLE cache_invalidation_log
        ADD CONSTRAINT cache_invalidation_log_channel_check
        CHECK (channel IN ({in_clause}))
        """
    )

    # ── 3. Per-channel indexes ─────────────────────────────────
    # Query patterns:
    #   - audit lookup by channel + tenant_id
    #   - correction_group_id → channels fanned out
    # 4 channels × (tenant_id + channel) covers the typical
    # `SELECT … WHERE tenant_id = … AND channel = … ORDER BY published_at DESC`
    # access pattern.
    for channel in _ALLOWED_CHANNELS_11_3:
        # Index name: 64-char Postgres identifier limit; truncate safely.
        idx_name = f"ix_cache_inv_log_ch_{channel[:30]}"
        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {idx_name}
            ON cache_invalidation_log (tenant_id, channel, published_at DESC)
            """
        )

    # ── 4. Document the channel set ───────────────────────────
    op.execute(
        f"""
        COMMENT ON COLUMN cache_invalidation_log.channel IS
        'AD-25 cache invalidation channel. Story 11.3 expansion: '
        'ai_cache | cost_engine_cache | fiscal_period_cache | closing_snapshot_cache. '
        'Allowed set = ({", ".join(_ALLOWED_CHANNELS_11_3)}).'
        """
    )


def downgrade() -> None:
    """Reverse Story 11.3 channel expansion.

    WARNING: this downgrade will fail if any row in
    `cache_invalidation_log` has a channel outside the 1-channel set
    (i.e., any `cost_engine_cache` / `fiscal_period_cache` /
    `closing_snapshot_cache` row written after 11-3). Operators MUST
    archive + delete those rows before downgrading.
    """
    # Drop per-channel indexes.
    for channel in _ALLOWED_CHANNELS_11_3:
        idx_name = f"ix_cache_inv_log_ch_{channel[:30]}"
        op.execute(f"DROP INDEX IF EXISTS {idx_name}")

    # Drop the 4-channel CHECK.
    op.execute(
        """
        ALTER TABLE cache_invalidation_log
        DROP CONSTRAINT IF EXISTS cache_invalidation_log_channel_check
        """
    )

    # Restore the 1-channel CHECK.
    op.execute(
        """
        ALTER TABLE cache_invalidation_log
        ADD CONSTRAINT cache_invalidation_log_channel_check
        CHECK (channel IN ('ai_cache'))
        """
    )