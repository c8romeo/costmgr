"""Story 13.1 — LISTEN/NOTIFY Consume Trigger EXTENSION (A39/A51/A52 결정 wire).

D-10-2-DEFER-3 ✅ RESOLVED wire 진입: PostgreSQL NOTIFY trigger on
`cache_invalidation_log` AFTER INSERT emits `pg_notify` events for
AD-25 verbatim multi-channel cache invalidation consume trigger EXTENSION.

Per AD-25 (ARCHITECTURE-SPINE.md §142-148 verbatim):
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Per AD-2: append-only ledger — `cache_invalidation_log` retains
insert-only semantics (no UPDATE/DELETE triggers added; receipt
record is immutable after publish).

Trigger function semantics:
- `cache_invalidation_log_notify()` — PL/pgSQL function
- AFTER INSERT trigger on `cache_invalidation_log`
- `pg_notify('cache_invalidation_log', payload)` where payload is a
  deterministic JSON object with 5 alphabetical keys (channel,
  correction_group_id, period_key, tenant_id, trace_id) for V8
  byte-identical determinism (CR 4-4 / F13.3 verbatim).

Channel whitelist (4 channels, AD-25 verbatim):
  - `ai_cache`               — M10 AI cache invalidation (11-1 wire 보존)
  - `cost_engine_cache`      — M3 cost engine calculation result cache (11-3 NEW)
  - `fiscal_period_cache`    — M11 fiscal_periods + fiscal_period_snapshots
                                metadata cache (11-3 NEW)
  - `closing_snapshot_cache` — M11 closing_snapshot + ledger closing event
                                cache (11-3 NEW)

Payload shape (5 keys, alphabetical order — V8 determinism):
  {
    "channel":              "ai_cache",
    "correction_group_id":  "uuid-string",
    "period_key":           "YYYY-MM",
    "tenant_id":            "uuid-string",
    "trace_id":             "uuid-string"
  }

NOTE: tenant_id is converted to TEXT (UUID string) for cross-language
  drift detector parity (CR 12-5 D-PARITY-01 inversion). Python ↔ TS
  payload shape MUST be identical.

Down revision: 0032_ai_promotion_port (Story 10.4 wire tip).

NFR18 lock: trigger payload shape captured in DB (NFR18 lock policy).
"""

from __future__ import annotations

from alembic import op

revision = "0033_listen_notify_consume_trigger"
down_revision = "0032_ai_promotion_port"
branch_labels = None
depends_on = None


# Channel values (Story 11.3 multi-channel expansion, 13-1 consume EXTENSION).
# Mirrored in apps/api/core/cache_invalidation_publisher.py:ALLOWED_CHANNELS.
_ALLOWED_CHANNELS_13_1: tuple[str, ...] = (
    "ai_cache",
    "cost_engine_cache",
    "fiscal_period_cache",
    "closing_snapshot_cache",
)

# NOTIFY channel name (PostgreSQL identifier, ≤ 63 chars by default).
# Mirrored in apps/api/core/cache_invalidation_listener.py:NOTIFY_CHANNEL_NAME.
NOTIFY_CHANNEL_NAME = "cache_invalidation_log"


def _build_trigger_function_ddl() -> str:
    """Build the PL/pgSQL trigger function DDL.

    V8 determinism invariant: payload JSON keys are output in
    alphabetical order via `json_object()` argument order (PG >= 12
    guarantees key-alphabetical JSON output for `json_build_object`
    when called with named keys; we use explicit positional args to
    `json_object()` to make the ordering part of the contract,
    not an implementation detail).

    Returns the CREATE FUNCTION statement (deliberately wrapped in a
    single string so the SQL is line-by-line greppable in tests).
    """
    in_clause = ", ".join(f"'{c}'" for c in _ALLOWED_CHANNELS_13_1)
    return f"""
        CREATE OR REPLACE FUNCTION cache_invalidation_log_notify()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            payload TEXT;
        BEGIN
            -- Channel whitelist check (defense-in-depth; the CHECK
            -- constraint on cache_invalidation_log.channel is the primary
            -- gate, but we re-verify here so the NOTIFY never emits an
            -- unrecognised channel even if the constraint is dropped).
            IF NEW.channel NOT IN ({in_clause}) THEN
                RAISE EXCEPTION
                    'cache_invalidation_log_notify: channel %% not in allowed set',
                    NEW.channel
                    USING ERRCODE = '22000';
            END IF;

            -- V8 determinism: alphabetical key ordering guaranteed by
            -- explicit positional order in json_object(). The 5 keys
            -- are: channel, correction_group_id, period_key, tenant_id,
            -- trace_id (alphabetical).
            payload := json_object(
                'channel',
                NEW.channel,
                'correction_group_id',
                NEW.correction_group_id::text,
                'period_key',
                NEW.period_key,
                'tenant_id',
                NEW.tenant_id::text,
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
    """
    return """
        CREATE TRIGGER cache_invalidation_log_notify_trg
        AFTER INSERT ON cache_invalidation_log
        FOR EACH ROW
        EXECUTE FUNCTION cache_invalidation_log_notify();
    """


def upgrade() -> None:
    """Story 13.1 — AD-25 consume trigger EXTENSION wire.

    1. CREATE OR REPLACE FUNCTION `cache_invalidation_log_notify()` (
       PL/pgSQL, deterministic alphabetical JSON payload).
    2. CREATE TRIGGER `cache_invalidation_log_notify_trg` (AFTER INSERT
       on cache_invalidation_log, FOR EACH ROW).
    3. COMMENT ON FUNCTION for AD-25 + F13 verbatim documentation.
    """
    # ── 1. Trigger function ─────────────────────────────────
    op.execute(_build_trigger_function_ddl())

    # ── 2. AFTER INSERT trigger ────────────────────────────
    op.execute(_build_trigger_ddl())

    # ── 3. Document the trigger + payload shape ────────────
    op.execute(
        f"""
        COMMENT ON FUNCTION cache_invalidation_log_notify() IS
        'Story 13.1 (AD-25 consume trigger EXTENSION, F13.1 verbatim). '
        'AFTER INSERT on cache_invalidation_log emits pg_notify(''{NOTIFY_CHANNEL_NAME}'', payload) '
        'where payload = json_object(channel, correction_group_id, period_key, tenant_id, trace_id) '
        '(5 keys, alphabetical, V8 byte-identical determinism). '
        'Channel whitelist = ({", ".join(_ALLOWED_CHANNELS_13_1)}). '
        'CR 12-5 D-PARITY-01 inversion: payload shape MUST match '
        'apps/web/lib/cache-invalidation-listener.ts (Python ↔ TS parity).'
        """
    )


def downgrade() -> None:
    """Reverse Story 13.1 consume trigger EXTENSION.

    WARNING: this downgrade will NOT drop function `cache_invalidation_log_notify`
    if any other code path (e.g., a 13-1 follow-up story) depends on it.
    Operators MUST audit downstream consumers before downgrading.
    """
    # Drop the trigger first (drop order matters — trigger references function).
    op.execute(
        "DROP TRIGGER IF EXISTS cache_invalidation_log_notify_trg ON cache_invalidation_log"
    )

    # Drop the function (drop order matters — function must be droppable
    # without cascade if no other triggers reference it).
    op.execute("DROP FUNCTION IF EXISTS cache_invalidation_log_notify()")
