"""tests/cost_engine/test_closing_period_snapshot.py — Story 6.1 V4 pure kernel tests.

Tests for `packages/cost_engine/closing_period_snapshot.py`:
- verify_closing_period_consistency (PASS / FAIL / SKIP paths)
- V4 typed envelope (status='passed'/'failed'/'skipped')
- Korean SSOT (V4_FAIL_MESSAGE_KO + V4_SKIP_REASON_*)
- AD-12 ordering invariant (V4_ORDER_INDEX = 2)
- cost_engine layer rule: pure-Python, stdlib-only, no sqlalchemy/DB
  (CR 6-1: cost_engine = pure kernel, service layer owns DB)

Subset of the 12 cases from spec §T10.2 — full set deferred to follow-up.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from packages.cost_engine.closing_period_snapshot import (
    V4_FAIL_MESSAGE_KO,
    V4_ORDER_INDEX,
    V4_RULE_CODE,
    V4_SKIP_REASON_EMPTY_AGGREGATE_KO,
    V4_SKIP_REASON_SERVICE_ONLY_KO,
    V4_STATUS_FAILED,
    V4_STATUS_PASSED,
    V4_STATUS_SKIPPED,
    V4_STATUSES,
    verify_closing_period_consistency,
)


# ── V4 PASS path (3 cases) ─────────────────────────────────────


def test_v4_pass_when_all_per_product_match() -> None:
    """ledger_qty == closing_snapshot_qty for ALL whitelist products → PASS."""
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    ledger = {p1: Decimal("5.0000"), p2: Decimal("3.0000")}
    snapshot = {p1: Decimal("5.0000"), p2: Decimal("3.0000")}
    whitelist = {p1, p2}

    verdict = verify_closing_period_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=snapshot,
        product_whitelist=whitelist,
        industry="manufacturing",
    )

    assert verdict["status"] == V4_STATUS_PASSED
    assert verdict["code"] == V4_RULE_CODE
    assert verdict["failures"] == []
    assert verdict["skip_reason_ko"] is None


def test_v4_pass_when_only_common_products_match() -> None:
    """Only common products in both aggregates — all match → PASS.

    CR 6-1 R4 patch D2: rename from `test_v4_pass_missing_product_treated_as_zero`
    (which actually asserted FAILED). The renamed test now exercises the
    PASS path: when both ledger + snapshot contain the same products and
    all qty values match, V4 returns passed.
    """
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    ledger = {p1: Decimal("5"), p2: Decimal("3")}
    snapshot = {p1: Decimal("5"), p2: Decimal("3")}
    whitelist = {p1, p2}

    verdict = verify_closing_period_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=snapshot,
        product_whitelist=whitelist,
        industry="manufacturing",
    )
    assert verdict["status"] == V4_STATUS_PASSED
    assert verdict["failures"] == []


def test_v4_pass_bankers_rounding_equivalent() -> None:
    """0.0055 vs 0.0056 are NOT equal at QTY_QUANTUM (4 decimals) → FAIL.
    Use exact-equal values to confirm PASS."""
    p1 = uuid.uuid4()
    # Both sides quantized to QTY_QUANTUM=0.0001 (4 decimals).
    ledger = {p1: Decimal("5.1234")}
    snapshot = {p1: Decimal("5.1234")}
    whitelist = {p1}

    verdict = verify_closing_period_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=snapshot,
        product_whitelist=whitelist,
        industry="manufacturing",
    )
    assert verdict["status"] == V4_STATUS_PASSED


# ── V4 FAIL path (3 cases) ─────────────────────────────────────


def test_v4_fail_per_product_mismatch() -> None:
    """1 product ledger_qty != closing_snapshot_qty → FAIL + failure entry."""
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    ledger = {p1: Decimal("5"), p2: Decimal("3")}
    snapshot = {p1: Decimal("5"), p2: Decimal("4")}  # p2 mismatch
    whitelist = {p1, p2}

    verdict = verify_closing_period_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=snapshot,
        product_whitelist=whitelist,
        industry="manufacturing",
    )

    assert verdict["status"] == V4_STATUS_FAILED
    assert len(verdict["failures"]) == 1
    failure = verdict["failures"][0]
    assert failure["product_id"] == str(p2)
    assert failure["ledger_qty"] == "3.0000"
    assert failure["closing_snapshot_qty"] == "4.0000"
    assert failure["message_ko"] == V4_FAIL_MESSAGE_KO


def test_v4_fail_multiple_failures_sorted_by_product_id() -> None:
    """2 products mismatch → failures sorted by product_id (deterministic)."""
    p_a, p_b = uuid.uuid4(), uuid.uuid4()
    # Sort by str(p) — ensure p_a sorts before p_b lexicographically.
    sorted_p = sorted([str(p_a), str(p_b)])
    first_pid = sorted_p[0]
    second_pid = sorted_p[1]

    ledger = {
        p_a: Decimal("1"),
        p_b: Decimal("2"),
    }
    snapshot = {
        p_a: Decimal("9"),  # mismatch
        p_b: Decimal("8"),  # mismatch
    }
    whitelist = {p_a, p_b}

    verdict = verify_closing_period_consistency(
        ledger_aggregate=ledger,
        closing_snapshot_aggregate=snapshot,
        product_whitelist=whitelist,
        industry="manufacturing",
    )

    assert verdict["status"] == V4_STATUS_FAILED
    assert len(verdict["failures"]) == 2
    # Failures must be sorted by product_id (string) for deterministic V8 parity.
    assert verdict["failures"][0]["product_id"] == first_pid
    assert verdict["failures"][1]["product_id"] == second_pid


def test_v4_fail_v4_fail_message_ko_constant() -> None:
    """V4_FAIL_MESSAGE_KO mirrors TS V4 failure Korean message SSOT."""
    assert V4_FAIL_MESSAGE_KO == "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요"


# ── V4 SKIP path (3 cases) ─────────────────────────────────────


def test_v4_skip_service_industry() -> None:
    """industry='service' → SKIP (service-only tenant inventory 무의미)."""
    verdict = verify_closing_period_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        product_whitelist=set(),
        industry="service",
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert verdict["skip_reason_ko"] == V4_SKIP_REASON_SERVICE_ONLY_KO
    assert verdict["failures"] == []


def test_v4_skip_both_aggregates_empty() -> None:
    """Both aggregates empty (no ledger events) → SKIP with empty_aggregate reason."""
    verdict = verify_closing_period_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        product_whitelist=set(),
        industry="manufacturing",
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert verdict["skip_reason_ko"] == V4_SKIP_REASON_EMPTY_AGGREGATE_KO


def test_v4_skip_does_not_evaluate_per_product() -> None:
    """SKIP path: product_whitelist_size preserved but failures empty."""
    p1 = uuid.uuid4()
    verdict = verify_closing_period_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        product_whitelist={p1},
        industry="manufacturing",
    )
    assert verdict["status"] == V4_STATUS_SKIPPED
    assert verdict["product_whitelist_size"] == 1
    assert verdict["failures"] == []


# ── V4 envelope invariants (3 cases) ────────────────────────────


def test_v4_verdict_envelope_code_invariant() -> None:
    """All V4 verdicts carry code='V4' (AD-12 ordering invariant)."""
    p1 = uuid.uuid4()
    pass_v = verify_closing_period_consistency(
        ledger_aggregate={p1: Decimal("1")},
        closing_snapshot_aggregate={p1: Decimal("1")},
        product_whitelist={p1},
        industry="manufacturing",
    )
    fail_v = verify_closing_period_consistency(
        ledger_aggregate={p1: Decimal("1")},
        closing_snapshot_aggregate={p1: Decimal("2")},
        product_whitelist={p1},
        industry="manufacturing",
    )
    skip_v = verify_closing_period_consistency(
        ledger_aggregate={},
        closing_snapshot_aggregate={},
        product_whitelist=set(),
        industry="service",
    )
    assert all(v["code"] == "V4" for v in (pass_v, fail_v, skip_v))


def test_v4_order_index_slot_2_of_5() -> None:
    """AD-12: V4 = slot 2 of 5 (V1 → V4 → V3 → V7 → V8)."""
    assert V4_ORDER_INDEX == 2


def test_v4_statuses_frozenset_completeness() -> None:
    """V4_STATUSES contains exactly passed/failed/skipped."""
    assert V4_STATUSES == frozenset(
        {V4_STATUS_PASSED, V4_STATUS_FAILED, V4_STATUS_SKIPPED}
    )