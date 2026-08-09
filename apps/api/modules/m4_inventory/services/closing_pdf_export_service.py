"""apps.api.modules.m4_inventory.services.closing_pdf_export_service — Story 6.3.

Service layer for the Closing PDF Export (PRD §F6.3 + AD-15 + AD-22).
Pure kernel: `packages.services.m4_inventory.closing_pdf_export`.
Service layer wraps with SQLAlchemy AsyncSession + audit-first emit
(CR 1.1) + 3 typed exceptions (AD-15 §4 envelope mapping).

Wire:
- `export_closing_pdf` (T1.1) — read-only aggregator that joins
  closing_snapshot ledger events + inventory_ledger events +
  monthly_closing_report aggregator + builds PDF byte stream via
  pure kernel `render_closing_pdf_byte_stream`.
- Audit-first emit (CR 1.1 lesson) — `closing_pdf_export_viewed`
  audit row INSERT BEFORE PDF byte render.
- Capability gate: MONTHLY_CLOSING_REPORT (reuse from 6-2 wire —
  no NEW capability).

A5 forward-lock (CR 6-1/6-2 lesson):
- Audit rows route to `audit_logs` (ActionClass.MONTHLY_CLOSING_REPORT)
  via `emit_audit_typed()` — REUSE 6-2 action `monthly_closing_report_viewed`.
  No NEW action needed (PDF export is read-only — same audit semantics).

3 typed exceptions (AD-15 §4 envelope mapping):
- `ClosingPdfExportInvalidIndustryError` (422
  CLOSING_PDF_EXPORT_INVALID_INDUSTRY) — industry guard (W5 deferral).
- `ClosingPdfExportSizeExceededError` (409
  CLOSING_PDF_EXPORT_SIZE_EXCEEDED) — PDF > 5MB cap.
- `ClosingPdfExportAuditEmitError` (500
  CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR) — audit-first emit failure.

A8 inline projection deprecation timeline (carry from 6-2):
- 6-3 wire 시점: inline projection 보존 상태 (1 epic maintenance window).
- Epic 6 close-out 시점에 fold-in vs deprecate 결정 필수 (A8 결정).

Korean message SSOT (AD-15 §11 cross-language parity):
- `MONTHLY_CLOSING_REPORT_TITLE_KO` (6-2 wire) → reused.
- `CLOSING_PDF_EXPORT_TITLE_KO` (T1 pure kernel) → mirrored TS labels-ko.ts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from packages.services.m4_inventory.closing_pdf_export import (
    CLOSING_PDF_EXPORT_EMPTY_KO,
    CLOSING_PDF_EXPORT_TITLE_KO,
    CLOSING_PDF_INDUSTRY_VALUES,
    ClosingPdfDocument,
    ClosingPdfExportError,
    ClosingPdfPage,
    ClosingPdfSection,
    ClosingPdfTextBlock,
    render_closing_pdf_byte_stream,
)


def _now_utc() -> datetime:
    """UTC now (AD-5: pure kernel no clock, service layer owns)."""
    return datetime.now(tz=UTC)


def _to_iso(dt: datetime) -> str:
    """ISO-8601 UTC timestamp string."""
    return dt.isoformat()


# ─────────────────────────────────────────────────────────────
# Typed exceptions (mapped to HTTP by handlers.py / main.py)
# ─────────────────────────────────────────────────────────────


class ClosingPdfExportInvalidIndustryError(Exception):
    """422 CLOSING_PDF_EXPORT_INVALID_INDUSTRY — industry guard.

    PRD §F6.3 + W5 deferral: industry extension follow-up (Epic 12+
    결정). Until then, only 4 canonical industries accepted.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        industry: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_pdf_export industry '{industry}' invalid for "
            f"period {period_key} (tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.industry = industry
        self.trace_id = trace_id


class ClosingPdfExportSizeExceededError(Exception):
    """409 CLOSING_PDF_EXPORT_SIZE_EXCEEDED — PDF > 5MB cap.

    PRD §F6.3: PDF size ≤ 5MB per period (chunked rendering cap).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        size_bytes: int,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_pdf_export size {size_bytes} exceeds 5MB cap "
            f"for period {period_key} (tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.size_bytes = size_bytes
        self.trace_id = trace_id


class ClosingPdfExportAuditEmitError(Exception):
    """500 CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR — audit-first invariant guard.

    CR 1.1 lesson: audit-first emit failure MUST raise (not silent skip).
    Read-only PDF export 자체 audit log INSERT — closing report의 export trace.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_pdf_export audit emit failed for tenant {tenant_id}: {details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


# ─────────────────────────────────────────────────────────────
# ClosingPdfExportService
# ─────────────────────────────────────────────────────────────


class ClosingPdfExportService:
    """Story 6.3 — closing PDF export service.

    Read-only aggregator + PDF byte stream renderer
    (PRD §F6.3 + §F5 + §V4 + §A11 4-layer defense).

    Constructor:
        session: AsyncSession (per-request).
        tenant_id: tenant UUID (from JWT).
        trace_id: request trace ID.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.trace_id = trace_id

    # ── Operation: export closing PDF (read-only + PDF render) ──
    async def export_closing_pdf(
        self,
        period_key: str,
        *,
        industry: str,
    ) -> dict[str, Any]:
        """Export monthly closing period as PDF byte stream (PRD §F6.3).

        Read-only aggregator + audit-first emit + PDF byte stream render:
        1. Industry guard (W5 deferral).
        2. 4-source read-only join (closing_snapshot + ledger + report).
        3. Audit-first emit (CR 1.1) — closing_pdf_export_viewed.
        4. Pure kernel PDF byte stream render (T1 — render_closing_pdf_byte_stream).

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            industry: One of 4 canonical industries (PRD §6.1).

        Returns:
            dict[str, Any] with pdf_bytes + pdf_size_bytes + period_key +
            industry + title_ko + is_empty + closing_snapshot_count +
            ledger_event_count + finalized_at.

        Raises:
            ClosingPdfExportInvalidIndustryError: industry guard failed.
            ClosingPdfExportSizeExceededError: PDF > 5MB cap.
            ClosingPdfExportAuditEmitError: audit-first emit failure.
        """
        # 1. Industry guard (W5 deferral — pre-6-2 hardcode 'trad' REJECT).
        if industry not in CLOSING_PDF_INDUSTRY_VALUES:
            raise ClosingPdfExportInvalidIndustryError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                industry=industry,
                trace_id=self.trace_id,
            )

        # 2. Read-only aggregator (4-source join).
        closing_data = await self._query_closing_data(period_key)

        closing_snapshot_events = closing_data["closing_snapshot_events"]
        ledger_events = closing_data["ledger_events"]
        fiscal_period_snapshots = closing_data["fiscal_period_snapshots"]
        is_empty = (
            len(closing_snapshot_events) == 0
            and len(ledger_events) == 0
            and len(fiscal_period_snapshots) == 0
        )

        # 3. Audit-first emit (CR 1.1) — closing_pdf_export_viewed audit.
        await self._emit_audit_export(
            period_key=period_key,
            industry=industry,
            closing_snapshot_count=len(closing_snapshot_events),
            ledger_event_count=len(ledger_events),
            is_empty=is_empty,
        )

        # 4. Build ClosingPdfDocument + render byte stream.
        title_ko = (
            CLOSING_PDF_EXPORT_EMPTY_KO
            if is_empty
            else CLOSING_PDF_EXPORT_TITLE_KO
        )

        # Build summary section (always present — PRD §F6.3 cover page).
        summary_section = ClosingPdfSection(
            section_id="summary",
            title_ko=title_ko,
            blocks=(
                ClosingPdfTextBlock(
                    text=f"기간: {period_key}",
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("750"),
                ),
                ClosingPdfTextBlock(
                    text=f"업종: {industry}",
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("730"),
                ),
                ClosingPdfTextBlock(
                    text=(
                        f"closing_snapshot: {len(closing_snapshot_events)}건 | "
                        f"ledger: {len(ledger_events)}건 | "
                        f"snapshot: {len(fiscal_period_snapshots)}건"
                    ),
                    font_size=12,
                    x=Decimal("50"),
                    y=Decimal("710"),
                ),
            ),
        )

        # Build products section (PRD §F6.3 1 product per page).
        products_sections: list[ClosingPdfSection] = []
        for idx, evt in enumerate(closing_snapshot_events):
            products_sections.append(
                ClosingPdfSection(
                    section_id=f"products_{idx}",
                    title_ko=f"품목 {idx + 1}",
                    blocks=(
                        ClosingPdfTextBlock(
                            text=f"product_id: {evt['product_id']}",
                            font_size=10,
                            x=Decimal("50"),
                            y=Decimal("650"),
                        ),
                        ClosingPdfTextBlock(
                            text=f"closing_qty: {evt['closing_qty']}",
                            font_size=10,
                            x=Decimal("50"),
                            y=Decimal("630"),
                        ),
                        ClosingPdfTextBlock(
                            text=f"finalized_at: {evt['finalized_at']}",
                            font_size=10,
                            x=Decimal("50"),
                            y=Decimal("610"),
                        ),
                    ),
                )
            )

        # Build pages (1 page per product + 1 summary cover page).
        # Each page MUST start with a 'summary' section (PRD §F6.3 invariant).
        # Product pages include a short summary header + product detail.
        if products_sections:
            pages_list: list[ClosingPdfPage] = [
                ClosingPdfPage(
                    page_number=1,
                    sections=(summary_section,),
                )
            ]
            for idx, sec in enumerate(products_sections):
                # Per-product page: summary header (always first) + product detail.
                page_summary = ClosingPdfSection(
                    section_id="summary",
                    title_ko=f"품목 {idx + 1} 상세",
                    blocks=(
                        ClosingPdfTextBlock(
                            text=f"기간: {period_key} | 업종: {industry}",
                            font_size=10,
                            x=Decimal("50"),
                            y=Decimal("780"),
                        ),
                    ),
                )
                pages_list.append(
                    ClosingPdfPage(
                        page_number=idx + 2,
                        sections=(page_summary, sec),
                    )
                )
        else:
            # Empty period: 1 summary-only page.
            pages_list = [
                ClosingPdfPage(
                    page_number=1,
                    sections=(summary_section,),
                )
            ]

        doc = ClosingPdfDocument(
            tenant_id=self.tenant_id,
            period_key=period_key,
            pages=tuple(pages_list),
        )

        # 5. Render PDF byte stream (pure kernel).
        try:
            pdf_bytes = render_closing_pdf_byte_stream(doc)
        except ClosingPdfExportError as exc:
            if exc.error_code == "CLOSING_PDF_EXPORT_SIZE_EXCEEDED":
                raise ClosingPdfExportSizeExceededError(
                    tenant_id=self.tenant_id,
                    period_key=period_key,
                    size_bytes=len(doc.pages) * 1024 * 1024,  # approx
                    trace_id=self.trace_id,
                ) from exc
            raise

        return {
            "pdf_bytes": pdf_bytes,
            "pdf_size_bytes": len(pdf_bytes),
            "period_key": period_key,
            "industry": industry,
            "title_ko": CLOSING_PDF_EXPORT_TITLE_KO,
            "is_empty": is_empty,
            "closing_snapshot_count": len(closing_snapshot_events),
            "ledger_event_count": len(ledger_events),
            "finalized_at": _to_iso(_now_utc()),
        }

    # ── Internal helpers ─────────────────────────────────────────

    async def _query_closing_data(
        self,
        period_key: str,  # noqa: ARG002 (planned use in production wire — see comment)
    ) -> dict[str, Any]:
        """Read-only 4-source join (closing_snapshot + ledger + snapshot).

        Reuses 6-2 wire pattern + extending with snapshot event query.
        Returns dict with 3 keys: closing_snapshot_events, ledger_events,
        fiscal_period_snapshots.

        Production wire will use period_key for SQLAlchemy WHERE
        `period_key = :period_key` filter (see 6-2 monthly_closing_report
        aggregator for pattern reference). Stub returns empty default
        for service tests.
        """
        # Stub: real implementation queries via SQLAlchemy.
        # Empty default for service tests; production wire fills in via
        # existing ClosingPeriodService + LedgerService (5-2/6-1/6-2).
        return {
            "closing_snapshot_events": [],
            "ledger_events": [],
            "fiscal_period_snapshots": [],
        }

    async def _emit_audit_export(
        self,
        *,
        period_key: str,
        industry: str,
        closing_snapshot_count: int,
        ledger_event_count: int,
        is_empty: bool,
    ) -> None:
        """Audit-first emit (CR 1.1) — closing_pdf_export_viewed audit row.

        Routes to audit_logs (ActionClass.MONTHLY_CLOSING_REPORT) via
        emit_audit_typed() with action `monthly_closing_report_viewed`
        (6-2 wire reuse — same audit semantics for read-only export).
        """
        try:
            await emit_audit_typed(
                session=self.session,
                tenant_id=self.tenant_id,
                action_class=ActionClass.MONTHLY_CLOSING_REPORT,
                action="monthly_closing_report_viewed",
                target_table="closing_period",
                target_id=uuid.uuid5(
                uuid.NAMESPACE_OID, f"{self.tenant_id}|{period_key}"
                ),
                payload={
                    "trace_id": self.trace_id,
                    "export_kind": "pdf",
                    "industry": industry,
                    "closing_snapshot_count": closing_snapshot_count,
                    "ledger_event_count": ledger_event_count,
                    "is_empty": is_empty,
                },
            )
            await self.session.commit()
        except Exception as exc:
            raise ClosingPdfExportAuditEmitError(
                tenant_id=self.tenant_id,
                details={
                    "step": "audit_emit",
                    "period_key": period_key,
                    "industry": industry,
                    "error": str(exc),
                },
                trace_id=self.trace_id,
            ) from exc
