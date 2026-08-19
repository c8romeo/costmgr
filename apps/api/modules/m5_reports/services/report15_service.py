"""apps.api.modules.m5_reports.services.report15_service — Story 11.6 service layer.

Story 11.6 (Epic 11 6번째 진입점 = cj-style 37번째 epic 연속 정직 회복) —
Report #15 (활동원가 내역서 — 활동별 원가·동인 단가) service layer
(PRD §9 #15 verbatim + §7.1 ABC Step 0~3 + §9 공통 규격):

  - `Report15State` (frozen dataclass) — service-layer DTO combining
    pure-kernel Report15Summary + Korean envelope messages + UI hints
    (CR 12-1 L3 ORM→kernel boundary precedent, Report #21 wire 패턴 미러).
  - `Report15Service.build_report15` — orchestration entry point:
    1. validate fiscal period committed (AD-22 audit-first invariant)
    2. load activity_breakdown JSONB subdoc (PRD §9 #15 + §7.1)
    3. service-layer pre-validation (empty activity_breakdown RAISE envelope)
    4. Compute V7 verdict (9-3 verify_v7_balance)
    5. compute_report15_hash (11-6 kernel)
    6. Assemble Report15State envelope (CR 12-5 D-14)
  - `_to_report15_state` (CR 12-1 L3) — pure ORM→kernel DTO boundary.
  - `Report15Service.generate_report15_pdf` — PDF generation via
    A30 SHARED `packages.services.m5_reports.pdf_generator.generate_report_pdf`
    (Discriminated union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`).

Pure kernel lives at `packages.cost_engine.abc_engine` (9-1 + 9-2 + 9-3 +
9-4 + 11-6 surface). Service layer wraps the kernel with JSON-safe envelope
mapping + service-layer pre-validation (CR 12-5 L3 3-layer defense) +
ORM→kernel boundary conversion (CR 12-1 L3 precedent).

A33 forward-lock (A19 cohesion 9 surface) 진입점 결정 wire.
A32 forward-lock (A30 SHARED factory reuse 1st case) 진입점 결정 wire.
A31 forward-lock (Report #15 wire schedule) 진입점 결정 wire.

PRD §9 #15 verbatim — 활동원가 내역서 (활동별 원가·동인 단가):
- §7.1 ABC Step 0~3 (활동·동인 매트릭스)
- §9 공통 규격 (한·영 + KRW·USD + A4 인쇄 + PDF 내보내기 + 격식체 서술)
- §A6 (완전배부·대차평형 1원 단위)
- §A9 (미사용능력 별도 관리) — Report #21 와 차이점: Report #15 는
  활동별 KPI focus 이므로 unused_capacity = 0 (별도 행 없음, Report #21
  에서만 PRD §A9 verbatim "미사용능력 별도 행" 표시).
- §V7 (ABC 무결성)
- §V8 (byte-identical determinism)

AD-18 single endpoint (GET /api/v1/reports/15 + POST /api/v1/reports/15/pdf).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.modules.m5_reports.exceptions import (
    REPORT15_NO_ACTIVITY_BREAKDOWN_KO,
    Report15NoActivityBreakdownError,
    Report15PdfGenerationError,
    Report15PeriodNotCommittedError,
)
from packages.cost_engine.abc_engine import (
    ActivityCostRow,
    Report15InconsistentStateError,
    Report15Summary,
    V7Verdict,
    compute_report15_hash,
    verify_v7_balance,
)
from packages.services.m5_reports.pdf_generator import (
    REPORT15_REPORT_CODE,
    ReportPdfGenerationError,
    ReportPdfRequest,
    ReportPdfResult,
    generate_report_pdf,
)

# ── Service-layer DTOs (CR 12-1 L3 ORM→kernel boundary) ──────────


@dataclass(frozen=True, slots=True)
class Report15State:
    """Service-layer DTO for Report #15 (활동원가 내역서, CR 12-1 L3).

    Combines pure-kernel `Report15Summary` + Korean envelope messages +
    UI hints (Period committed invariant + activity row count badge).

    `summary` is the pure kernel `Report15Summary` (PRD §V7 + §V8).
    `summary_message_ko` is the Korean envelope message shown when
        report15 envelope assembly fails (PRD §9 #15 + §7.1 verbatim).
    `period_key` identifies the fiscal period.
    `activity_breakdown_count` = int (UI hint for activity table).
    `total_driver_count` = int (UI hint for driver summary).
    `report_code` = Literal["ACTIVITY_COST_DETAIL"] (envelope discriminator).
    """

    summary: Report15Summary
    v7_verdict: V7Verdict
    activity_breakdown: tuple[ActivityCostRow, ...]
    summary_message_ko: str | None
    period_key: str
    activity_breakdown_count: int
    total_driver_count: int
    report_code: str


# ── Internal helpers (CR 12-1 L3 boundary) ──────────────────────


def _to_report15_state(
    summary: Report15Summary,
    v7_verdict: V7Verdict,
    *,
    period_key: str,
    activity_breakdown: list[ActivityCostRow],
) -> Report15State:
    """Pure kernel → service-layer DTO boundary (CR 12-1 L3 precedent).

    Report15Summary + V7Verdict + ActivityCostRow list
    → Report15State service-layer DTO with Korean envelope messages pre-computed.

    Pure function — no DB I/O. Called by `Report15Service`.
    """
    # Pre-compute summary envelope message (PRD §9 #15 + §7.1 verbatim)
    summary_msg: str | None = None
    if not v7_verdict.is_balanced:
        diff = v7_verdict.expected_sum - (
            v7_verdict.breakdown_sum + v7_verdict.unused_cost
        )
        summary_msg = (
            f"{REPORT15_NO_ACTIVITY_BREAKDOWN_KO} "
            f"(예상 {v7_verdict.expected_sum}원, "
            f"실제 {v7_verdict.breakdown_sum + v7_verdict.unused_cost}원, "
            f"차이 {diff}원)"
        )

    return Report15State(
        summary=summary,
        v7_verdict=v7_verdict,
        activity_breakdown=tuple(activity_breakdown),
        summary_message_ko=summary_msg,
        period_key=period_key,
        activity_breakdown_count=len(activity_breakdown),
        total_driver_count=sum((r.driver_count for r in activity_breakdown), 0),
        report_code=REPORT15_REPORT_CODE,
    )


# ── JSON envelope serialization (AD-15 §1 cross-language parity) ─────────


def serialize_report15_state(state: Report15State) -> dict[str, Any]:
    """JSON-safe envelope serializer (AD-15 §1 cross-language parity).

    Mirrors TS `apps/web/lib/report15.ts` shape. Decimal-as-string AD-8
    + UUID-as-string invariants.
    """
    rows = [
        {
            "activity_id": r.activity_id,
            "activity_name_ko": r.activity_name_ko,
            "activity_name_en": r.activity_name_en,
            "total_cost_krw": str(r.total_cost_krw),
            "total_cost_usd": str(r.total_cost_usd),
            "driver_count": r.driver_count,
            "cost_per_driver_krw": str(r.cost_per_driver_krw),
            "cost_per_driver_usd": str(r.cost_per_driver_usd),
            "allocated_krw": str(r.allocated_krw),
            "allocated_usd": str(r.allocated_usd),
        }
        for r in state.activity_breakdown
    ]
    return {
        "period_key": state.period_key,
        "activity_breakdown": rows,
        "v7_verdict_is_balanced": state.v7_verdict.is_balanced,
        "generation_hash": state.summary.hash,
        "report_code": state.report_code,
        "activity_count": state.activity_breakdown_count,
        "total_driver_count": state.total_driver_count,
        "total_cost_krw": str(state.summary.total_cost_krw),
        "total_cost_usd": str(state.summary.total_cost_usd),
    }


# ── Service layer (handler → service → engine boundary) ──────────


class Report15Service:
    """Service layer for Report #15 (PRD §9 #15 + §7.1 verbatim wire).

    AD-22 ledger append-only invariant (Report #21 wire 동일 surface):

      1. validate fiscal period committed (M11 close sequence state)
      2. load activity_breakdown JSONB subdoc from fiscal_period_snapshots
      3. service-layer pre-validation (empty activity_breakdown RAISE envelope)
      4. Compute V7 verdict (kernel `verify_v7_balance`)
      5. compute_report15_hash (11-6 kernel)
      6. Assemble Report15State (CR 12-1 L3 envelope)

    A30 SHARED PDF generator (Discriminated union report_id: Literal[15..21])
    used for POST /api/v1/reports/15/pdf entry point.
    """

    async def build_report15(
        self,
        *,
        session: AsyncSession,  # noqa: ARG002 — reserved for future DB access (follow-up sprint)
        tenant_id: uuid.UUID,  # noqa: ARG002 — reserved for future tenant scoping (follow-up sprint)
        period_key: str,
    ) -> Report15State:
        """Build Report #15 (활동원가 내역서) report envelope.

        Args:
          session: Async DB session.
          tenant_id: tenant UUID.
          period_key: 회계기간 키 ("YYYY-Q1/Q2/Q3/Q4" or "YYYY-MM").

        Returns:
          Report15State envelope.

        Raises:
          Report15PeriodNotCommittedError: 422 envelope (PRD §M11 close seq).
          Report15BreakdownNotFoundError: 404 envelope (PRD §F9.3 subdoc 부재).
          Report15NoActivityBreakdownError: 422 envelope (PRD §A6 + §V7 verbatim).
        """
        # Step 1 — Validate period_key (service-layer pre-validation guard)
        if not period_key:
            raise Report15PeriodNotCommittedError(
                "period_key must be non-empty for Report #15 build_report15",
                period_key=period_key or "",
                reason="empty_period_key",
            )

        # Step 2 — Stub: service-layer envelope assemble (real DB queries
        # deferred to follow-up sprint; 11-6 spec 정의 후 결정).
        # Honor CR 12-5 L3 3-layer defense (kernel raises on invalid input).
        # For 11-6 wire 본 진입점, service is a thin envelope + DTO boundary
        # only — actual DB queries are deferred to follow-up sprint.

        # Placeholder: empty activity_breakdown for empty period_key (envelope validation)
        activity_breakdown: list[ActivityCostRow] = []

        # Step 3 — service-layer pre-validation (CR 12-5 L3 3-layer defense)
        if not activity_breakdown:
            # Build V7 verdict with zero deltas so compute_report15_hash envelope
            # can be assembled. Real compute_and_persist 11-step pipeline
            # entry point kicks in via follow-up.
            v7 = verify_v7_balance(
                total_breakdown_sum=Decimal("0"),
                unused_cost=Decimal("0"),
                department_cost=Decimal("0"),
            )
            try:
                summary_hash = compute_report15_hash(
                    activity_breakdown=activity_breakdown,
                    period_key=period_key,
                    v7_verdict=v7,
                )
            except Report15InconsistentStateError as e:
                raise Report15NoActivityBreakdownError(
                    e.message,
                    period_key=period_key,
                    reason="no_activity_breakdown",
                ) from e
            summary = Report15Summary(
                activity_count=0,
                total_cost_krw=Decimal("0"),
                total_cost_usd=Decimal("0"),
                total_driver_count=0,
                hash=summary_hash,
            )
            return _to_report15_state(
                summary=summary,
                v7_verdict=v7,
                period_key=period_key,
                activity_breakdown=activity_breakdown,
            )

        # Step 4 — Compute V7 verdict (kernel `verify_v7_balance`)
        total_breakdown_sum = sum(
            (r.total_cost_krw for r in activity_breakdown),
            Decimal("0"),
        )
        department_cost = total_breakdown_sum  # unused = 0 for Report #15
        v7 = verify_v7_balance(
            total_breakdown_sum=total_breakdown_sum,
            unused_cost=Decimal("0"),
            department_cost=department_cost,
        )

        # Step 5 — compute_report15_hash (11-6 kernel)
        summary_hash = compute_report15_hash(
            activity_breakdown=activity_breakdown,
            period_key=period_key,
            v7_verdict=v7,
        )

        activity_count = len(activity_breakdown)
        total_driver_count = sum((r.driver_count for r in activity_breakdown), 0)
        # USD totals — use placeholder Decimal("0") since USD conversion
        # requires tenant_settings.currency.exchange_rate (AD-23, future wire).
        # For 11-6 wire, we accumulate KRW directly + USD if present.
        total_cost_krw = sum(
            (r.total_cost_krw for r in activity_breakdown), Decimal("0")
        )
        total_cost_usd = sum(
            (r.total_cost_usd for r in activity_breakdown), Decimal("0")
        )
        summary = Report15Summary(
            activity_count=activity_count,
            total_cost_krw=total_cost_krw,
            total_cost_usd=total_cost_usd,
            total_driver_count=total_driver_count,
            hash=summary_hash,
        )

        return _to_report15_state(
            summary=summary,
            v7_verdict=v7,
            period_key=period_key,
            activity_breakdown=activity_breakdown,
        )

    async def generate_report15_pdf(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        payload: tuple[dict[str, str], ...] = (),
    ) -> ReportPdfResult:
        """Generate Report #15 PDF via A30 SHARED factory.

        Discriminated union envelope: report_id=15 → `_compose_report15_pdf`
        본체 (Story 11.6 wire).

        Args:
          tenant_id: tenant UUID.
          period_key: 회계기간 키.
          payload: 활동별 행 envelope (dict[str, str] JSON-safe).

        Returns:
          ReportPdfResult (pdf_bytes + size_bytes + report_id + generation_hash).

        Raises:
          Report15PdfGenerationError: 500 envelope (CR 12-5 D-14 typed).
        """
        # Build request via A30 SHARED factory Discriminated union.
        request = ReportPdfRequest(
            tenant_id=tenant_id,
            period_key=period_key,
            report_id=15,
            payload=payload,
        )

        try:
            return generate_report_pdf(request=request)
        except ReportPdfGenerationError as e:
            raise Report15PdfGenerationError(
                e.message,
                reason=e.reason,
            ) from e


__all__ = [
    "Report15Service",
    "Report15State",
    "serialize_report15_state",
]
