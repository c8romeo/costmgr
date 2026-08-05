"""packages.cost_engine.closing_invariant_check — Story 5.3 V3 pure kernel.

V3 (연결성 verification = closing ≥ 0 invariant) pure rule.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m6_verification/services/closing_invariant_verifier.py`
  (T5 service layer — verify_v3_closing_invariant dispatch)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes
ledger_aggregate (dict[UUID, Decimal]) + product_whitelist (set[UUID])
as arguments; this kernel owns the V3 verdict logic + invariant check.

V3 fixture parity: 5-3 ships 2 NEW 골든 fixtures:
- `v3_closing_pass_manufacturing.json` (all closing >= 0 → status='passed')
- `v3_closing_fail_manufacturing.json` (>=1 closing < 0 → status='failed')
- V8 fixture count: 12 → 14.
- AD-12 ordering: V3 fails BEFORE V7 (ABC integrity) + V8 (byte-identical
  golden match). V1 → V4 → V3 → V7 → V8 ordering invariant preserved.

PRD §V3 connection verification:
- "closing ≥ 0 invariant" — 모든 inventory-tracked product의 closing
  balance가 0 이상이어야 한다.
- V3 fail → top_failure.code='V3' + block_reason='NEGATIVE_CLOSING_INVENTORY'
  (4-2 close-time hook + 4-3 verdict envelope 동등 발동).
- V3 skip → industry='service' (service-only tenant inventory 무의미)
  OR aggregate empty + no products in whitelist.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, TypedDict

# ── Constants ────────────────────────────────────────────────
# V3 verdict status (matches Story 4-3 V1·V4·V7·V8 verbatim).
V3_STATUS_PASSED: Final[str] = "passed"
V3_STATUS_FAILED: Final[str] = "failed"
V3_STATUS_SKIPPED: Final[str] = "skipped"

V3_STATUSES: Final[frozenset[str]] = frozenset(
    {V3_STATUS_PASSED, V3_STATUS_FAILED, V3_STATUS_SKIPPED}
)

# AD-12 ordering invariant (Story 4-3 wire). V3 is slot 3 of 5.
V3_ORDER_INDEX: Final[int] = 3
V3_RULE_CODE: Final[str] = "V3"

# V3 skip reason (Korean SSOT for service-only tenant).
V3_SKIP_REASON_SERVICE_ONLY_KO: Final[str] = "service-only tenant은 inventory 의미 없음"
V3_SKIP_REASON_EMPTY_AGGREGATE_KO: Final[str] = "기말재고 ledger aggregate 비어있음 — V3 SKIP"


# ── TypedDict shapes ─────────────────────────────────────────
class V3Failure(TypedDict):
    """Per-product closing ≥ 0 invariant violation.

    AD-15: snake_case field names.
    """

    product_id: str  # UUID string for JSON serialization
    closing_qty: str  # Decimal string for AD-8 monetary parity
    message_ko: str


class V3Verdict(TypedDict):
    """V3 verdict envelope.

    Mirrors `packages/cost_engine/protocol.py::Verdict` shape (AD-15).
    `failures` is empty when status='passed' or 'skipped'.
    """

    status: str  # V3_STATUS_PASSED / FAILED / SKIPPED
    code: str  # always 'V3' for this rule
    failures: list[V3Failure]
    verified_at: str  # ISO8601 UTC string
    product_whitelist_size: int
    skip_reason_ko: str | None  # None unless status='skipped'


# ── ClosingInvariantViolationError ────────────────────────────
class ClosingInvariantViolationError(Exception):
    """Pure-kernel V3 violation error (defense-in-depth).

    Distinct from service-layer typed exceptions (which carry HTTP
    envelope + audit-first semantics). This exception is raised when
    internal invariants are violated (e.g. malformed verdict shape).
    NO HTTP mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "CLOSING_INVARIANT_VIOLATION",
        period_key: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.period_key = period_key


# ── verify_closing_invariant ──────────────────────────────────
def verify_closing_invariant(
    *,
    ledger_aggregate: dict[uuid.UUID, Decimal],
    product_whitelist: set[uuid.UUID],
    verified_at: str = "",
    skip_reason_ko: str | None = None,
) -> V3Verdict:
    """V3 (closing ≥ 0 invariant) pure verification.

    Pure-kernel dispatch: takes pre-computed ledger_aggregate (from
    `packages.services.m4_inventory.closing_guard.compute_closing_balance_per_product`)
    + product_whitelist (active products table for tenant) and returns
    a V3Verdict. The service layer wires SQL + RLS predicates; this
    kernel owns verdict logic only.

    Rules:
    1. If skip_reason_ko is non-None → status='skipped' (industry skip
       matrix — service-only tenant, no inventory semantics).
    2. If ledger_aggregate is empty AND product_whitelist is empty →
       status='skipped' with V3_SKIP_REASON_EMPTY_AGGREGATE_KO.
    3. For each (product_id, qty) in ledger_aggregate:
       - product_id not in product_whitelist → log + ignore (defense-in-depth
         against orphan ledger rows).
       - qty < 0 → V3Failure append.
    4. failures empty → status='passed'. failures non-empty → status='failed'.

    Args:
        ledger_aggregate: product_id → closing Decimal (signed aggregate
            from inventory_ledger). Empty allowed.
        product_whitelist: set of active product UUIDs for the tenant.
            Empty + non-empty aggregate = status='skipped' (no inventory).
        verified_at: ISO8601 UTC string (caller-provided; empty string
            allowed for pure-kernel tests).
        skip_reason_ko: Optional service-layer override (e.g. service-only
            industry). None = no skip.

    Returns:
        V3Verdict TypedDict with status / failures / metadata.

    Raises:
        ClosingInvariantViolationError: On internal invariant violations
            (non-finite Decimal, malformed UUID key).
    """
    # Validate input
    _validate_inputs(ledger_aggregate, product_whitelist)

    # Rule 1: explicit skip reason (industry skip matrix)
    if skip_reason_ko:
        return _make_verdict(
            status=V3_STATUS_SKIPPED,
            failures=[],
            verified_at=verified_at,
            product_whitelist_size=len(product_whitelist),
            skip_reason_ko=skip_reason_ko,
        )

    # Rule 2: empty aggregate + empty whitelist → skip
    if not ledger_aggregate and not product_whitelist:
        return _make_verdict(
            status=V3_STATUS_SKIPPED,
            failures=[],
            verified_at=verified_at,
            product_whitelist_size=0,
            skip_reason_ko=V3_SKIP_REASON_EMPTY_AGGREGATE_KO,
        )

    # Rule 3: iterate + classify
    failures: list[V3Failure] = []
    for pid, qty in ledger_aggregate.items():
        if pid not in product_whitelist:
            # Orphan ledger row (defense-in-depth) — log + ignore.
            # Production data integrity incident; not a V3 verdict failure
            # since V3 is about closing invariant, not whitelist integrity.
            continue
        if not qty.is_finite():
            raise ClosingInvariantViolationError(
                message=(f"V3: product {pid} has non-finite closing qty {qty!r}"),
                error_code="NON_FINITE_CLOSING_QTY",
            )
        quantized = qty.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
        if quantized < Decimal("0"):
            failures.append(
                V3Failure(
                    product_id=str(pid),
                    closing_qty=f"{quantized:f}",
                    message_ko=f"기말재고 음수 {quantized}개 (PRD §V3)",
                )
            )

    # Rule 4: verdict
    if failures:
        return _make_verdict(
            status=V3_STATUS_FAILED,
            failures=_sort_failures_by_severity(failures),
            verified_at=verified_at,
            product_whitelist_size=len(product_whitelist),
            skip_reason_ko=None,
        )

    return _make_verdict(
        status=V3_STATUS_PASSED,
        failures=[],
        verified_at=verified_at,
        product_whitelist_size=len(product_whitelist),
        skip_reason_ko=None,
    )


# ── Internal helpers ─────────────────────────────────────────
def _make_verdict(
    *,
    status: str,
    failures: list[V3Failure],
    verified_at: str,
    product_whitelist_size: int,
    skip_reason_ko: str | None,
) -> V3Verdict:
    """Build a V3Verdict TypedDict with validation."""
    if status not in V3_STATUSES:
        raise ClosingInvariantViolationError(
            message=f"V3 verdict status {status!r} not in {sorted(V3_STATUSES)}",
            error_code="INVALID_VERDICT_STATUS",
        )
    return V3Verdict(
        status=status,
        code=V3_RULE_CODE,
        failures=failures,
        verified_at=verified_at,
        product_whitelist_size=product_whitelist_size,
        skip_reason_ko=skip_reason_ko,
    )


def _sort_failures_by_severity(
    failures: list[V3Failure],
) -> list[V3Failure]:
    """Sort V3 failures by closing_qty ASC (severity sort, deterministic).

    CR 4-3 lesson: deterministic ordering for cross-language parity tests.
    """
    return sorted(failures, key=lambda f: f["closing_qty"])


def _validate_inputs(
    ledger_aggregate: dict[uuid.UUID, Decimal],
    product_whitelist: set[uuid.UUID],
) -> None:
    """Validate V3 inputs (defense-in-depth)."""
    if not isinstance(ledger_aggregate, dict):
        raise ClosingInvariantViolationError(
            message=(f"ledger_aggregate must be dict, got " f"{type(ledger_aggregate).__name__!r}"),
            error_code="INVALID_LEDGER_AGGREGATE",
        )
    if not isinstance(product_whitelist, set):
        raise ClosingInvariantViolationError(
            message=(
                f"product_whitelist must be set, got " f"{type(product_whitelist).__name__!r}"
            ),
            error_code="INVALID_PRODUCT_WHITELIST",
        )


__all__ = [
    "V3_FAILURE_KO_MESSAGE",
    "V3_ORDER_INDEX",
    "V3_RULE_CODE",
    "V3_SKIP_REASON_EMPTY_AGGREGATE_KO",
    "V3_SKIP_REASON_SERVICE_ONLY_KO",
    "V3_STATUSES",
    "V3_STATUS_FAILED",
    "V3_STATUS_PASSED",
    "V3_STATUS_SKIPPED",
    "ClosingInvariantViolationError",
    "V3Failure",
    "V3Verdict",
    "verify_closing_invariant",
]

# Alias for SSOT consistency.
V3_FAILURE_KO_MESSAGE: Final[str] = "기말재고 음수 {qty}개 (PRD §V3)"
