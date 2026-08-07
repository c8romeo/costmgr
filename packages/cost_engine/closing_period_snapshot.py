"""packages.cost_engine.closing_period_snapshot — Story 6.1 V4 pure kernel.

V4 (closing snapshot 일관성 verification) pure rule.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py`
  (T4 service layer — verify_v4_closing_period_consistency dispatch)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes
ledger_aggregate (dict[UUID, Decimal]) + closing_snapshot_aggregate
(dict[UUID, Decimal]) + product_whitelist (set[UUID]) as arguments;
this kernel owns the V4 verdict logic + per-product inconsistency check.

V4 fixture parity: 6-1 ships 2 NEW 골든 fixtures:
- `v4_closing_period_pass_manufacturing.json` (all ledger == closing_snapshot)
- `v4_closing_period_fail_manufacturing.json` (>=1 per-product mismatch)
- V8 fixture count: 14 → 16.
- AD-12 ordering: V4 succeeds BEFORE V3 (closing ≥ 0 invariant) +
  V7 (ABC integrity) + V8 (byte-identical golden match).
  V1 → V4 → V3 → V7 → V8 ordering invariant preserved.

PRD §V4 closing snapshot 일관성 verification:
- "closing snapshot 일관성" — ledger aggregate (5-2 `query_period_closing`)
  vs closing_snapshot ledger events aggregate (5-2 inventory_ledger
  event_type='closing_snapshot') per-product 일치 검증.
- V4 fail → top_failure.code='V4' + block_reason=
  'CLOSING_PERIOD_SNAPSHOT_INCONSISTENCY' + Korean message SSOT.
- V4 skip → industry='service' (service-only tenant inventory 무의미)
  OR ledger_aggregate empty + no products in whitelist.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, TypedDict

from packages.services.m2_input.inventory_projection import QTY_QUANTUM

# ── Constants ────────────────────────────────────────────────
# V4 verdict status (matches Story 4-3 V1·V3·V7·V8 verbatim + 5-3 V3).
V4_STATUS_PASSED: Final[str] = "passed"
V4_STATUS_FAILED: Final[str] = "failed"
V4_STATUS_SKIPPED: Final[str] = "skipped"

V4_STATUSES: Final[frozenset[str]] = frozenset(
    {V4_STATUS_PASSED, V4_STATUS_FAILED, V4_STATUS_SKIPPED}
)

# AD-12 ordering invariant (Story 4-3 wire + 5-3 wire). V4 is slot 2 of 5.
# V1 (completeness) → V4 (closing snapshot 일관성) → V3 (closing ≥ 0) →
# V7 (ABC integrity) → V8 (byte-identical golden match).
V4_ORDER_INDEX: Final[int] = 2
V4_RULE_CODE: Final[str] = "V4"

# V4 skip reason (Korean SSOT for service-only tenant + empty aggregate).
V4_SKIP_REASON_SERVICE_ONLY_KO: Final[str] = "service-only tenant은 inventory 의미 없음"
V4_SKIP_REASON_EMPTY_AGGREGATE_KO: Final[str] = (
    "기말재고 ledger aggregate 비어있음 — V4 SKIP"
)

# V4 fail Korean message SSOT (AD-15 §11 parity with TS).
V4_FAIL_MESSAGE_KO: Final[str] = "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요"


# ── TypedDict shapes ─────────────────────────────────────────
class V4Failure(TypedDict):
    """Per-product closing snapshot inconsistency.

    AD-15: snake_case field names. Mirrors TS `V4Failure` (future
    Story 6-2 Monthly Closing Report wire).

    - `product_id`: UUID string for JSON serialization (AD-15).
    - `ledger_qty`: Decimal string (AD-8 monetary parity).
    - `closing_snapshot_qty`: Decimal string (AD-8 monetary parity).
    - `message_ko`: Korean failure message (AD-15 §11).
    """

    product_id: str
    ledger_qty: str
    closing_snapshot_qty: str
    message_ko: str


class V4Verdict(TypedDict):
    """V4 verdict envelope.

    Mirrors `packages/cost_engine/protocol.py::Verdict` shape (AD-15).
    `failures` is empty when status='passed' or 'skipped'.
    """

    status: str  # V4_STATUS_PASSED / FAILED / SKIPPED
    code: str  # always 'V4' for this rule
    failures: list[V4Failure]
    verified_at: str  # ISO8601 UTC string
    product_whitelist_size: int
    skip_reason_ko: str | None  # None unless status='skipped'


# ── V4 typed exception (pure-kernel domain semantics) ─────────
class ClosingPeriodSnapshotInconsistencyError(Exception):
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


# ── verify_closing_period_consistency ────────────────────────
def verify_closing_period_consistency(
    *,
    ledger_aggregate: dict[uuid.UUID, Decimal],
    closing_snapshot_aggregate: dict[uuid.UUID, Decimal],
    product_whitelist: set[uuid.UUID],
    industry: str | None = None,
) -> V4Verdict:
    """V4 rule pure kernel — closing snapshot 일관성 verification.

    Per-product qty 일치 검증: ledger_aggregate[pid] ==
    closing_snapshot_aggregate[pid] for all pid in product_whitelist.
    Banker's rounding (ROUND_HALF_EVEN) at QTY_QUANTUM applied for
    deterministic parity (CR 0-4 lesson + AD-15 §11).

    Args:
        ledger_aggregate: dict[product_id → closing_qty] from 5-2
            `LedgerService.query_period_closing` (5-2 wire SSOT).
        closing_snapshot_aggregate: dict[product_id → closing_qty]
            from inventory_ledger event_type='closing_snapshot' aggregate
            (5-2 wire 진입점, 6-1 confirms).
        product_whitelist: set of product_ids to verify (caller filters
            active products; service layer from session).
        industry: Industry SSOT (Story 4-3 wire). 'service' → SKIP.

    Returns:
        V4Verdict TypedDict:
        - status='skipped' if industry='service' OR both aggregates empty.
        - status='passed' if all per-product qty match.
        - status='failed' if any per-product qty mismatch (failures populated).
    """
    # V4 SKIP — industry='service' (service-only tenant inventory 무의미)
    if industry == "service":
        return _v4_skipped(
            reason_ko=V4_SKIP_REASON_SERVICE_ONLY_KO,
            whitelist_size=len(product_whitelist),
        )

    # V4 SKIP — both aggregates empty (no ledger events at all)
    if not ledger_aggregate and not closing_snapshot_aggregate:
        return _v4_skipped(
            reason_ko=V4_SKIP_REASON_EMPTY_AGGREGATE_KO,
            whitelist_size=len(product_whitelist),
        )

    failures: list[V4Failure] = []
    verified_at = _iso_now_static_placeholder()

    # Per-product consistency check
    for pid in sorted(product_whitelist, key=str):
        ledger_qty = ledger_aggregate.get(pid, Decimal("0"))
        closing_qty = closing_snapshot_aggregate.get(pid, Decimal("0"))

        # Banker's rounding at QTY_QUANTUM for deterministic comparison
        ledger_q = ledger_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
        closing_q = closing_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)

        if ledger_q != closing_q:
            failures.append(
                V4Failure(
                    product_id=str(pid),
                    ledger_qty=f"{ledger_q:f}",
                    closing_snapshot_qty=f"{closing_q:f}",
                    message_ko=V4_FAIL_MESSAGE_KO,
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
    )


# ── Internal helpers ─────────────────────────────────────────
def _v4_skipped(*, reason_ko: str, whitelist_size: int) -> V4Verdict:
    """Build a SKIP V4Verdict (Korean SSOT)."""
    return V4Verdict(
        status=V4_STATUS_SKIPPED,
        code=V4_RULE_CODE,
        failures=[],
        verified_at=_iso_now_static_placeholder(),
        product_whitelist_size=whitelist_size,
        skip_reason_ko=reason_ko,
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
    "V4_ORDER_INDEX",
    "V4_RULE_CODE",
    "V4_SKIP_REASON_EMPTY_AGGREGATE_KO",
    "V4_SKIP_REASON_SERVICE_ONLY_KO",
    "V4_STATUSES",
    "V4_STATUS_FAILED",
    "V4_STATUS_PASSED",
    "V4_STATUS_SKIPPED",
    "ClosingPeriodSnapshotInconsistencyError",
    "V4Failure",
    "V4Verdict",
    "verify_closing_period_consistency",
]
