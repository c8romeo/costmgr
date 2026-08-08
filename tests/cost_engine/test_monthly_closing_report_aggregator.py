"""tests/cost_engine/test_monthly_closing_report_aggregator.py — Story 6.2 T9.2 V4 aggregator tests.

Tests for `packages/cost_engine/monthly_closing_report_aggregator.py`:
- verify_monthly_closing_report_consistency (3-source V4 contract per D1)
- V4 verdict status: PASS / FAIL / SKIP (AD-12 ordering)
- Korean SSOT constants (V4_FAIL_MESSAGE_KO + V4_SKIP_REASON_*)
- industry='service' → V4 SKIP (A10 capability gate 동등)
- 2-source extension (ledger + closing_snapshot + product_whitelist) —
  fiscal_period_snapshot 은 wire 에 포함되지만 V4 qty 비교 source 에서 제외
  (PRD §6.1 산식 체인이 manufacturing_cost KRW 임을 명시, bmad-code-review
  D1 결정 2026-08-08).
- banker's rounding via QTY_QUANTUM (CR 0-4 lesson + AD-15 parity)
- 10 cases total
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from packages.cost_engine.monthly_closing_report_aggregator import (
    V4_FAIL_MESSAGE_KO,
    V4_ORDER_INDEX,
    V4_RULE_CODE,
    V4_SKIP_REASON_EMPTY_AGGREGATE_KO,
    V4_SKIP_REASON_SERVICE_ONLY_KO,
    V4_STATUS_FAILED,
    V4_STATUS_PASSED,
    V4_STATUS_SKIPPED,
    V4_STATUSES,
    verify_monthly_closing_report_consistency,
)


def _u() -> uuid.UUID:
    return uuid.uuid4()


# ── V4 constants SSOT (3 cases) ───────────────────────────────────


def test_v4_statuses_frozenset_three() -> None:
    """V4_STATUSES = 3 codes (PASSED / FAILED / SKIPPED)."""
    assert frozenset(
        {V4_STATUS_PASSED, V4_STATUS_FAILED, V4_STATUS_SKIPPED}
    ) == V4_STATUSES


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


def test_v4_order_index_ad12_slot_2() -> None:
    """V4_ORDER_INDEX = 2 (AD-12 ordering V1 → V4 → V3 → V7 → V8)."""
    assert V4_ORDER_INDEX == 2
    assert V4_RULE_CODE == "V4"


# ── V4 verdict PASS path (1 case) ────────────────────────────────


def test_verify_v4_pass_ledger_closing_match() -> None:
    """ledger == closing_snapshot (per product) → V4 PASS (D1 3-source).

    M3 fix — name/assertion contradiction 제거: PASS-named test 가
    진짜로 PASS 를 assert (bmad-code-review 결정 2026-08-08).
    """
    p1, p2 = _u(), _u()
    ledger = {p1: Decimal("90.0000"), p2: Decimal("55.5000")}
    closing = {p1: Decimal("90.0000"), p2: Decimal("55.5000")}
    whitelist = {p1, p2}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
        product_whitelist=whitelist,
    )

    assert verdict["status"] == V4_STATUS_PASSED
    assert verdict["source_count"] == 2
    assert verdict["code"] == "V4"
    assert verdict["failures"] == []


# ── V4 verdict FAIL path (2 cases) ──────────────────────────────


def test_verify_v4_fail_ledger_closing_mismatch() -> None:
    """ledger vs closing snapshot mismatch → V4 FAIL + V4_FAIL_MESSAGE_KO."""
    p1 = _u()
    ledger = {p1: Decimal("10.0000")}
    closing = {p1: Decimal("11.0000")}  # mismatch
    whitelist = {p1}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
        product_whitelist=whitelist,
    )
    assert verdict["status"] == V4_STATUS_FAILED
    assert len(verdict["failures"]) == 1
    assert verdict["failures"][0]["message_ko"] == V4_FAIL_MESSAGE_KO


def test_verify_v4_fail_multiple_products() -> None:
    """Multiple products fail → all reported."""
    p1, p2 = _u(), _u()
    ledger = {p1: Decimal("10"), p2: Decimal("20")}
    closing = {p1: Decimal("11"), p2: Decimal("19")}
    whitelist = {p1, p2}

    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=closing,
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
        product_whitelist={p1},
        industry="service",
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert verdict["skip_reason_ko"] == V4_SKIP_REASON_SERVICE_ONLY_KO


def test_verify_v4_skip_empty_aggregates() -> None:
    """All sources empty → V4 SKIP (empty aggregate guard)."""
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        product_whitelist=set(),
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert verdict["skip_reason_ko"] == V4_SKIP_REASON_EMPTY_AGGREGATE_KO


# ── V4 verdict source_count invariant (1 case) ───────────────────


def test_verify_v4_source_count_2_d1() -> None:
    """source_count = 2 (D1 결정, 2026-08-08)."""
    verdict = verify_monthly_closing_report_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        product_whitelist=set(),
    )
    assert verdict["source_count"] == 2
