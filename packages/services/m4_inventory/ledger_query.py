"""packages.services.m4_inventory.ledger_query — Story 5.2 pure kernel #2.

Read-only SQL fragment builders for the inventory_ledger projection.
The DB schema (Alembic 0015) + service-layer SQLAlchemy execution own
the production query; this kernel owns the SQL text fragments as
immutable strings (named-parameterized, no f-string interpolation of
caller values) so the 5-1 `LEDGER_REFERENCE_QUERY_STUB` swap target
has a stable, testable shape.

AD-1 / AD-11 binding: pure-Python, stdlib-only, no DB, no clock, no
random. Drift between Python and TS caught by
`tests/integration/test_inventory_ledger_query_consistency.py`.
"""

from __future__ import annotations

import re
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# Parameter names mirror what the service layer binds (SQLAlchemy
# `text(...).bindparams(...)`). Drift between Python and TS caught
# by `_query_consistency` integration test.
PARAM_PERIOD_KEY: Final[str] = "period_key"
PARAM_PRODUCT_ID: Final[str] = "product_id"
PARAM_TENANT_ID: Final[str] = "tenant_id"
PARAM_TRACE_ID: Final[str] = "trace_id"

# Maximum period chain length (carry-chain recursion bound). Story 5.1
# established `INVENTORY_PERIOD_CHAIN_LIMIT = 12`; the ledger_query
# re-exports it for symmetry / drift detection.
CARRY_CHAIN_RECURSION_DEPTH: Final[int] = 12


# ── SQL fragment allowlist ───────────────────────────────────
# Identifiers (column + table names) hard-coded into SQL fragments.
# We keep these as named constants to make drift vs DB schema visible
# at code-review time. Any new column reference must be added here
# AND to the Alembic 0015 migration simultaneously (3-way drift
# detector: Python ↔ TS ↔ PostgreSQL DDL).
_COL_EVENT_ID: Final[str] = "event_id"
_COL_TENANT_ID: Final[str] = "tenant_id"
_COL_PRODUCT_ID: Final[str] = "product_id"
_COL_PERIOD_KEY: Final[str] = "period_key"
_COL_EVENT_TYPE: Final[str] = "event_type"
_COL_QTY: Final[str] = "qty"
_COL_TRACE_ID: Final[str] = "trace_id"
_COL_INSERTED_AT: Final[str] = "inserted_at"

_TBL_INVENTORY_LEDGER: Final[str] = "inventory_ledger"

# Tenant-isolation guard (AD-4 row-level security). Every fragment MUST
# filter on tenant_id via bound parameter — never inline.
_TENANT_GUARD_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"\b{_COL_TENANT_ID}\s*=\s*:\s*{PARAM_TENANT_ID}\b"
)


# ── LedgerQuery NamedTuple ───────────────────────────────────
class LedgerQuery(NamedTuple):
    """Read-only SQL fragment descriptor.

    `sql` is a `:param` named-parameterized text fragment (NEVER f-string
    interpolated caller values). `params` lists the expected bind
    parameter names for documentation + drift detection. `description`
    is the human-readable role (used by service-layer audit log emit).

    AD-15: snake_case field names.
    """

    sql: str
    params: tuple[str, ...]
    description: str


# ── Period-closing aggregate ─────────────────────────────────
def build_period_closing_query() -> LedgerQuery:
    """SUM(qty) for a single (tenant_id, product_id, period_key).

    Returns the period closing_balance per PRD §6.2 inventory
    equation. `closing_snapshot` rows are NOT included in this
    aggregate — they're materialized balance snapshots, not flow
    events (PRD §6.2: closing = sum of flow events).

    Returns:
        LedgerQuery with sql + params + description. Service layer
        binds via SQLAlchemy `text(...).bindparams(...)`.

    Tenant-isolation: MUST filter on tenant_id (AD-4 RLS).
    """
    sql = (
        f"SELECT COALESCE(SUM({_COL_QTY}), 0) AS closing_qty "
        f"FROM {_TBL_INVENTORY_LEDGER} "
        f"WHERE {_COL_TENANT_ID} = :{PARAM_TENANT_ID} "
        f"  AND {_COL_PRODUCT_ID} = :{PARAM_PRODUCT_ID} "
        f"  AND {_COL_PERIOD_KEY} = :{PARAM_PERIOD_KEY} "
        f"  AND {_COL_EVENT_TYPE} != 'closing_snapshot'"
    )
    return LedgerQuery(
        sql=sql,
        params=(PARAM_TENANT_ID, PARAM_PRODUCT_ID, PARAM_PERIOD_KEY),
        description="period_closing_aggregate",
    )


# ── Carry-chain recursive CTE ────────────────────────────────
def build_carry_chain_query() -> LedgerQuery:
    """Recursive CTE for the carry-chain audit walk (Story 5.1 + 5.2).

    Walks `opening_carried` events backwards from the most recent
    period_key through `CARRY_CHAIN_RECURSION_DEPTH` (12) periods.
    Service layer (5-1 `OpeningCarryService` consumer) binds
    period_key as the upper bound (exclusive) and tenant_id +
    product_id for AD-4 isolation.

    Returns:
        LedgerQuery with sql + params + description. Service layer
        binds via SQLAlchemy `text(...).bindparams(...)`.

    Tenant-isolation: MUST filter on tenant_id (AD-4 RLS).
    """
    sql = (
        f"WITH RECURSIVE carry_chain AS ( "
        f"  SELECT {_COL_EVENT_ID}, {_COL_TENANT_ID}, {_COL_PRODUCT_ID}, "
        f"         {_COL_PERIOD_KEY}, {_COL_EVENT_TYPE}, {_COL_QTY}, "
        f"         {_COL_INSERTED_AT} "
        f"    FROM {_TBL_INVENTORY_LEDGER} "
        f"   WHERE {_COL_TENANT_ID} = :{PARAM_TENANT_ID} "
        f"     AND {_COL_PRODUCT_ID} = :{PARAM_PRODUCT_ID} "
        f"     AND {_COL_EVENT_TYPE} = 'opening_carried' "
        f"     AND {_COL_PERIOD_KEY} < :{PARAM_PERIOD_KEY} "
        f"  UNION ALL "
        f"  SELECT e.{_COL_EVENT_ID}, e.{_COL_TENANT_ID}, "
        f"         e.{_COL_PRODUCT_ID}, e.{_COL_PERIOD_KEY}, "
        f"         e.{_COL_EVENT_TYPE}, e.{_COL_QTY}, "
        f"         e.{_COL_INSERTED_AT} "
        f"    FROM {_TBL_INVENTORY_LEDGER} e "
        f"    INNER JOIN carry_chain cc "
        f"      ON cc.{_COL_TENANT_ID} = e.{_COL_TENANT_ID} "
        f"     AND cc.{_COL_PRODUCT_ID} = e.{_COL_PRODUCT_ID} "
        f"     AND cc.{_COL_PERIOD_KEY} = "
        f"        (e.{_COL_PERIOD_KEY} || '-01')::date - INTERVAL '1 month' "
        f"   WHERE e.{_COL_EVENT_TYPE} = 'opening_carried' "
        f") "
        f"SELECT {_COL_EVENT_ID}, {_COL_PERIOD_KEY}, {_COL_QTY}, "
        f"       {_COL_INSERTED_AT} "
        f"  FROM carry_chain "
        f" ORDER BY {_COL_PERIOD_KEY} ASC "
        f" LIMIT {CARRY_CHAIN_RECURSION_DEPTH}"
    )
    return LedgerQuery(
        sql=sql,
        params=(PARAM_TENANT_ID, PARAM_PRODUCT_ID, PARAM_PERIOD_KEY),
        description="carry_chain_recursive_walk",
    )


# ── Tenant-guard validation ──────────────────────────────────
def assert_tenant_guarded(query: LedgerQuery) -> None:
    """Validate that a fragment contains the tenant_id bound param.

    Pure-kernel early-fail guard. Service-layer audit log emit must
    pass this check before persisting the SQL text into any audit log
    payload (CR 4-3 lesson: A5 audit-first pattern — payload
    self-describing means even the SQL fragment must be tenant-safe).
    """
    if not _TENANT_GUARD_PATTERN.search(query.sql):
        raise ValueError(
            f"LedgerQuery {query.description!r} missing tenant_id bound "
            f"parameter guard (AD-4 RLS). Tenant-isolation guard "
            f"must be present in EVERY fragment."
        )


__all__ = [
    "CARRY_CHAIN_RECURSION_DEPTH",
    "LedgerQuery",
    "PARAM_PERIOD_KEY",
    "PARAM_PRODUCT_ID",
    "PARAM_TENANT_ID",
    "PARAM_TRACE_ID",
    "assert_tenant_guarded",
    "build_carry_chain_query",
    "build_period_closing_query",
]
