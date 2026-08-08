"""tests.services.m11_close.test_close_sequence_state — Story 11.2 pure kernel #3.

~20 tests covering:
- compute_close_sequence_state for 0/1/2/3/4 stages + closed_at presence
- check_ad6_insert_allowed allow/reject matrix (6 cases)
- AD-22 reversal/correction event allow matrix
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from packages.services.m11_close.close_sequence_state import (
    AD6_LOCKED_TABLES,
    Ad6InsertGuardResult,
    CloseSequenceStateError,
    REVERSAL_TARGET_EVENT_TYPES,
    check_ad6_insert_allowed,
    compute_close_sequence_state,
)


_BASE_TS = datetime(2026, 8, 1, 0, 0, 0)


def _ts(offset_minutes: int = 0) -> datetime:
    return _BASE_TS + timedelta(minutes=offset_minutes)


# ── compute_close_sequence_state ────────────────────────────
def test_zero_steps_returns_divisions_state() -> None:
    state = compute_close_sequence_state(
        divisions_completed_at=None,
        manufacturing_completed_at=None,
        abc_completed_at=None,
        common_completed_at=None,
        closed_at=None,
    )
    assert state == "divisions"


def test_one_step_returns_manufacturing_state() -> None:
    state = compute_close_sequence_state(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=None,
        abc_completed_at=None,
        common_completed_at=None,
        closed_at=None,
    )
    assert state == "manufacturing"


def test_two_steps_returns_abc_state() -> None:
    state = compute_close_sequence_state(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=None,
        common_completed_at=None,
        closed_at=None,
    )
    assert state == "abc"


def test_three_steps_returns_common_state() -> None:
    state = compute_close_sequence_state(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=_ts(20),
        common_completed_at=None,
        closed_at=None,
    )
    assert state == "common"


def test_four_steps_with_closed_at_returns_confirmed() -> None:
    state = compute_close_sequence_state(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=_ts(20),
        common_completed_at=_ts(30),
        closed_at=_ts(40),
    )
    assert state == "confirmed"


def test_four_steps_without_closed_at_returns_common() -> None:
    """4 stages done but not yet confirmed (awaiting close flow)."""
    state = compute_close_sequence_state(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=_ts(20),
        common_completed_at=_ts(30),
        closed_at=None,
    )
    assert state == "common"


# ── check_ad6_insert_allowed — non-confirmed states ─────────
def test_non_confirmed_state_allows_insert() -> None:
    result = check_ad6_insert_allowed(
        close_sequence_state="divisions",
        target_table="monthly_input_rows",
        target_event_type="purchase_inbound",
    )
    assert result.allowed is True
    assert result.guard_type == "ALLOWED"
    assert result.reject_reason_ko is None


def test_manufacturing_state_allows_insert() -> None:
    result = check_ad6_insert_allowed(
        close_sequence_state="manufacturing",
        target_table="inventory_ledger",
        target_event_type="sales_outbound",
    )
    assert result.allowed is True
    assert result.guard_type == "ALLOWED"


# ── check_ad6_insert_allowed — confirmed + business table → BLOCKED
def test_confirmed_state_blocks_business_data_insert() -> None:
    result = check_ad6_insert_allowed(
        close_sequence_state="confirmed",
        target_table="monthly_input_rows",
        target_event_type="purchase_inbound",
    )
    assert result.allowed is False
    assert result.guard_type == "CLOSED_LOCK"
    assert result.reject_reason_ko is not None


def test_confirmed_state_blocks_inventory_ledger_insert() -> None:
    result = check_ad6_insert_allowed(
        close_sequence_state="confirmed",
        target_table="inventory_ledger",
        target_event_type="production_output_inbound",
    )
    assert result.allowed is False
    assert result.guard_type == "CLOSED_LOCK"


def test_confirmed_state_blocks_fiscal_period_snapshots_insert() -> None:
    result = check_ad6_insert_allowed(
        close_sequence_state="confirmed",
        target_table="fiscal_period_snapshots",
        target_event_type="compute",
    )
    assert result.allowed is False
    assert result.guard_type == "CLOSED_LOCK"


# ── check_ad6_insert_allowed — reversal/correction exception
def test_confirmed_state_allows_reversal_negating() -> None:
    """AD-22 reversal/correction events pass through AD-6 lock."""
    result = check_ad6_insert_allowed(
        close_sequence_state="confirmed",
        target_table="inventory_ledger",
        target_event_type="reversal_negating",
    )
    assert result.allowed is True
    assert result.guard_type == "REVERSAL_EXCEPTION"


def test_confirmed_state_allows_reversal_corrected() -> None:
    result = check_ad6_insert_allowed(
        close_sequence_state="confirmed",
        target_table="inventory_ledger",
        target_event_type="reversal_corrected",
    )
    assert result.allowed is True
    assert result.guard_type == "REVERSAL_EXCEPTION"


# ── check_ad6_insert_allowed — bookkeeping tables allowed
def test_confirmed_state_allows_audit_log_insert() -> None:
    """audit_logs is bookkeeping, not in AD6_LOCKED_TABLES."""
    result = check_ad6_insert_allowed(
        close_sequence_state="confirmed",
        target_table="audit_logs",
        target_event_type="closing_period_confirmed",
    )
    assert result.allowed is True
    assert result.guard_type == "ALLOWED"


def test_confirmed_state_allows_reversal_log_insert() -> None:
    result = check_ad6_insert_allowed(
        close_sequence_state="confirmed",
        target_table="reversal_log",
        target_event_type="reversal_negating_inserted",
    )
    assert result.allowed is True
    assert result.guard_type == "ALLOWED"


# ── check_ad6_insert_allowed — invalid input
def test_invalid_state_raises_error() -> None:
    with pytest.raises(CloseSequenceStateError):
        check_ad6_insert_allowed(
            close_sequence_state="garbage",
            target_table="monthly_input_rows",
            target_event_type="purchase_inbound",
        )


# ── Module surface ──────────────────────────────────────────
def test_module_exports_ad6_locked_tables_constant() -> None:
    assert "monthly_input_periods" in AD6_LOCKED_TABLES
    assert "monthly_input_rows" in AD6_LOCKED_TABLES
    assert "inventory_ledger" in AD6_LOCKED_TABLES
    assert "fiscal_period_snapshots" in AD6_LOCKED_TABLES


def test_module_exports_reversal_target_event_types() -> None:
    assert "reversal_negating" in REVERSAL_TARGET_EVENT_TYPES
    assert "reversal_corrected" in REVERSAL_TARGET_EVENT_TYPES


# ── Result namedtuple surface ───────────────────────────────
def test_ad6_insert_guard_result_namedtuple() -> None:
    r = Ad6InsertGuardResult(
        allowed=True,
        reject_reason_ko=None,
        guard_type="ALLOWED",
    )
    assert r.allowed is True
    assert r.reject_reason_ko is None
    assert r.guard_type == "ALLOWED"