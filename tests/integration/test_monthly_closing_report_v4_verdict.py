"""tests/integration/test_monthly_closing_report_v4_verdict.py — Story 6.2 T9.8 V4 wire tests.

V4 verdict wire integration tests for Monthly Closing Report:
- V4 verdict envelope shape (status / code / failures / source_count)
- V4 verdict PASS / FAIL / SKIP transitions
- industry='service' → V4 SKIP (A10 capability gate 동등)
- 4-source aggregate extension invariants

Pure-kernel + aggregator level — 4 cases total.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.cost_engine.monthly_closing_report_aggregator import (
    V4_FAIL_MESSAGE_KO,
    V4_ORDER_INDEX,
    V4_RULE_CODE,
    V4_STATUS_FAILED,
    V4_STATUS_PASSED,
    V4_STATUS_SKIPPED,
    verify_monthly_closing_report_consistency,
)


def _u() -> uuid.UUID:
    return uuid.uuid4()


# ── V4 wire shape (2 cases) ──────────────────────────────────────


def test_v4_verdict_envelope_shape_pass() -> None:
    """V4 verdict PASS → TypedDict with status/code/failures/source_count=4."""
    p1 = _u()
    qty = Decimal("100.0000")
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={p1: qty},
        closing_snapshot_aggregate={p1: qty},
        fiscal_period_snapshot_aggregate={p1: qty},
        product_whitelist={p1},
    )
    assert verdict["status"] == V4_STATUS_PASSED
    assert verdict["code"] == "V4"
    assert verdict["failures"] == []
    assert verdict["source_count"] == 4
    assert verdict["skip_reason_ko"] is None


def test_v4_verdict_envelope_shape_fail() -> None:
    """V4 verdict FAIL → failures populated + Korean message_ko."""
    p1 = _u()
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={p1: Decimal("10")},
        closing_snapshot_aggregate={p1: Decimal("11")},
        fiscal_period_snapshot_aggregate={p1: Decimal("10")},
        product_whitelist={p1},
    )
    assert verdict["status"] == V4_STATUS_FAILED
    assert verdict["code"] == "V4"
    assert len(verdict["failures"]) == 1
    failure = verdict["failures"][0]
    assert failure["message_ko"] == V4_FAIL_MESSAGE_KO
    assert failure["product_id"] == str(p1)


# ── V4 wire transitions (2 cases) ────────────────────────────────


def test_v4_verdict_skip_transition_service() -> None:
    """industry='service' → V4 SKIP (transition from any state)."""
    p1 = _u()
    # Pass all 3 aggregates identically — but service industry forces SKIP
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={p1: Decimal("10")},
        closing_snapshot_aggregate={p1: Decimal("10")},
        fiscal_period_snapshot_aggregate={p1: Decimal("10")},
        product_whitelist={p1},
        industry="service",
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert "service-only" in (verdict["skip_reason_ko"] or "")


def test_v4_verdict_order_index_ad12_slot_2() -> None:
    """V4_ORDER_INDEX = 2 (AD-12 ordering: V1 → V4 → V3 → V7 → V8)."""
    assert V4_ORDER_INDEX == 2
    assert V4_RULE_CODE == "V4"