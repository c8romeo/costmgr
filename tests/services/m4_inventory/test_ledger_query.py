"""Story 5.2 — pure helpers test suite (T2).

Drives the red-green-refactor cycle for
`packages.services.m4_inventory.ledger_query`. Read-only SQL fragment
builders — no DB, no clock, no random. Drift between Python and TS
caught by `tests/integration/test_inventory_ledger_query_consistency.py`.
"""

from __future__ import annotations

import re

import pytest

from packages.services.m4_inventory.ledger_query import (
    CARRY_CHAIN_RECURSION_DEPTH,
    LedgerQuery,
    PARAM_PERIOD_KEY,
    PARAM_PRODUCT_ID,
    PARAM_TENANT_ID,
    assert_tenant_guarded,
    build_carry_chain_query,
    build_period_closing_query,
)


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

def test_carry_chain_recursion_depth_12() -> None:
    """Story 5.1 OQ4 cj-style default: 12-period chain limit."""
    assert CARRY_CHAIN_RECURSION_DEPTH == 12


# ─────────────────────────────────────────────────────────────
# build_period_closing_query
# ─────────────────────────────────────────────────────────────

def test_period_closing_query_includes_tenant_guard() -> None:
    """Tenant_id bound parameter MUST be present (AD-4 RLS)."""
    query = build_period_closing_query()
    assert f":{PARAM_TENANT_ID}" in query.sql


def test_period_closing_query_filters_period_key() -> None:
    """period_key bound parameter present."""
    query = build_period_closing_query()
    assert f":{PARAM_PERIOD_KEY}" in query.sql


def test_period_closing_query_filters_product_id() -> None:
    """product_id bound parameter present."""
    query = build_period_closing_query()
    assert f":{PARAM_PRODUCT_ID}" in query.sql


def test_period_closing_query_excludes_closing_snapshot() -> None:
    """PRD §6.2: closing_snapshot is a materialized balance, not a flow."""
    query = build_period_closing_query()
    assert "closing_snapshot" in query.sql
    # The fragment explicitly excludes this event_type from SUM().
    assert "!=" in query.sql or "<>" in query.sql


def test_period_closing_query_uses_sum_qty() -> None:
    """Aggregate function: SUM(qty)."""
    query = build_period_closing_query()
    assert "SUM(qty)" in query.sql


def test_period_closing_query_params_match_docs() -> None:
    """3 params: tenant_id, product_id, period_key."""
    query = build_period_closing_query()
    assert set(query.params) == {PARAM_TENANT_ID, PARAM_PRODUCT_ID, PARAM_PERIOD_KEY}


def test_period_closing_query_description() -> None:
    """Human-readable role for audit log."""
    query = build_period_closing_query()
    assert query.description == "period_closing_aggregate"


# ─────────────────────────────────────────────────────────────
# build_carry_chain_query
# ─────────────────────────────────────────────────────────────

def test_carry_chain_query_is_recursive_cte() -> None:
    """WITH RECURSIVE keyword present."""
    query = build_carry_chain_query()
    assert "WITH RECURSIVE" in query.sql
    assert "carry_chain" in query.sql


def test_carry_chain_query_filters_opening_carried() -> None:
    """Only opening_carried events are walked (5-1 carry chain)."""
    query = build_carry_chain_query()
    assert "'opening_carried'" in query.sql


def test_carry_chain_query_includes_tenant_guard() -> None:
    """Tenant_id bound parameter MUST be present (AD-4 RLS)."""
    query = build_carry_chain_query()
    assert f":{PARAM_TENANT_ID}" in query.sql


def test_carry_chain_query_orders_chronologically() -> None:
    """ORDER BY period_key ASC + LIMIT 12 (chain bound)."""
    query = build_carry_chain_query()
    assert "ORDER BY" in query.sql
    assert "period_key" in query.sql
    assert "ASC" in query.sql
    assert f"LIMIT {CARRY_CHAIN_RECURSION_DEPTH}" in query.sql


def test_carry_chain_query_params_match_docs() -> None:
    """3 params: tenant_id, product_id, period_key."""
    query = build_carry_chain_query()
    assert set(query.params) == {PARAM_TENANT_ID, PARAM_PRODUCT_ID, PARAM_PERIOD_KEY}


def test_carry_chain_query_description() -> None:
    """Human-readable role for audit log."""
    query = build_carry_chain_query()
    assert query.description == "carry_chain_recursive_walk"


# ─────────────────────────────────────────────────────────────
# Determinism — repeated calls produce byte-identical output
# ─────────────────────────────────────────────────────────────

def test_period_closing_query_idempotent() -> None:
    """Same call 100× → byte-identical output (AD-16 determinism)."""
    first = build_period_closing_query()
    for _ in range(100):
        again = build_period_closing_query()
        assert again.sql == first.sql
        assert again.params == first.params


def test_carry_chain_query_idempotent() -> None:
    """Same call 100× → byte-identical output (AD-16 determinism)."""
    first = build_carry_chain_query()
    for _ in range(100):
        again = build_carry_chain_query()
        assert again.sql == first.sql
        assert again.params == first.params


# ─────────────────────────────────────────────────────────────
# assert_tenant_guarded
# ─────────────────────────────────────────────────────────────

def test_assert_tenant_guarded_passes_valid_query() -> None:
    """period_closing_query passes tenant guard check."""
    query = build_period_closing_query()
    assert_tenant_guarded(query)  # no raise


def test_assert_tenant_guarded_raises_on_missing_guard() -> None:
    """Fragment missing tenant_id raises ValueError."""
    bad_query = LedgerQuery(
        sql="SELECT 1 FROM inventory_ledger WHERE product_id = :product_id",
        params=(PARAM_PRODUCT_ID,),
        description="malformed_fragment",
    )
    with pytest.raises(ValueError, match="tenant_id bound parameter guard"):
        assert_tenant_guarded(bad_query)


# ─────────────────────────────────────────────────────────────
# SQL safety — no caller-value interpolation
# ─────────────────────────────────────────────────────────────

def test_period_closing_query_no_fstring_interpolation_pattern() -> None:
    """SQL fragment uses :param binding (no caller-value interpolation)."""
    query = build_period_closing_query()
    # No `WHERE foo = 'literal'` patterns with quotes around values.
    # (Caveat: 'closing_snapshot' literal is a SQL enum string, NOT
    # caller data — it's whitelisted at the Python layer.)
    # Verify that any quoted string is the enum literal.
    quoted = re.findall(r"'([^']*)'", query.sql)
    for q in quoted:
        assert q in {"closing_snapshot"}, (
            f"Unexpected quoted string in SQL fragment: {q!r} — "
            f"only whitelisted enum literals allowed; caller data must "
            f"use :param binding (AD-15 §0.4 cross-language parity)."
        )


def test_carry_chain_query_no_fstring_interpolation_pattern() -> None:
    """SQL fragment uses :param binding (no caller-value interpolation).

    Allowed SQL literals: enum values + date-arithmetic constants
    ('-01' for first-of-month concat, '1 month' for INTERVAL).
    """
    query = build_carry_chain_query()
    allowed = {"opening_carried", "-01", "1 month"}
    quoted = re.findall(r"'([^']*)'", query.sql)
    for q in quoted:
        assert q in allowed, (
            f"Unexpected quoted string in SQL fragment: {q!r} — "
            f"only whitelisted enum literals or date-arithmetic "
            f"constants allowed."
        )