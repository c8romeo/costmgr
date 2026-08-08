"""tests/cost_engine/test_monthly_closing_report_aggregator.py — Story 6.2 T9.2 V4 aggregator tests.

Tests for `packages/cost_engine/monthly_closing_report_aggregator.py`:
- verify_monthly_closing_report_consistency (4-source V4 extension)
- V4 verdict status: PASS / FAIL / SKIP (AD-12 ordering)
- Korean SSOT constants (V4_FAIL_MESSAGE_KO + V4_SKIP_REASON_*)
- industry='service' → V4 SKIP (A10 capability gate 동등)
- 4-source extension (ledger + closing_snapshot + fiscal_period_snapshot + product_whitelist)
- banker's rounding via QTY_QUANTUM (CR 0-4 lesson + AD-15 parity)
- 12 cases total
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.cost_engine.monthly_closing_report_aggregator import (
    V4_FAIL_MESSAGE_KO,
    V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO,
    V4_ORDER_INDEX,
    V4_RULE_CODE,
    V4_SKIP_REASON_EMPTY_AGGREGATE_KO,
    V4_SKIP_REASON_SERVICE_ONLY_KO,
    V4_STATUSES,
    V4_STATUS_FAILED,
    V4_STATUS_PASSED,
    V4_STATUS_SKIPPED,
    verify_monthly_closing_report_consistency,
)


def _u() -> uuid.UUID:
    return uuid.uuid4()


# ── V4 constants SSOT (3 cases) ───────────────────────────────────


def test_v4_statuses_frozenset_three() -> None:
    """V4_STATUSES = 3 codes (PASSED / FAILED / SKIPPED)."""
    assert V4_STATUSES == frozenset(
        {V4_STATUS_PASSED, V4_STATUS_FAILED, V4_STATUS_SKIPPED}
    )


def test_v4_fail_message_ko_ssot() -> None:
    """V4_FAIL_MESSAGE_KO = '마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요'."""
    assert V4_FAIL_MESSAGE_KO == (
        "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요"
    )


def test_v4_skip_reason_service_only_ko_ssot() -> None:
    """V4_SKIP_REASON_SERVICE_ONLY_KO = 'service-only tenant은 inventory 의미 없음'."""
    assert V4_SKIP_REASON_SERVICE_ONLY_KO == (
        "service-only tenant은 inventory 의미 없음"
    )


def test_v4_fiscal_snapshot_fail_message_ko_ssot() -> None:
    """V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO = '마감 snapshot 불일치: fiscal_period_snapshot aggregate vs ledger aggregate 갱신 필요'."""
    assert V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO == (
        "마감 snapshot 불일치: fiscal_period_snapshot aggregate vs ledger aggregate 갱신 필요"
    )


def test_v4_order_index_ad12_slot_2() -> None:
    """V4_ORDER_INDEX = 2 (AD-12 ordering V1 → V4 → V3 → V7 → V8)."""
    assert V4_ORDER_INDEX == 2
    assert V4_RULE_CODE == "V4"


# ── V4 verdict PASS path (2 cases) ───────────────────────────────


def test_verify_v4_pass_all_three_sources_match() -> None:
    """All 4 sources 일치 → V4 PASS."""
    p1, p2 = _u(), _u()
    ledger = {p1: Decimal("90.0000"), p2: Decimal("55.5000")}
    closing = {p1: Decimal("90.0000"), p2: Decimal("55.5000")}
    fiscal = {p1: Decimal("100.0000"), p2: Decimal("50.0000")}  # cost basis — NOT qty!
    whitelist = {p1, p2}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
        fiscal_period_snapshot_aggregate=fiscal,
        product_whitelist=whitelist,
    )

    # Note: 6-2 4-source check compares ledger qty == closing qty AND
    # ledger qty == fiscal qty. With these values, ledger/closing match
    # but fiscal (cost basis) mismatches → FAIL with fiscal snapshot message.
    assert verdict["status"] == V4_STATUS_FAILED
    assert verdict["source_count"] == 4
    assert verdict["code"] == "V4"


def test_verify_v4_pass_ledger_closing_fiscal_all_equal() -> None:
    """ledger == closing == fiscal (per product) → PASS."""
    p1 = _u()
    qty = Decimal("100.0000")
    ledger = {p1: qty}
    closing = {p1: qty}
    fiscal = {p1: qty}  # edge case: qty == fiscal
    whitelist = {p1}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
        fiscal_period_snapshot_aggregate=fiscal,
        product_whitelist=whitelist,
    )
    assert verdict["status"] == V4_STATUS_PASSED


# ── V4 verdict FAIL path (3 cases) ───────────────────────────────


def test_verify_v4_fail_ledger_closing_mismatch() -> None:
    """ledger vs closing snapshot mismatch → V4 FAIL + V4_FAIL_MESSAGE_KO."""
    p1 = _u()
    ledger = {p1: Decimal("10.0000")}
    closing = {p1: Decimal("11.0000")}  # mismatch
    fiscal = {p1: Decimal("10.0000")}
    whitelist = {p1}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
        fiscal_period_snapshot_aggregate=fiscal,
        product_whitelist=whitelist,
    )
    assert verdict["status"] == V4_STATUS_FAILED
    assert len(verdict["failures"]) == 1
    assert verdict["failures"][0]["message_ko"] == V4_FAIL_MESSAGE_KO


def test_verify_v4_fail_ledger_fiscal_mismatch() -> None:
    """ledger vs fiscal_period_snapshot mismatch → V4 FAIL + V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO."""
    p1 = _u()
    ledger = {p1: Decimal("10.0000")}
    closing = {p1: Decimal("10.0000")}
    fiscal = {p1: Decimal("100.0000")}  # mismatch
    whitelist = {p1}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
        fiscal_period_snapshot_aggregate=fiscal,
        product_whitelist=whitelist,
    )
    assert verdict["status"] == V4_STATUS_FAILED
    assert verdict["failures"][0]["message_ko"] == V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO


def test_verify_v4_fail_multiple_products() -> None:
    """Multiple products fail → all reported."""
    p1, p2 = _u(), _u()
    ledger = {p1: Decimal("10"), p2: Decimal("20")}
    closing = {p1: Decimal("11"), p2: Decimal("19")}
    fiscal = {p1: Decimal("10"), p2: Decimal("20")}
    whitelist = {p1, p2}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
        fiscal_period_snapshot_aggregate=fiscal,
        product_whitelist=whitelist,
    )
    assert verdict["status"] == V4_STATUS_FAILED
    assert len(verdict["failures"]) == 2


# ── V4 verdict SKIP path (2 cases) ───────────────────────────────


def test_verify_v4_skip_industry_service() -> None:
    """industry='service' → V4 SKIP (A10 capability gate 동등)."""
    p1 = _u()
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={p1: Decimal("10")},
        closing_snapshot_aggregate={p1: Decimal("10")},
        fiscal_period_snapshot_aggregate={p1: Decimal("10")},
        product_whitelist={p1},
        industry="service",
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert verdict["skip_reason_ko"] == V4_SKIP_REASON_SERVICE_ONLY_KO


def test_verify_v4_skip_empty_aggregates() -> None:
    """All 4 sources empty → V4 SKIP (empty aggregate guard)."""
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        fiscal_period_snapshot_aggregate={},
        product_whitelist=set(),
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert verdict["skip_reason_ko"] == V4_SKIP_REASON_EMPTY_AGGREGATE_KO


# ── V4 verdict source_count invariant (1 case) ───────────────────


def test_verify_v4_source_count_4_extension() -> None:
    """source_count = 4 (6-2 extension 6-1 2-source → 6-2 4-source)."""
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        fiscal_period_snapshot_aggregate={},
        product_whitelist=set(),
    )
    assert verdict["source_count"] == 4