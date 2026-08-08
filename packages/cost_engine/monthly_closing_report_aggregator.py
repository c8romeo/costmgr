"""packages.cost_engine.monthly_closing_report_aggregator — Story 6.2 V4 pure kernel.

V4 (closing snapshot 일관성 verification) 4-source extension for Monthly
Closing Report (PRD §F5 + §V4 + §A11 4-layer defense).

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py`
  (T4 V4 slot fill — verify_v4_closing_period_consistency dispatch
  extension to 4-source aggregate)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes
ledger_aggregate (dict[UUID, Decimal]) + closing_snapshot_aggregate
(dict[UUID, Decimal]) + fiscal_period_snapshot_aggregate
(dict[UUID, Decimal]) + product_whitelist (set[UUID]) as arguments;
this kernel owns the 4-source V4 verdict logic + per-product
inconsistency check.

4-source aggregate (extension 6-1 2-source → 6-2 4-source):
1. ledger_aggregate (5-2 wire — `LedgerService.query_period_closing`).
2. closing_snapshot_aggregate (5-2 wire — closing_snapshot ledger events).
3. fiscal_period_snapshot_aggregate (4-2 wire — fiscal_period_snapshots
   engine_type='trad' cost data).
4. product_whitelist (current tenant active product UUID set).

V4 verdict (extension 6-1 → 6-2):
- PASS: 4 source 모두 일치 (per-product qty 일치 + fiscal_period_snapshot
  aggregate 합 일치).
- FAIL: 1+ source per-product qty 불일치.
- SKIP: industry='service' OR 4 source 모두 empty.

V4 fixture parity: 6-2 ships 2 NEW 골든 fixtures (extension 6-1 wire):
- `v4_closing_period_pass_manufacturing.json` (6-1 T10.5 deferred fill).
- `v4_closing_period_fail_manufacturing.json` (6-1 T10.5 deferred fill).
- Plus 2 NEW A11 골든 fixtures (closing_snapshot + ledger_period_closing).
- V8 fixture count: 14 → 16 → 18.

AD-12 ordering invariant (Story 4-3 wire + 5-3 wire + 6-1 wire). V4
is slot 2 of 5. V1 (completeness) → V4 (closing snapshot 일관성) →
V3 (closing ≥ 0) → V7 (ABC integrity) → V8 (byte-identical golden match).
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, TypedDict

from packages.services.m2_input.inventory_projection import QTY_QUANTUM

# ── Constants ────────────────────────────────────────────────
# V4 verdict status (matches Story 4-3 V1·V3·V7·V8 verbatim + 5-3 V3 +
# 6-1 V4).
V4_STATUS_PASSED: Final[str] = "passed"
V4_STATUS_FAILED: Final[str] = "failed"
V4_STATUS_SKIPPED: Final[str] = "skipped"

V4_STATUSES: Final[frozenset[str]] = frozenset(
    {V4_STATUS_PASSED, V4_STATUS_FAILED, V4_STATUS_SKIPPED}
)

# AD-12 ordering invariant (Story 4-3 wire + 5-3 wire + 6-1 wire). V4
# is slot 2 of 5.
V4_ORDER_INDEX: Final[int] = 2
V4_RULE_CODE: Final[str] = "V4"

# V4 skip reason (Korean SSOT for service-only tenant + empty aggregate).
V4_SKIP_REASON_SERVICE_ONLY_KO: Final[str] = "service-only tenant은 inventory 의미 없음"
V4_SKIP_REASON_EMPTY_AGGREGATE_KO: Final[str] = (
    "기말재고 ledger aggregate 비어있음 — V4 SKIP"
)

# V4 fail Korean message SSOT (AD-15 §11 parity with TS).
V4_FAIL_MESSAGE_KO: Final[str] = (
    "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요"
)

# V4 fiscal_period_snapshot inconsistency Korean message (extension).
V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO: Final[str] = (
    "마감 snapshot 불일치: fiscal_period_snapshot aggregate vs ledger aggregate 갱신 필요"
)


# ── TypedDict shapes ─────────────────────────────────────────
class V4Failure(TypedDict):
    """Per-product closing snapshot inconsistency (extension 6-1 → 6-2).

    AD-15: snake_case field names. Mirrors TS `V4Failure` (future
    Story 6-2 Monthly Closing Report wire).

    - `product_id`: UUID string for JSON serialization (AD-15).
    - `ledger_qty`: Decimal string (AD-8 monetary parity).
    - `closing_snapshot_qty`: Decimal string (AD-8 monetary parity).
    - `fiscal_period_snapshot_qty`: Decimal string (AD-8 — 4-2 wire).
    - `message_ko`: Korean failure message (AD-15 §11).
    """

    product_id: str
    ledger_qty: str
    closing_snapshot_qty: str
    fiscal_period_snapshot_qty: str
    message_ko: str


class V4Verdict(TypedDict):
    """V4 verdict envelope (extension 6-1 → 6-2 4-source).

    Mirrors `packages/cost_engine/protocol.py::Verdict` shape (AD-15).
    `failures` is empty when status='passed' or 'skipped'.
    """

    status: str  # V4_STATUS_PASSED / FAILED / SKIPPED
    code: str  # always 'V4' for this rule
    failures: list[V4Failure]
    verified_at: str  # ISO8601 UTC string
    product_whitelist_size: int
    skip_reason_ko: str | None  # None unless status='skipped'
    source_count: int  # 6-2 extension — 4 (closing + ledger + fiscal + product)


# ── V4 typed exception (pure-kernel domain semantics) ─────────
class MonthlyClosingReportInconsistencyError(Exception):
    """Pure-kernel V4 inconsistency detected (defense-in-depth).

    Distinct from service-layer typed exceptions. NO HTTP mapping;
    service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        product_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.product_id = product_id


# ── verify_monthly_closing_report_consistency ─────────────────
def verify_monthly_closing_report_consistency(
    *,
    ledger_aggregate: dict[uuid.UUID, Decimal],
    closing_snapshot_aggregate: dict[uuid.UUID, Decimal],
    fiscal_period_snapshot_aggregate: dict[uuid.UUID, Decimal],
    product_whitelist: set[uuid.UUID],
    industry: str | None = None,
) -> V4Verdict:
    """V4 rule pure kernel — 4-source closing snapshot 일관성 verification.

    Per-product qty 일치 검증: ledger_aggregate[pid] ==
    closing_snapshot_aggregate[pid] == fiscal_period_snapshot_aggregate[pid]
    for all pid in product_whitelist. Banker's rounding
    (ROUND_HALF_EVEN) at QTY_QUANTUM applied for deterministic parity
    (CR 0-4 lesson + AD-15 §11).

    Args:
        ledger_aggregate: dict[product_id → closing_qty] from 5-2
            `LedgerService.query_period_closing` (5-2 wire SSOT).
        closing_snapshot_aggregate: dict[product_id → closing_qty]
            from inventory_ledger event_type='closing_snapshot' aggregate
            (5-2 wire 진입점, 6-1 confirms).
        fiscal_period_snapshot_aggregate: dict[product_id → cost]
            from `fiscal_period_snapshots` engine_type='trad' aggregate
            (4-2 wire — PRD §6.1 산식 체인).
        product_whitelist: set of product_ids to verify (caller filters
            active products; service layer from session).
        industry: Industry SSOT (Story 4-3 wire). 'service' → SKIP.

    Returns:
        V4Verdict TypedDict:
        - status='skipped' if industry='service' OR all aggregates empty.
        - status='passed' if all per-product qty + cost match.
        - status='failed' if any per-product qty/cost mismatch.
    """
    # V4 SKIP — industry='service' (service-only tenant inventory 무의미)
    if industry == "service":
        return _v4_skipped(
            reason_ko=V4_SKIP_REASON_SERVICE_ONLY_KO,
            whitelist_size=len(product_whitelist),
            source_count=4,
        )

    # V4 SKIP — all aggregates empty (no ledger events at all)
    if (
        not ledger_aggregate
        and not closing_snapshot_aggregate
        and not fiscal_period_snapshot_aggregate
    ):
        return _v4_skipped(
            reason_ko=V4_SKIP_REASON_EMPTY_AGGREGATE_KO,
            whitelist_size=len(product_whitelist),
            source_count=4,
        )

    failures: list[V4Failure] = []
    verified_at = _iso_now_static_placeholder()

    # Per-product 4-source consistency check.
    # Note: 6-2 extension includes fiscal_period_snapshot_aggregate
    # (4-2 wire). When a product is in closing_snapshot but not in
    # fiscal_period_snapshot aggregate, default to 0 (no fiscal snapshot).
    all_product_ids: set[uuid.UUID] = (
        set(ledger_aggregate)
        | set(closing_snapshot_aggregate)
        | set(fiscal_period_snapshot_aggregate)
        | set(product_whitelist)
    )

    for pid in sorted(all_product_ids, key=str):
        ledger_qty = ledger_aggregate.get(pid, Decimal("0"))
        closing_qty = closing_snapshot_aggregate.get(pid, Decimal("0"))
        fiscal_qty = fiscal_period_snapshot_aggregate.get(pid, Decimal("0"))

        # Banker's rounding at QTY_QUANTUM for deterministic comparison
        ledger_q = ledger_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
        closing_q = closing_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
        fiscal_q = fiscal_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)

        # 4-source aggregate check (ledger == closing_snapshot ==
        # fiscal_period_snapshot per product). 6-1 wire check was
        # 2-source (ledger + closing_snapshot). 6-2 extension adds
        # fiscal_period_snapshot.
        if ledger_q != closing_q:
            failures.append(
                V4Failure(
                    product_id=str(pid),
                    ledger_qty=f"{ledger_q:f}",
                    closing_snapshot_qty=f"{closing_q:f}",
                    fiscal_period_snapshot_qty=f"{fiscal_q:f}",
                    message_ko=V4_FAIL_MESSAGE_KO,
                )
            )
        elif ledger_q != fiscal_q:
            # Extension 6-2 — fiscal_period_snapshot mismatch check.
            failures.append(
                V4Failure(
                    product_id=str(pid),
                    ledger_qty=f"{ledger_q:f}",
                    closing_snapshot_qty=f"{closing_q:f}",
                    fiscal_period_snapshot_qty=f"{fiscal_q:f}",
                    message_ko=V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO,
                )
            )

    status = V4_STATUS_FAILED if failures else V4_STATUS_PASSED
    return V4Verdict(
        status=status,
        code=V4_RULE_CODE,
        failures=failures,
        verified_at=verified_at,
        product_whitelist_size=len(product_whitelist),
        skip_reason_ko=None,
        source_count=4,
    )


# ── Internal helpers ─────────────────────────────────────────
def _v4_skipped(*, reason_ko: str, whitelist_size: int, source_count: int) -> V4Verdict:
    """Build a SKIP V4Verdict (Korean SSOT)."""
    return V4Verdict(
        status=V4_STATUS_SKIPPED,
        code=V4_RULE_CODE,
        failures=[],
        verified_at=_iso_now_static_placeholder(),
        product_whitelist_size=whitelist_size,
        skip_reason_ko=reason_ko,
        source_count=source_count,
    )


def _iso_now_static_placeholder() -> str:
    """Return a static placeholder ISO-8601 timestamp.

    AD-5: pure kernel has no clock. Caller (service layer) MUST
    overwrite `verified_at` with the real ISO-8601 UTC timestamp from
    `datetime.now(UTC).isoformat()` before returning the verdict to
    the response. This placeholder exists so the V4Verdict shape is
    complete at pure-kernel construction.
    """
    return "1970-01-01T00:00:00+00:00"


__all__ = [
    "V4_FAIL_MESSAGE_KO",
    "V4_FISCAL_SNAPSHOT_FAIL_MESSAGE_KO",
    "V4_ORDER_INDEX",
    "V4_RULE_CODE",
    "V4_SKIP_REASON_EMPTY_AGGREGATE_KO",
    "V4_SKIP_REASON_SERVICE_ONLY_KO",
    "V4_STATUSES",
    "V4_STATUS_FAILED",
    "V4_STATUS_PASSED",
    "V4_STATUS_SKIPPED",
    "MonthlyClosingReportInconsistencyError",
    "V4Failure",
    "V4Verdict",
    "verify_monthly_closing_report_consistency",
]
