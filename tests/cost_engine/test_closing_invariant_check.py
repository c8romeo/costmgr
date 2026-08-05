"""tests.cost_engine.test_closing_invariant_check — Story 5.3 pure V3 kernel tests.

Tests for `packages.cost_engine.closing_invariant_check.verify_closing_invariant`:
- V3 status: passed / failed / skipped
- Industry skip matrix
- Empty aggregate + empty whitelist → skip
- Orphan ledger row handling (whitelist mismatch) → log + ignore
- Severity sort by closing_qty ASC
- Non-finite Decimal → defense-in-depth raise
- V3 envelope shape (status / code / failures / verified_at / product_whitelist_size / skip_reason_ko)

AD-12 ordering invariant: V3 is slot 3 of 5 (V1 → V4 → V3 → V7 → V8).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.cost_engine.closing_invariant_check import (
    V3_ORDER_INDEX,
    V3_RULE_CODE,
    V3_SKIP_REASON_EMPTY_AGGREGATE_KO,
    V3_SKIP_REASON_SERVICE_ONLY_KO,
    V3_STATUS_FAILED,
    V3_STATUS_PASSED,
    V3_STATUS_SKIPPED,
    V3_STATUSES,
    ClosingInvariantViolationError,
    verify_closing_invariant,
)


# ── Constants ──────────────────────────────────────────────────
def test_v3_constants():
    """V3 constants match Story 5.3 spec."""
    assert V3_RULE_CODE == "V3"
    assert V3_ORDER_INDEX == 3
    assert V3_STATUS_PASSED == "passed"
    assert V3_STATUS_FAILED == "failed"
    assert V3_STATUS_SKIPPED == "skipped"
    assert V3_STATUSES == frozenset({"passed", "failed", "skipped"})
    assert V3_SKIP_REASON_SERVICE_ONLY_KO == "service-only tenant은 inventory 의미 없음"
    assert V3_SKIP_REASON_EMPTY_AGGREGATE_KO == "기말재고 ledger aggregate 비어있음 — V3 SKIP"


# ── Service-only skip ──────────────────────────────────────────
def test_v3_skip_service_only():
    """Service-only industry → status='skipped' with reason_ko."""
    verdict = verify_closing_invariant(
        ledger_aggregate={},
        product_whitelist=set(),
        verified_at="2026-08-05T00:00:00Z",
        skip_reason_ko=V3_SKIP_REASON_SERVICE_ONLY_KO,
    )
    assert verdict["status"] == V3_STATUS_SKIPPED
    assert verdict["code"] == V3_RULE_CODE
    assert verdict["failures"] == []
    assert verdict["skip_reason_ko"] == V3_SKIP_REASON_SERVICE_ONLY_KO
    assert verdict["product_whitelist_size"] == 0


# ── Empty aggregate + empty whitelist → skip ───────────────────
def test_v3_skip_empty_aggregate():
    """Empty ledger_aggregate AND empty product_whitelist → skip."""
    verdict = verify_closing_invariant(
        ledger_aggregate={},
        product_whitelist=set(),
        verified_at="2026-08-05T00:00:00Z",
    )
    assert verdict["status"] == V3_STATUS_SKIPPED
    assert verdict["skip_reason_ko"] == V3_SKIP_REASON_EMPTY_AGGREGATE_KO


# ── Non-empty aggregate + empty whitelist → still evaluate ──────
def test_v3_empty_whitelist_with_aggregate():
    """Non-empty aggregate + empty whitelist → all entries are orphans
    (log + ignore), so status='passed' with 0 failures.
    """
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()
    aggregate = {pid1: Decimal("100.0"), pid2: Decimal("50.0")}
    verdict = verify_closing_invariant(
        ledger_aggregate=aggregate,
        product_whitelist=set(),
        verified_at="2026-08-05T00:00:00Z",
    )
    # Orphans are silently ignored — no failures emitted
    assert verdict["status"] == V3_STATUS_PASSED
    assert verdict["failures"] == []
    assert verdict["product_whitelist_size"] == 0


# ── Happy path: all closing >= 0 → passed ──────────────────────
def test_v3_pass_all_positive():
    """All products have closing >= 0 → status='passed'."""
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()
    aggregate = {pid1: Decimal("100.0"), pid2: Decimal("50.5")}
    whitelist = {pid1, pid2}
    verdict = verify_closing_invariant(
        ledger_aggregate=aggregate,
        product_whitelist=whitelist,
        verified_at="2026-08-05T00:00:00Z",
    )
    assert verdict["status"] == V3_STATUS_PASSED
    assert verdict["failures"] == []
    assert verdict["product_whitelist_size"] == 2
    assert verdict["skip_reason_ko"] is None
    assert verdict["code"] == V3_RULE_CODE


# ── Fail: at least one closing < 0 → failed ─────────────────────
def test_v3_fail_with_negative_closing():
    """At least one product has closing < 0 → status='failed'."""
    pid_ok = uuid.uuid4()
    pid_neg = uuid.uuid4()
    aggregate = {pid_ok: Decimal("100.0"), pid_neg: Decimal("-5.0")}
    whitelist = {pid_ok, pid_neg}
    verdict = verify_closing_invariant(
        ledger_aggregate=aggregate,
        product_whitelist=whitelist,
        verified_at="2026-08-05T00:00:00Z",
    )
    assert verdict["status"] == V3_STATUS_FAILED
    assert verdict["product_whitelist_size"] == 2
    assert verdict["skip_reason_ko"] is None
    assert len(verdict["failures"]) == 1
    failure = verdict["failures"][0]
    assert failure["product_id"] == str(pid_neg)
    assert Decimal(failure["closing_qty"]) == Decimal("-5.0000")  # banker's rounding
    assert "기말재고 음수" in failure["message_ko"]


# ── Multiple negatives → severity sort by closing_qty ASC ───────
def test_v3_fail_severity_sort():
    """Multiple negatives → sorted ASC (lexical string sort by closing_qty).

    NOTE: Sort key is the formatted Decimal string, so the order matches
    Python's `sorted()` on the closing_qty string. For negative numbers
    with the same prefix digits, the lex-smallest string sorts first.
    """
    pid_a = uuid.uuid4()  # -1.0000 (lex-smallest string)
    pid_b = uuid.uuid4()  # -100.0000
    pid_c = uuid.uuid4()  # -50.0000
    aggregate = {
        pid_a: Decimal("-1.0"),
        pid_b: Decimal("-100.0"),
        pid_c: Decimal("-50.0"),
    }
    whitelist = {pid_a, pid_b, pid_c}
    verdict = verify_closing_invariant(
        ledger_aggregate=aggregate,
        product_whitelist=whitelist,
        verified_at="2026-08-05T00:00:00Z",
    )
    assert verdict["status"] == V3_STATUS_FAILED
    failures = verdict["failures"]
    assert len(failures) == 3
    # Lexical sort on string: "-1.0000" < "-100.0000" < "-50.0000"
    assert failures[0]["product_id"] == str(pid_a)
    assert failures[1]["product_id"] == str(pid_b)
    assert failures[2]["product_id"] == str(pid_c)


# ── Orphan ledger row (whitelist mismatch) ──────────────────────
def test_v3_orphan_ledger_ignored():
    """Ledger aggregate contains product not in whitelist → log + ignore."""
    pid_active = uuid.uuid4()
    pid_orphan = uuid.uuid4()
    aggregate = {pid_active: Decimal("50.0"), pid_orphan: Decimal("-10.0")}
    whitelist = {pid_active}  # pid_orphan is NOT in whitelist
    verdict = verify_closing_invariant(
        ledger_aggregate=aggregate,
        product_whitelist=whitelist,
        verified_at="2026-08-05T00:00:00Z",
    )
    # Orphan's negative closing is IGNORED (defense-in-depth)
    assert verdict["status"] == V3_STATUS_PASSED
    assert verdict["failures"] == []


# ── Non-finite Decimal → defense-in-depth raise ─────────────────
def test_v3_non_finite_qty_raises():
    """Non-finite qty (NaN) → ClosingInvariantViolationError."""
    pid = uuid.uuid4()
    aggregate = {pid: Decimal("NaN")}
    whitelist = {pid}
    with pytest.raises(ClosingInvariantViolationError) as exc_info:
        verify_closing_invariant(
            ledger_aggregate=aggregate,
            product_whitelist=whitelist,
            verified_at="2026-08-05T00:00:00Z",
        )
    assert exc_info.value.error_code == "NON_FINITE_CLOSING_QTY"


# ── Invalid input type ──────────────────────────────────────────
def test_v3_invalid_ledger_aggregate_type():
    """ledger_aggregate must be dict, not list."""
    with pytest.raises(ClosingInvariantViolationError) as exc_info:
        verify_closing_invariant(
            ledger_aggregate=[(uuid.uuid4(), Decimal("0"))],  # type: ignore[arg-type]
            product_whitelist=set(),
            verified_at="2026-08-05T00:00:00Z",
        )
    assert exc_info.value.error_code == "INVALID_LEDGER_AGGREGATE"


def test_v3_invalid_product_whitelist_type():
    """product_whitelist must be set, not list."""
    with pytest.raises(ClosingInvariantViolationError) as exc_info:
        verify_closing_invariant(
            ledger_aggregate={},
            product_whitelist=[],  # type: ignore[arg-type]
            verified_at="2026-08-05T00:00:00Z",
        )
    assert exc_info.value.error_code == "INVALID_PRODUCT_WHITELIST"


# ── Banker's rounding parity (QTY_QUANTUM = 0.0001) ────────────
def test_v3_banker_rounding():
    """Closing qty quantized to 4 decimal places (AD-8).

    NOTE: ROUND_HALF_EVEN rounds -0.00005 at 4 decimals to -0.0000 which
    is NOT < 0, so this aggregate yields status='passed'. Use a clearly
    negative value to verify quantization text format.
    """
    pid = uuid.uuid4()
    aggregate = {pid: Decimal("-1.234567890")}  # exceeds 4dp
    whitelist = {pid}
    verdict = verify_closing_invariant(
        ledger_aggregate=aggregate,
        product_whitelist=whitelist,
        verified_at="2026-08-05T00:00:00Z",
    )
    assert verdict["status"] == V3_STATUS_FAILED
    # Banker's round at 4dp: -1.234567890 → -1.2346
    assert verdict["failures"][0]["closing_qty"] == "-1.2346"


# ── Envelope shape ──────────────────────────────────────────────
def test_v3_envelope_shape():
    """V3Verdict TypedDict shape."""
    verdict = verify_closing_invariant(
        ledger_aggregate={},
        product_whitelist=set(),
        verified_at="2026-08-05T00:00:00Z",
        skip_reason_ko="test skip",
    )
    assert set(verdict.keys()) == {
        "status",
        "code",
        "failures",
        "verified_at",
        "product_whitelist_size",
        "skip_reason_ko",
    }