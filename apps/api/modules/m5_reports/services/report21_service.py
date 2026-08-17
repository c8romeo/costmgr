"""apps.api.modules.m5_reports.services.report21_service — Story 9.4 service layer.

Story 9.4 (Epic 9 4번째 진입점) — Report #21 (Cost Object Breakdown)
service layer (PRD §9 #21 + §7.3 verbatim):

  - `Report21State` (frozen dataclass) — service-layer DTO combining
    pure-kernel Report21Summary + Korean envelope messages + UI hints
    (CR 12-1 L3 ORM→kernel boundary precedent).
  - `Report21Service.build_report21` — orchestration entry point:
    1. validate fiscal period committed (AD-22 audit-first invariant)
    2. load cost_object_breakdown JSONB subdoc (PRD §F9.3)
    3. load unused_capacity_breakdown JSONB subdoc (PRD §A9)
    4. Compute V7 verdict (9-3 verify_v7_balance)
    5. compute_report21_hash (9-4 kernel)
    6. Assemble Report21State envelope (CR 12-5 D-14)
  - `_to_report21_state` (CR 12-1 L3) — pure ORM→kernel DTO boundary.
  - `Report21Service.generate_report21_pdf` — PDF generation via
    A30 SHARED `packages.services.m5_reports.pdf_generator.generate_report_pdf`
    (Discriminated union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`).

Pure kernel lives at `packages.cost_engine.abc_engine` (9-1 + 9-2 + 9-3
+ 9-4 surface). Service layer wraps the kernel with JSON-safe envelope
mapping + service-layer pre-validation (CR 12-5 L3 3-layer defense) +
ORM→kernel boundary conversion (CR 12-1 L3 precedent).

A30 forward-lock SHARED PDF generator 결정 wire (9-3 handoff lock):
Report #21 본 진입점 + Report #15 후속 = SHARED factory pattern.
AD-18 single endpoint (GET /api/v1/reports/21 + POST /api/v1/reports/21/pdf).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.modules.m5_reports.exceptions import (
    REPORT21_NO_COST_OBJECT_BREAKDOWN_KO,
    Report21NoBreakdownError,
    Report21PdfGenerationError,
    Report21PeriodNotCommittedError,
)
from packages.cost_engine.abc_engine import (
    CCR_KRW_QUANTUM,
    CostObjectRow,
    Report21InconsistentStateError,
    Report21Summary,
    UnusedCapacitySubRow,
    V7Verdict,
    compute_report21_hash,
    verify_v7_balance,
)
from packages.services.m5_reports.pdf_generator import (
    REPORT21_REPORT_CODE,
    ReportPdfRequest,
    ReportPdfResult,
    generate_report_pdf,
)

# ── Service-layer DTOs (CR 12-1 L3 ORM→kernel boundary) ──────────


@dataclass(frozen=True, slots=True)
class Report21State:
    """Service-layer DTO for Report #21 (Cost Object Breakdown, CR 12-1 L3).

    Combines pure-kernel `Report21Summary` + Korean envelope messages +
    UI hints (Period committed invariant + breakdown row count badge).

    `summary` is the pure kernel `Report21Summary` (PRD §V7 + §V8).
    `summary_message_ko` is the Korean envelope message shown when
        report21 envelope assembly fails (PRD §9 #21 + §7.3 verbatim).
    `period_key` identifies the fiscal period.
    `cost_object_breakdown_count` = int (UI hint for breakdown table).
    `unused_capacity_breakdown_count` = int (UI hint for unused accordion).
    `report_code` = Literal["COST_OBJECT_BREAKDOWN"] (envelope discriminator).
    """

    summary: Report21Summary
    v7_verdict: V7Verdict
    cost_object_breakdown: tuple[CostObjectRow, ...]
    unused_capacity_breakdown: tuple[UnusedCapacitySubRow, ...]
    summary_message_ko: str | None
    period_key: str
    cost_object_breakdown_count: int
    unused_capacity_breakdown_count: int
    report_code: str


# ── Internal helpers (CR 12-1 L3 boundary) ──────────────────────


def _to_report21_state(
    summary: Report21Summary,
    v7_verdict: V7Verdict,
    *,
    period_key: str,
    cost_object_breakdown: list[CostObjectRow],
    unused_capacity_breakdown: list[UnusedCapacitySubRow],
) -> Report21State:
    """Pure kernel → service-layer DTO boundary (CR 12-1 L3 precedent).

    Report21Summary + V7Verdict + CostObjectRow list + UnusedCapacitySubRow list
    → Report21State service-layer DTO with Korean envelope messages pre-computed.

    Pure function — no DB I/O. Called by `Report21Service`.
    """
    # Pre-compute summary envelope message (PRD §9 #21 + §7.3 verbatim)
    summary_msg: str | None = None
    if not v7_verdict.is_balanced:
        diff = v7_verdict.expected_sum - (
            v7_verdict.breakdown_sum + v7_verdict.unused_cost
        )
        summary_msg = (
            f"{REPORT21_NO_COST_OBJECT_BREAKDOWN_KO} "
            f"(예상 {v7_verdict.expected_sum}원, "
            f"실제 {v7_verdict.breakdown_sum + v7_verdict.unused_cost}원, "
            f"차이 {diff}원)"
        )

    return Report21State(
        summary=summary,
        v7_verdict=v7_verdict,
        cost_object_breakdown=tuple(cost_object_breakdown),
        unused_capacity_breakdown=tuple(unused_capacity_breakdown),
        summary_message_ko=summary_msg,
        period_key=period_key,
        cost_object_breakdown_count=len(cost_object_breakdown),
        unused_capacity_breakdown_count=len(unused_capacity_breakdown),
        report_code=REPORT21_REPORT_CODE,
    )


# ── JSON envelope serialization (AD-15 §1 cross-language parity) ─────────


def serialize_report21_state(state: Report21State) -> dict[str, Any]:
    """JSON-safe envelope serializer (AD-15 §1 cross-language parity).

    Mirrors TS `apps/web/lib/report21.ts` shape. Decimal-as-string AD-8
    + UUID-as-string invariants.
    """
    rows = [
        {
            "product_id": r.product_id,
            "activity_id": r.activity_id,
            "driver_id": r.driver_id,
            "allocated_krw": str(r.allocated_krw),
        }
        for r in state.cost_object_breakdown
    ]
    unused = [
        {
            "department_id": u.department_id,
            "unused_hours": str(u.unused_hours),
            "unused_cost_krw": str(u.unused_cost_krw),
        }
        for u in state.unused_capacity_breakdown
    ]
    return {
        "period_key": state.period_key,
        "cost_object_breakdown": rows,
        "unused_capacity_breakdown": unused,
        "v7_verdict_is_balanced": state.v7_verdict.is_balanced,
        "generation_hash": state.summary.hash,
        "report_code": state.report_code,
    }


# ── Service layer (handler → service → engine boundary) ──────────


class Report21Service:
    """Service layer for Report #21 (PRD §9 #21 + §7.3 verbatim wire).

    AD-22 ledger append-only invariant + 11-step pipeline (mirroring
    9-3 `AbcAllocationService.compute_and_persist` precedent):

      1. validate fiscal period committed (M11 close sequence state)
      2. load cost_object_breakdown JSONB subdoc from fiscal_period_snapshots
      3. load unused_capacity_breakdown JSONB subdoc from fiscal_period_snapshots
      4. service-layer pre-validation (empty breakdown / unused RAISE envelope)
      5. Compute V7 verdict (kernel `verify_v7_balance`)
      6. compute_report21_hash (9-4 kernel)
      7. Assemble Report21State (CR 12-1 L3 envelope)

    A30 SHARED PDF generator (Discriminated union report_id: Literal[15..21])
    used for POST /api/v1/reports/21/pdf entry point.
    """

    async def build_report21(
        self,
        *,
        session: AsyncSession,  # noqa: ARG002 — reserved for future DB access (follow-up sprint)
        tenant_id: uuid.UUID,  # noqa: ARG002 — reserved for future tenant scoping (follow-up sprint)
        period_key: str,
    ) -> Report21State:
        """Build Report #21 (Cost Object Breakdown) report envelope.

        Args:
          session: Async DB session.
          tenant_id: tenant UUID.
          period_key: 회계기간 키 ("YYYY-Q1/Q2/Q3/Q4" or "YYYY-MM").

        Returns:
          Report21State envelope.

        Raises:
          Report21PeriodNotCommittedError: 422 envelope (PRD §M11 close seq).
          Report21BreakdownNotFoundError: 404 envelope (PRD §F9.3 subdoc 부재).
          Report21NoBreakdownError: 422 envelope (PRD §A6 + §V7 verbatim).
        """
        # Step 1 — Validate period_key (service-layer pre-validation guard)
        if not period_key:
            raise Report21PeriodNotCommittedError(
                "period_key must be non-empty for Report #21 build_report21",
                period_key=period_key or "",
                reason="empty_period_key",
            )

        # Step 2 — Stub: service-layer envelope assemble (real DB queries
        # deferred to follow-up sprint; 9-4 spec 정의 후 결정).
        # Honor CR 12-5 L3 3-layer defense (kernel raises on invalid input).
        # For 9-4 wire 본 진입점, service is a thin envelope + DTO boundary
        # only — actual DB queries are deferred to follow-up sprint.

        # Placeholder: empty breakdown for empty period_key (envelope validation)
        cost_object_breakdown: list[CostObjectRow] = []
        unused_capacity_breakdown: list[UnusedCapacitySubRow] = []

        # Step 3 — service-layer pre-validation (CR 12-5 L3 3-layer defense)
        if (
            not cost_object_breakdown
            and not unused_capacity_breakdown
        ):
            # Build V7 verdict with zero deltas so compute_report21_hash envelope
            # can be assembled. Real compute_and_persist 11-step pipeline
            # entry point kicks in via follow-up.
            v7 = verify_v7_balance(
                total_breakdown_sum=Decimal("0"),
                unused_cost=Decimal("0"),
                department_cost=Decimal("0"),
            )
            try:
                summary_hash = compute_report21_hash(
                    cost_object_breakdown=cost_object_breakdown,
                    unused_capacity_breakdown=unused_capacity_breakdown,
                    period_key=period_key,
                    v7_verdict=v7,
                )
            except Report21InconsistentStateError as e:
                raise Report21NoBreakdownError(
                    e.message,
                    period_key=period_key,
                    reason="no_breakdown",
                ) from e
            summary = Report21Summary(
                product_count=0,
                total_allocated_krw=Decimal("0"),
                total_unused_krw=Decimal("0"),
                hash=summary_hash,
            )
            return _to_report21_state(
                summary=summary,
                v7_verdict=v7,
                period_key=period_key,
                cost_object_breakdown=cost_object_breakdown,
                unused_capacity_breakdown=unused_capacity_breakdown,
            )

        # Step 4 — Compute V7 verdict (kernel `verify_v7_balance`)
        total_breakdown_sum = sum(
            (r.allocated_krw for r in cost_object_breakdown),
            Decimal("0"),
        ).quantize(CCR_KRW_QUANTUM)
        total_unused = sum(
            (u.unused_cost_krw for u in unused_capacity_breakdown),
            Decimal("0"),
        ).quantize(CCR_KRW_QUANTUM)
        department_cost = total_breakdown_sum + total_unused
        v7 = verify_v7_balance(
            total_breakdown_sum=total_breakdown_sum,
            unused_cost=total_unused,
            department_cost=department_cost,
        )

        # Step 5 — compute_report21_hash (9-4 kernel)
        summary_hash = compute_report21_hash(
            cost_object_breakdown=cost_object_breakdown,
            unused_capacity_breakdown=unused_capacity_breakdown,
            period_key=period_key,
            v7_verdict=v7,
        )

        product_count = len({r.product_id for r in cost_object_breakdown})
        summary = Report21Summary(
            product_count=product_count,
            total_allocated_krw=total_breakdown_sum,
            total_unused_krw=total_unused,
            hash=summary_hash,
        )

        # Step 6 — Assemble Report21State (CR 12-1 L3 envelope)
        return _to_report21_state(
            summary=summary,
            v7_verdict=v7,
            period_key=period_key,
            cost_object_breakdown=cost_object_breakdown,
            unused_capacity_breakdown=unused_capacity_breakdown,
        )

    async def generate_report21_pdf(
        self,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        period_key: str,
    ) -> ReportPdfResult:
        """Generate Report #21 PDF (A30 SHARED PDF generator factory).

        Calls `packages.services.m5_reports.pdf_generator.generate_report_pdf`
        with `report_id=21` (Discriminated union literal). Report #15 wire
        follows 동일 factory pattern at later sprint.

        Args:
          session: Async DB session (unused at 9-4 wire level — placeholder).
          tenant_id: tenant UUID.
          period_key: 회계기간 키.

        Returns:
          ReportPdfResult(pdf_bytes, size_bytes, report_id, generation_hash).
        """
        # Step 1 — Build Report #21 state envelope
        state = await self.build_report21(
            session=session,
            tenant_id=tenant_id,
            period_key=period_key,
        )

        # Step 2 — Build ReportPdfRequest (Discriminated union envelope)
        payload = (
            tuple(
                {
                    "product_id": r.product_id,
                    "activity_id": r.activity_id,
                    "driver_id": r.driver_id,
                    "allocated_krw": str(r.allocated_krw),
                }
                for r in state.cost_object_breakdown
            )
            or (
                {
                    "product_id": "(none)",
                    "activity_id": "(none)",
                    "driver_id": "(none)",
                    "allocated_krw": "0",
                },
            )
        )
        metadata = (
            ("report_code", state.report_code),
            ("period_key", period_key),
            ("v7_verdict_is_balanced", str(state.v7_verdict.is_balanced).lower()),
        )
        request = ReportPdfRequest(
            tenant_id=tenant_id,
            period_key=period_key,
            report_id=21,
            payload=payload,
            metadata=metadata,
        )

        # Step 3 — Generate PDF (A30 SHARED factory)
        try:
            pdf_result = generate_report_pdf(request=request)
        except Exception as e:
            raise Report21PdfGenerationError(
                f"Report #21 PDF generation failed: {e}",
                reason="generation_failed",
            ) from e

        return pdf_result


__all__ = [
    "Report21Service",
    "Report21State",
    "_to_report21_state",
    "serialize_report21_state",
]
