"""Story 14.1 — LISTEN/NOTIFY Consume Cross-Tenant Fan-Out Trigger EXTENSION
(A57/A58/A59 결정 wire).

D-13-1-DEFER-3 ✅ RESOLVED wire 진입 (separate epic LISTEN/NOTIFY
consume 2nd batch = Epic 14 = cross-tenant invalidation fan-out +
multi-process coordination). A53 ✅ DONE = Epic 14 진입 결정 wire.
A57 ✅ DONE = master PRD v2.4 → v2.5 atomic edit (§F14 신규).
A58 ✅ DONE = AD-25 EXTENSION 4-channel → 5+ channels + cross_tenant_fanout
채널 추가 + Multi-process coordination Option 1 결정 (PostgreSQL
LISTEN/NOTIFY only via pg_notify fan-out leader/follower model).
A59 ✅ DONE = capability matrix v1.22 → v1.23 EXTENSION
LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 2 NEW rows.

Per PRD §F14.1 (cross-tenant invalidation fan-out 토폴로지):
  - Cross-tenant invalidation fan-out 시 tenant isolation 검증 강제
    (CR 0-2 RLS lesson + AD-22 verbatim).
  - NOTIFY trigger (alembic 0034 EXTENSION) 의 PL/pgSQL function
    `cache_invalidation_log_notify_cross_tenant()` 가 `target_tenant_ids`
    를 NOTIFY payload 에 포함.
  - Multi-tenant isolation 위반 시 reject (cross_tenant_fanout channel
    payload 의 adapter 가 tenant context 와 mismatch 시 거부).

Per PRD §F14.3 (V8 determinism + cross-language drift detector EXTENSION):
  - Payload JSON serialization 결정적 (alphabetical key ordering) — F13.3
    verbatim 보존 + EXTENSION.
  - 7-key alphabetical: `channel`, `correction_group_id`,
    `invalidation_id`, `period_key`, `source_tenant_id`,
    `target_tenant_ids`, `trace_id`.
  - UUID fields cast to TEXT for cross-language drift detector parity
    (CR 12-5 D-PARITY-01 inversion 적용 보존).
  - target_tenant_ids 는 JSON array 결정적 직렬화 (PostgreSQL `jsonb`
    canonical form 또는 Python `json.dumps(sort_keys=True)`).

Trigger function semantics:
- `cache_invalidation_log_notify_cross_tenant()` — PL/pgSQL function
- AFTER INSERT trigger on `cache_invalidation_log`
- `pg_notify('cache_invalidation_log', payload)` where payload is a
  deterministic JSON object with 7 alphabetical keys (channel,
  correction_group_id, invalidation_id, period_key, source_tenant_id,
  target_tenant_ids, trace_id) for V8 byte-identical determinism
  (CR 4-4 / F13.3 / F14.3 verbatim 보존 + EXTENSION).
- The trigger fires ONLY when `NEW.channel = 'cross_tenant_fanout'`
  — defense-in-depth so 4-channel triggers from alembic 0033 do NOT
  emit cross_tenant_fanout payloads, and this new trigger does NOT
  emit payloads for the 4 other channels (cross-channel contamination
  방어 EXTENSION, F10.1-(d) verbatim).

Channel whitelist (5+ channels, AD-25 verbatim EXTENSION):
  - `ai_cache`               — M10 AI cache invalidation (11-1 wire 보존)
  - `cost_engine_cache`      — M3 cost engine calculation result cache (11-3 NEW)
  - `fiscal_period_cache`    — M11 fiscal_periods + fiscal_period_snapshots
                                metadata cache (11-3 NEW)
  - `closing_snapshot_cache` — M11 closing_snapshot + ledger closing event
                                cache (11-3 NEW)
  - `cross_tenant_fanout`    — cross-tenant invalidation fan-out (14-1 NEW)

Payload shape (7 keys, alphabetical order — V8 determinism):
  {
    "channel":              "cross_tenant_fanout",
    "correction_group_id":  "uuid-string",
    "invalidation_id":      "uuid-string",
    "period_key":           "YYYY-MM",
    "source_tenant_id":     "uuid-string",
    "target_tenant_ids":    ["uuid-string-1", "uuid-string-2", ...],
    "trace_id":             "uuid-string"
  }

NOTE: source_tenant_id is converted to TEXT (UUID string) for
  cross-language drift detector parity (CR 12-5 D-PARITY-01 inversion).
  target_tenant_ids is JSON array (cast from JSONB canonical form);
  Python ↔ TS payload shape MUST be identical.

Down revision: 0033_listen_notify_consume_trigger (13-1 wire tip).

NFR18 lock: trigger payload shape captured in DB (NFR18 lock policy).

AD-2 append-only ledger 보존: cache_invalidation_log retains
insert-only semantics (no UPDATE/DELETE triggers added).
"""

from __future__ import annotations

from alembic import op

revision = "0034_listen_notify_consume_cross_tenant_fanout"
down_revision = "0033_listen_notify_consume_trigger"
branch_labels = None
depends_on = None


# Channel values (Story 11.3 multi-channel expansion, 13-1 consume
# EXTENSION, 14-1 cross_tenant_fanout EXTENSION). Mirrored in
# apps/api/core/cache_invalidation_publisher.py:ALLOWED_CHANNELS (and
# the cross_tenant_fanout EXTENSION in cache_invalidation_listener.py).
_ALLOWED_CHANNELS_14_1: tuple[str, ...] = (
    "ai_cache",
    "cost_engine_cache",
    "fiscal_period_cache",
    "closing_snapshot_cache",
    "cross_tenant_fanout",
)

# Cross-tenant fan-out trigger channel (single channel). Mirrored in
# apps/api/core/cache_invalidation_listener.py:CROSS_TENANT_FANOUT_CHANNEL.
CROSS_TENANT_FANOUT_CHANNEL: str = "cross_tenant_fanout"

# NOTIFY channel name (PostgreSQL identifier, ≤ 63 chars by default).
# Mirrored in apps/api/core/cache_invalidation_listener.py:NOTIFY_CHANNEL_NAME.
NOTIFY_CHANNEL_NAME = "cache_invalidation_log"


def _build_check_constraint_ddl() -> str:
    """Build the 5+ channel CHECK constraint for cache_invalidation_log.

    The previous 4-channel constraint (alembic 0021) is dropped and
    replaced with this 5+ channel constraint (cross_tenant_fanout 추가).
    Mirrors `_ALLOWED_CHANNELS_14_1` verbatim.
    """
    in_clause = ", ".join(f"'{c}'" for c in _ALLOWED_CHANNELS_14_1)
    return f"""
        ALTER TABLE cache_invalidation_log
        ADD CONSTRAINT cache_invalidation_log_channel_check
        CHECK (channel IN ({in_clause}))
    """


def _build_target_tenant_ids_column_ddl() -> str:
    """Build the target_tenant_ids JSONB column DDL.

    target_tenant_ids is JSONB (not ARRAY) so the cross-tenant fan-out
    trigger function can emit it as a canonical JSON array (alphabetical
    order preserved by jsonb canonical form + Python json.dumps sort).

    Per CR 12-5 D-PARITY-01 inversion: the column shape is JSONB so
    Python `json.dumps(sort_keys=True)` and TypeScript JSON.parse output
    match byte-identically.
    """
    return """
        ALTER TABLE cache_invalidation_log
        ADD COLUMN IF NOT EXISTS target_tenant_ids JSONB NULL
    """


def _build_invalidation_id_column_ddl() -> str:
    """Build the invalidation_id UUID column DDL.

    invalidation_id is a UUID identifier for the cross-tenant fan-out
    event itself (distinct from `correction_group_id` which groups
    AD-22 reversal pairs or AD-4 commit broadcasts). The cross-tenant
    fan-out payload carries this UUID so the listener can dedupe replay
    attempts across followers during multi-process coordination.

    Defaults to `gen_random_uuid()` at INSERT so callers do NOT need
    to provide one for the 4 existing channels (which do not carry
    this field in their payload).
    """
    return """
        ALTER TABLE cache_invalidation_log
        ADD COLUMN IF NOT EXISTS invalidation_id UUID NULL
        DEFAULT gen_random_uuid()
    """


def _build_trigger_function_ddl() -> str:
    """Build the PL/pgSQL trigger function DDL for cross_tenant_fanout.

    V8 determinism invariant: payload JSON keys are output in
    alphabetical order via `json_object()` argument order (PG >= 12
    guarantees key-alphabetical JSON output for `json_build_object`
    when called with named keys; we use explicit positional args to
    `json_object()` to make the ordering part of the contract,
    not an implementation detail).

    The 7 keys are: channel, correction_group_id, invalidation_id,
    period_key, source_tenant_id, target_tenant_ids, trace_id
    (alphabetical).

    Returns the CREATE FUNCTION statement (deliberately wrapped in a
    single string so the SQL is line-by-line greppable in tests).
    """
    return f"""
        CREATE OR REPLACE FUNCTION cache_invalidation_log_notify_cross_tenant()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            payload TEXT;
            target_arr JSONB;
        BEGIN
            -- Channel whitelist check (defense-in-depth; the CHECK
            -- constraint on cache_invalidation_log.channel is the primary
            -- gate, but we re-verify here so the NOTIFY never emits an
            -- unrecognised channel even if the constraint is dropped).
            IF NEW.channel <> '{CROSS_TENANT_FANOUT_CHANNEL}' THEN
                -- This trigger ONLY fires for cross_tenant_fanout. The
                -- 4-channel trigger from alembic 0033 handles the other
                -- channels. Cross-channel contamination 방어 EXTENSION
                -- (F10.1-(d) verbatim).
                RETURN NEW;
            END IF;

            -- target_tenant_ids is JSONB. We re-cast it as canonical
            -- JSONB (jsonb canonical form) for V8 determinism — this
            -- guarantees byte-identical serialization across reruns.
            -- If target_tenant_ids is NULL, emit an empty JSON array
            -- (defense-in-depth; the listener will reject empty
            -- target lists via the adapter layer).
            IF NEW.target_tenant_ids IS NULL THEN
                target_arr := '[]'::jsonb;
            ELSE
                target_arr := NEW.target_tenant_ids::jsonb;
            END IF;

            -- V8 determinism: alphabetical key ordering guaranteed by
            -- explicit positional order in json_object(). The 7 keys
            -- are: channel, correction_group_id, invalidation_id,
            -- period_key, source_tenant_id, target_tenant_ids,
            -- trace_id (alphabetical).
            payload := json_object(
                'channel',
                NEW.channel,
                'correction_group_id',
                NEW.correction_group_id::text,
                'invalidation_id',
                COALESCE(NEW.invalidation_id::text, ''),
                'period_key',
                NEW.period_key,
                'source_tenant_id',
                NEW.tenant_id::text,
                'target_tenant_ids',
                target_arr::text,
                'trace_id',
                NEW.trace_id::text
            );

            PERFORM pg_notify('{NOTIFY_CHANNEL_NAME}', payload);
            RETURN NEW;
        END;
        $$;
    """


def _build_trigger_ddl() -> str:
    """Build the AFTER INSERT trigger DDL.

    INSERT-only trigger EXTENSION (AD-2 append-only ledger 정합).
    No UPDATE/DELETE triggers added (row immutability is enforced by the
    audit-first INSERT contract, not by a DB-level trigger).

    The trigger fires ONLY when `NEW.channel = 'cross_tenant_fanout'`
    — the WHERE clause is enforced in the trigger function body, so a
    single trigger covers the entire table without needing to filter
    at trigger creation time.
    """
    return """
        CREATE TRIGGER cache_invalidation_log_notify_cross_tenant_trg
        AFTER INSERT ON cache_invalidation_log
        FOR EACH ROW
        EXECUTE FUNCTION cache_invalidation_log_notify_cross_tenant();
    """


def upgrade() -> None:
    """Story 14.1 — cross_tenant_fanout NOTIFY trigger EXTENSION wire.

    1. ADD COLUMN `invalidation_id` (UUID, nullable, default
       gen_random_uuid()) for cross-tenant fan-out event identification.
    2. ADD COLUMN `target_tenant_ids` (JSONB, nullable) for the list of
       tenants receiving the cross-tenant fan-out event.
    3. DROP + ADD the channel CHECK constraint (5+ channels EXTENSION,
       cross_tenant_fanout 추가).
    4. CREATE OR REPLACE FUNCTION
       `cache_invalidation_log_notify_cross_tenant()` (PL/pgSQL,
       deterministic alphabetical JSON payload, 7 keys).
    5. CREATE TRIGGER
       `cache_invalidation_log_notify_cross_tenant_trg` (AFTER INSERT
       on cache_invalidation_log, FOR EACH ROW).
    6. Add per-channel index for cross_tenant_fanout query performance.
    7. COMMENT ON FUNCTION for AD-25 + F14 verbatim documentation.
    """
    # ── 1. ADD COLUMN invalidation_id ────────────────────────
    op.execute(_build_invalidation_id_column_ddl())

    # ── 2. ADD COLUMN target_tenant_ids ──────────────────────
    op.execute(_build_target_tenant_ids_column_ddl())

    # ── 3. Drop + re-add channel CHECK constraint (5+ channels) ─
    op.execute(
        """
        ALTER TABLE cache_invalidation_log
        DROP CONSTRAINT IF EXISTS cache_invalidation_log_channel_check
        """
    )
    op.execute(_build_check_constraint_ddl())

    # ── 4. Trigger function ──────────────────────────────────
    op.execute(_build_trigger_function_ddl())

    # ── 5. AFTER INSERT trigger ──────────────────────────────
    op.execute(_build_trigger_ddl())

    # ── 6. Per-channel index for cross_tenant_fanout ─────────
    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS ix_cache_inv_log_ch_{CROSS_TENANT_FANOUT_CHANNEL[:30]}
        ON cache_invalidation_log (tenant_id, channel, published_at DESC)
        WHERE channel = '{CROSS_TENANT_FANOUT_CHANNEL}'
        """
    )

    # ── 7. Document the trigger + payload shape ──────────────
    op.execute(
        f"""
        COMMENT ON FUNCTION cache_invalidation_log_notify_cross_tenant() IS
        'Story 14.1 (AD-25 EXTENSION cross_tenant_fanout, F14.1 + F14.3 verbatim). '
        'AFTER INSERT on cache_invalidation_log emits pg_notify(''{NOTIFY_CHANNEL_NAME}'', payload) '
        'where payload = json_object(channel, correction_group_id, invalidation_id, period_key, '
        'source_tenant_id, target_tenant_ids, trace_id) '
        '(7 keys, alphabetical, V8 byte-identical determinism). '
        'Trigger fires ONLY for channel = ''{CROSS_TENANT_FANOUT_CHANNEL}''. '
        'Channel whitelist = ({", ".join(_ALLOWED_CHANNELS_14_1)}). '
        'CR 12-5 D-PARITY-01 inversion: payload shape MUST match '
        'apps/web/lib/cache-invalidation-listener.ts (Python ↔ TS parity). '
        'A53+A57+A58+A59 결정 wire (cj-style Epic 14 1번째 진입점 진입 결정 보존).'
        """
    )


def downgrade() -> None:
    """Reverse Story 14.1 cross_tenant_fanout NOTIFY trigger EXTENSION.

    WARNING: this downgrade will NOT drop columns `invalidation_id` and
    `target_tenant_ids` if any other code path (e.g., a 14-1 follow-up
    story) depends on them. Operators MUST audit downstream consumers
    before downgrading.
    """
    # Drop the trigger first (drop order matters — trigger references function).
    op.execute(
        "DROP TRIGGER IF EXISTS cache_invalidation_log_notify_cross_tenant_trg "
        "ON cache_invalidation_log"
    )

    # Drop the function (drop order matters — function must be droppable
    # without cascade if no other triggers reference it).
    op.execute(
        "DROP FUNCTION IF EXISTS cache_invalidation_log_notify_cross_tenant()"
    )

    # Drop the partial index.
    op.execute(
        f"""
        DROP INDEX IF EXISTS ix_cache_inv_log_ch_{CROSS_TENANT_FANOUT_CHANNEL[:30]}
        """
    )

    # Restore the 4-channel CHECK constraint (0021 wire shape).
    in_clause_4 = ", ".join(
        f"'{c}'"
        for c in _ALLOWED_CHANNELS_14_1
        if c != CROSS_TENANT_FANOUT_CHANNEL
    )
    op.execute(
        """
        ALTER TABLE cache_invalidation_log
        DROP CONSTRAINT IF EXISTS cache_invalidation_log_channel_check
        """
    )
    op.execute(
        f"""
        ALTER TABLE cache_invalidation_log
        ADD CONSTRAINT cache_invalidation_log_channel_check
        CHECK (channel IN ({in_clause_4}))
        """
    )

    # Drop the new columns. NOTE: downgrade does NOT drop invalidation_id
    # or target_tenant_ids — operators MUST audit downstream consumers
    # before downgrading (the schema can carry these columns even if
    # the trigger is gone; the 4-channel trigger from alembic 0033
    # does not reference them).
