"""Tests for Story 11.6 EXTENSION `compute_report15_hash` V8 determinism (Surface 8).

Coverage (11-6 wire Surface 8 — V8 byte-equality):
  - compute_report15_hash SHA-256 hexdigest format (2 cases)
  - V8 determinism 100 repeats with identical input (2 cases)
  - V8 sensitive to period_key + activity_breakdown + v7_verdict (2 cases)

Total: ~6 NEW pytest cases (T6.x) — V8 byte-equality invariant 검증.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    REPORT15_HASH_PREFIX,
    ActivityCostRow,
    compute_report15_hash,
    verify_v7_balance,
)


def _mk_row(
    *,
    activity_id: str = "act-1",
    total_cost_krw: str = "6600000",
    total_cost_usd: str = "4950",
    driver_count: int = 4,
) -> ActivityCostRow:
    """Helper — ActivityCostRow fixture (V8 determinism test surface)."""
    cost_per_driver_krw = str(int(Decimal(total_cost_krw) / driver_count))
    cost_per_driver_usd = str(Decimal(total_cost_usd) / driver_count)
    return ActivityCostRow(
        activity_id=activity_id,
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal(total_cost_krw),
        total_cost_usd=Decimal(total_cost_usd),
        driver_count=driver_count,
        cost_per_driver_krw=Decimal(cost_per_driver_krw),
        cost_per_driver_usd=Decimal(cost_per_driver_usd),
        allocated_krw=Decimal(total_cost_krw),
        allocated_usd=Decimal(total_cost_usd),
        hash="placeholder",
    )


def _mk_v7(
    *,
    breakdown_sum: str = "6600000",
    unused_cost: str = "0",
    department_cost: str = "6600000",
) -> object:
    """Helper — V7Verdict fixture."""
    return verify_v7_balance(
        total_breakdown_sum=Decimal(breakdown_sum),
        unused_cost=Decimal(unused_cost),
        department_cost=Decimal(department_cost),
    )


# ── compute_report15_hash SHA-256 hexdigest format (2 cases) ────────────


@pytest.mark.engine
def test_report15_hash_prefix_and_hexdigest_length() -> None:
    """V8 invariant — hash = "sha256:" + 64 hex chars."""
    row = _mk_row()
    v7 = _mk_v7()
    digest = compute_report15_hash(
        activity_breakdown=[row],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    assert digest.startswith(REPORT15_HASH_PREFIX)
    hex_part = digest[len(REPORT15_HASH_PREFIX):]
    assert len(hex_part) == 64
    int(hex_part, 16)  # hex parseable — ValueError if not


@pytest.mark.engine
def test_report15_hash_is_lowercase_hex() -> None:
    """V8 invariant — hexdigest is lowercase (Pydantic v2 + JSON-safe)."""
    row = _mk_row()
    v7 = _mk_v7()
    digest = compute_report15_hash(
        activity_breakdown=[row],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    hex_part = digest[len(REPORT15_HASH_PREFIX):]
    assert hex_part == hex_part.lower()


# ── V8 determinism 100 repeats (2 cases) ────────────


@pytest.mark.engine
def test_report15_hash_v8_determinism_100_repeats() -> None:
    """V8 invariant — 동일 input → byte-identical hash 100회."""
    row = _mk_row()
    v7 = _mk_v7()
    first = compute_report15_hash(
        activity_breakdown=[row],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    for _ in range(100):
        got = compute_report15_hash(
            activity_breakdown=[row],
            period_key="2026-Q1",
            v7_verdict=v7,  # type: ignore[arg-type]
        )
        assert got == first


@pytest.mark.engine
def test_report15_hash_v8_different_order_different_digest() -> None:
    """V8 sensitivity — activity_breakdown 순서 변경 시 digest 변경
    (PRD §9 #15 verbatim — 활동별 행의 순서가 의미를 가지므로 order-sensitive).

    Note: Report #15 는 order-sensitive 입니다 (compute_report15_hash 가 list 를
    직접 canonical form 으로 변환하지 않음). Service layer 에서 사전 정렬 후
    hash 호출 필요 — future sprint 결정 wire.
    """
    row1 = _mk_row(activity_id="act-1")
    row2 = _mk_row(activity_id="act-2", total_cost_krw="3300000")
    v7 = _mk_v7(breakdown_sum="9900000")
    digest_ordered = compute_report15_hash(
        activity_breakdown=[row1, row2],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    digest_swapped = compute_report15_hash(
        activity_breakdown=[row2, row1],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    assert digest_ordered != digest_swapped


# ── V8 sensitive to inputs (2 cases) ────────────


@pytest.mark.engine
def test_report15_hash_different_period_key_changes_digest() -> None:
    """V8 sensitivity — period_key 변경 시 digest 변경."""
    row = _mk_row()
    v7 = _mk_v7()
    digest_q1 = compute_report15_hash(
        activity_breakdown=[row],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    digest_q2 = compute_report15_hash(
        activity_breakdown=[row],
        period_key="2026-Q2",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    assert digest_q1 != digest_q2


@pytest.mark.engine
def test_report15_hash_different_activity_breakdown_changes_digest() -> None:
    """V8 sensitivity — activity_breakdown 변경 시 digest 변경."""
    row1 = _mk_row()
    row2 = _mk_row(activity_id="act-2", total_cost_krw="3300000")
    v7 = _mk_v7()
    digest_one = compute_report15_hash(
        activity_breakdown=[row1],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    digest_two = compute_report15_hash(
        activity_breakdown=[row1, row2],
        period_key="2026-Q1",
        v7_verdict=v7,  # type: ignore[arg-type]
    )
    assert digest_one != digest_two
