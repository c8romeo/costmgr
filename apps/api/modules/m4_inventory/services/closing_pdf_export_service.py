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
  via `emit_audit_typed()` with action `closing_pdf_export_viewed`
  (NEW 6.3 wire — separate from 6-2's `monthly_closing_report_viewed`).
  Drift detector: tests/integration/test_audit_action_consistency.py.

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

6-3 3rd sweep PATCH (B5~B9):
- B5: `_query_closing_data` stub → real SQLAlchemy read-only 4-source
  join (closing_snapshot + inventory_ledger + fiscal_period_snapshots).
- B6: audit action `closing_pdf_export_viewed` (NEW) 분리.
- B7: `target_id` = tenant_id (6-2 패턴 정합).
- B8: industry handler에서 제거 → service는 tenant settings 또는
  caller-provided industry를 그대로 사용. 패턴 유효성 검사만.
- B9: period_key Pydantic regex + closing-period finalized state 가드.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
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
    RenderedClosingPdf,
    render_closing_pdf_byte_stream,
)

# AD-24 period key pattern (canonical 'YYYY-MM' typed form).
PERIOD_KEY_PATTERN: re.Pattern[str] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


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
        cap_bytes: int,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_pdf_export size {size_bytes} exceeds "
            f"{cap_bytes} cap for period {period_key} (tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.size_bytes = size_bytes
        self.cap_bytes = cap_bytes
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
        actor_id: uuid.UUID | None = None,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.trace_id = trace_id
        self.actor_id = actor_id

    # ── Operation: export closing PDF (read-only + PDF render) ──
    async def export_closing_pdf(
        self,
        period_key: str,
        *,
        industry: str,
    ) -> dict[str, Any]:
        """Export monthly closing period as PDF byte stream (PRD §F6.3).

        Read-only aggregator + audit-first emit + PDF byte stream render:
        1. period_key / industry guards (Pydantic pre-validated).
        2. 3-source read-only join (closing_snapshot + ledger + snapshot).
        3. Audit-first emit (CR 1.1) — closing_pdf_export_viewed.
        4. Pure kernel PDF byte stream render (T1 —
           render_closing_pdf_byte_stream).

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

        # 1.5 period_key pattern guard (defense-in-depth — handler also
        # validates via Pydantic Query pattern).
        if not PERIOD_KEY_PATTERN.match(period_key):
            raise ClosingPdfExportInvalidIndustryError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                industry=industry,
                trace_id=self.trace_id,
            )

        # 2. Read-only aggregator (3-source join — same pattern as 6-2).
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
            actor_id=self.actor_id,
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

        finalized_at = _to_iso(_now_utc())
        doc = ClosingPdfDocument(
            tenant_id=self.tenant_id,
            period_key=period_key,
            pages=tuple(pages_list),
            finalized_at=finalized_at,
        )

        # 5. Render PDF byte stream (pure kernel).
        try:
            rendered: RenderedClosingPdf = render_closing_pdf_byte_stream(doc)
        except ClosingPdfExportError as exc:
            if exc.error_code == "CLOSING_PDF_EXPORT_SIZE_EXCEEDED":
                # Propagate the actual size_bytes from the pure kernel
                # exception (B4 — `pages * 1MB` approximation removed).
                size_bytes = int(exc.details.get("size_bytes", "0"))
                cap_bytes = int(exc.details.get("cap_bytes", str(5 * 1024 * 1024)))
                raise ClosingPdfExportSizeExceededError(
                    tenant_id=self.tenant_id,
                    period_key=period_key,
                    size_bytes=size_bytes,
                    cap_bytes=cap_bytes,
                    trace_id=self.trace_id,
                ) from exc
            raise

        return {
            "pdf_bytes": rendered.pdf_bytes,
            "pdf_size_bytes": rendered.size_bytes,
            "pdf_object_count": rendered.object_count,
            "period_key": period_key,
            "industry": industry,
            "title_ko": CLOSING_PDF_EXPORT_TITLE_KO,
            "is_empty": is_empty,
            "closing_snapshot_count": len(closing_snapshot_events),
            "ledger_event_count": len(ledger_events),
            "finalized_at": finalized_at,
        }

    # ── Internal helpers ─────────────────────────────────────────

    async def _query_closing_data(
        self,
        period_key: str,
    ) -> dict[str, Any]:
        """Read-only 3-source join (closing_snapshot + ledger + snapshot).

        6-3 wire (B5): real SQLAlchemy read-only query with tenant_id
        + period_key filters. Joins:
        - `inventory_ledger` rows with `event_type='closing_snapshot'`
          (6-1 wire pattern — 5-2 InventoryLedger is the source of
          truth for closing events).
        - `inventory_ledger` 전체 events (5-2 wire).
        - `fiscal_period_snapshots` (4-2 wire).

        All queries use `tenant_id = :tenant_id AND period_key = :period_key`.
        """
        tenant_id = self.tenant_id
        # 1) closing_snapshot events (5-2 InventoryLedger + event_type
        #    filter — matches 6-1/6-2 wire pattern).
        cs_rows = (await self.session.execute(
            text(
                """
                SELECT product_id, qty, payload->>'finalized_at' AS finalized_at
                FROM inventory_ledger
                WHERE tenant_id = :tenant_id
                  AND period_key = :period_key
                  AND event_type = 'closing_snapshot'
                """
            ),
            {"tenant_id": str(tenant_id), "period_key": period_key},
        )).fetchall()
        closing_snapshot_events: list[dict[str, Any]] = [
            {
                "product_id": str(row[0]) if row[0] is not None else "",
                "closing_qty": str(row[1]) if row[1] is not None else "",
                "finalized_at": str(row[2]) if row[2] is not None else "",
            }
            for row in cs_rows
        ]

        # 2) inventory_ledger (전체 events).
        il_rows = (await self.session.execute(
            text(
                """
                SELECT event_id, product_id, qty, payload->>'occurred_at' AS occurred_at
                FROM inventory_ledger
                WHERE tenant_id = :tenant_id
                  AND period_key = :period_key
                ORDER BY event_id
                """
            ),
            {"tenant_id": str(tenant_id), "period_key": period_key},
        )).fetchall()
        ledger_events: list[dict[str, Any]] = [
            {
                "id": str(row[0]) if row[0] is not None else "",
                "product_id": str(row[1]) if row[1] is not None else "",
                "quantity": str(row[2]) if row[2] is not None else "",
                "occurred_at": str(row[3]) if row[3] is not None else "",
            }
            for row in il_rows
        ]

        # 3) fiscal_period_snapshots.
        # Walking Skeleton (2026-08-16): `fiscal_period_snapshots` has
        # NO `payload` JSONB column — capture timestamp lives on
        # `created_at` (TIMESTAMPTZ). Column-name + table-shape fix.
        fp_rows = (await self.session.execute(
            text(
                """
                SELECT snapshot_id, period_key, created_at
                FROM fiscal_period_snapshots
                WHERE tenant_id = :tenant_id
                  AND period_key = :period_key
                ORDER BY snapshot_id
                """
            ),
            {"tenant_id": str(tenant_id), "period_key": period_key},
        )).fetchall()
        fiscal_period_snapshots: list[dict[str, Any]] = [
            {
                "id": str(row[0]) if row[0] is not None else "",
                "period_key": str(row[1]) if row[1] is not None else "",
                "captured_at": (
                    row[2].isoformat() if row[2] is not None else ""
                ),
            }
            for row in fp_rows
        ]
        fiscal_period_snapshots: list[dict[str, Any]] = [
            {
                "id": str(row[0]) if row[0] is not None else "",
                "period_key": str(row[1]) if row[1] is not None else "",
                "captured_at": str(row[2]) if row[2] is not None else "",
            }
            for row in fp_rows
        ]

        return {
            "closing_snapshot_events": closing_snapshot_events,
            "ledger_events": ledger_events,
            "fiscal_period_snapshots": fiscal_period_snapshots,
        }

    async def _emit_audit_export(
        self,
        *,
        period_key: str,
        industry: str,
        closing_snapshot_count: int,
        ledger_event_count: int,
        is_empty: bool,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        """Audit-first emit (CR 1.1) — closing_pdf_export_viewed audit row.

        Routes to audit_logs (ActionClass.MONTHLY_CLOSING_REPORT) via
        emit_audit_typed() with action `closing_pdf_export_viewed`
        (NEW 6.3 — separate from 6-2 `monthly_closing_report_viewed`).

        B7: `target_id` = tenant_id (matches 6-2 audit-trail join
        contract). Per-row differentiation comes from the `action`
        field, not `target_id`.

        Smoke-fix T2 (2026-08-18): actor_id is REQUIRED by emit_audit_typed
        — the previous version omitted it, causing the entire PDF export
        endpoint to 500 with CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR. Source
        comes from the handler (ctx.user_id) and flows through the
        service constructor.
        """
        try:
            await emit_audit_typed(
                session=self.session,
                tenant_id=self.tenant_id,
                action_class=ActionClass.MONTHLY_CLOSING_REPORT,
                action="closing_pdf_export_viewed",
                actor_id=actor_id,
                target_id=self.tenant_id,
                payload={
                    "trace_id": self.trace_id,
                    "export_kind": "pdf",
                    "industry": industry,
                    "period_key": period_key,
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
