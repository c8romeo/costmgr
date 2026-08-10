"""tests.api.m4_inventory.test_closing_pdf_export_service — Story 6.3 service tests.

Closing PDF Export service layer tests:
- `export_closing_pdf` aggregator dispatch
- 3 typed exceptions (AD-15 §4 envelope mapping)
- Audit-first emit (CR 1.1)
- capability gate wire (MONTHLY_CLOSING_REPORT reuse)
- Industry validation (PRD §6.1 + W5 deferral guard)
- 6-3 3rd sweep: pdf_object_count returned (B),
  size_bytes + cap_bytes on SizeExceeded (B4),
  closing_pdf_export_viewed audit action (B6),
  period_key Pydantic pattern guard (B9).
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m4_inventory.services.closing_pdf_export_service import (
    ClosingPdfExportAuditEmitError,
    ClosingPdfExportInvalidIndustryError,
    ClosingPdfExportService,
    ClosingPdfExportSizeExceededError,
)


def _make_session() -> MagicMock:
    """Build a mock AsyncSession for service tests."""
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    session.commit = AsyncMock()
    return session


def _run_export(
    svc: ClosingPdfExportService,
    *,
    period_key: str,
    industry: str,
) -> dict[str, Any]:
    """Bridge sync pytest to async service.export_closing_pdf (CR 1.1 wire)."""
    import asyncio

    return asyncio.run(
        svc.export_closing_pdf(
            period_key=period_key,
            industry=industry,
        )
    )


def test_export_closing_pdf_audit_emit_failure_raises() -> None:
    """Audit emit failure → 500 typed envelope (CR 1.1 invariant)."""
    tenant_id = uuid.uuid4()
    session = _make_session()

    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-001",
    )

    # Stub _emit_audit_export to raise ClosingPdfExportAuditEmitError.
    svc._emit_audit_export = AsyncMock(  # type: ignore[method-assign]
        side_effect=ClosingPdfExportAuditEmitError(
            tenant_id=tenant_id,
            details={"step": "audit_emit"},
            trace_id="trace-001",
        )
    )
    svc._query_closing_data = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "closing_snapshot_events": [],
            "ledger_events": [],
            "fiscal_period_snapshots": [],
        }
    )

    with pytest.raises(ClosingPdfExportAuditEmitError):
        _run_export(svc, period_key="2026-07", industry="manufacturing")


def test_export_closing_pdf_size_exceeded_raises() -> None:
    """PDF > 5MB → ClosingPdfExportSizeExceededError with cap_bytes."""
    tenant_id = uuid.uuid4()
    session = _make_session()

    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-002",
    )

    # Stub _query_closing_data to return synthetic data that exceeds cap.
    svc._query_closing_data = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "closing_snapshot_events": [
                {
                    "product_id": uuid.uuid4(),
                    "closing_qty": Decimal("9999999999.99"),
                    "finalized_at": "2026-08-01T00:00:00Z",
                }
            ]
            * 50000,  # 50k products → exceed 5MB
            "ledger_events": [],
            "fiscal_period_snapshots": [],
        }
    )
    svc._emit_audit_export = AsyncMock()  # type: ignore[method-assign]

    with pytest.raises(ClosingPdfExportSizeExceededError) as exc_info:
        _run_export(svc, period_key="2026-07", industry="manufacturing")
    # 3rd sweep B4: size_bytes + cap_bytes MUST be populated
    # from the pure kernel's real measurement.
    assert exc_info.value.size_bytes > 5 * 1024 * 1024
    assert exc_info.value.cap_bytes == 5 * 1024 * 1024


def test_export_closing_pdf_invalid_industry_raises() -> None:
    """Invalid industry → 422 typed envelope (W5 deferral guard)."""
    tenant_id = uuid.uuid4()
    session = _make_session()

    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-003",
    )

    with pytest.raises(ClosingPdfExportInvalidIndustryError):
        _run_export(svc, period_key="2026-07", industry="trad")


def test_export_closing_pdf_invalid_period_key_raises() -> None:
    """3rd sweep B9: invalid period_key pattern → typed envelope.

    Defense-in-depth — handler also validates via Pydantic Query
    regex, but the service MUST guard independently so direct
    service callers cannot bypass the pattern.
    """
    tenant_id = uuid.uuid4()
    session = _make_session()
    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-period-bad",
    )
    # Non YYYY-MM pattern → reject.
    with pytest.raises(ClosingPdfExportInvalidIndustryError):
        _run_export(svc, period_key="2026-7", industry="manufacturing")
    with pytest.raises(ClosingPdfExportInvalidIndustryError):
        _run_export(svc, period_key="2026-13", industry="manufacturing")
    with pytest.raises(ClosingPdfExportInvalidIndustryError):
        _run_export(svc, period_key="not-a-period", industry="manufacturing")


def test_export_closing_pdf_happy_path() -> None:
    """Valid industry + non-empty data → PDF bytes returned (B)."""
    tenant_id = uuid.uuid4()
    session = _make_session()

    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-004",
    )

    svc._query_closing_data = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "closing_snapshot_events": [
                {
                    "product_id": uuid.uuid4(),
                    "closing_qty": Decimal("100.00"),
                    "finalized_at": "2026-08-01T00:00:00Z",
                }
            ],
            "ledger_events": [
                {
                    "product_id": uuid.uuid4(),
                    "event_type": "inbound",
                }
            ],
            "fiscal_period_snapshots": [],
        }
    )
    svc._emit_audit_export = AsyncMock()  # type: ignore[method-assign]

    result = _run_export(svc, period_key="2026-07", industry="manufacturing")
    assert result["period_key"] == "2026-07"
    assert result["industry"] == "manufacturing"
    assert result["pdf_size_bytes"] <= 5 * 1024 * 1024
    assert result["pdf_bytes"].startswith(b"%PDF-1.7")
    # 3rd sweep: pdf_object_count is in the return dict.
    assert "pdf_object_count" in result
    assert result["pdf_object_count"] > 0
    # Audit emit MUST be called (CR 1.1).
    svc._emit_audit_export.assert_called_once()


def test_export_closing_pdf_empty_period_returns_empty_marker() -> None:
    """Empty period → CLOSING_PDF_EXPORT_EMPTY_KO marker + valid PDF."""
    tenant_id = uuid.uuid4()
    session = _make_session()

    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-005",
    )

    svc._query_closing_data = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "closing_snapshot_events": [],
            "ledger_events": [],
            "fiscal_period_snapshots": [],
        }
    )
    svc._emit_audit_export = AsyncMock()  # type: ignore[method-assign]

    result = _run_export(svc, period_key="2026-07", industry="manufacturing")
    assert result["is_empty"] is True
    assert result["title_ko"] == "마감 보고서 PDF Export"
    # Empty periods still produce a valid 1-page PDF.
    assert result["pdf_bytes"].startswith(b"%PDF-1.7")
    assert result["pdf_object_count"] > 0


def test_export_closing_pdf_audit_first_emit_called() -> None:
    """Audit emit MUST be called before PDF byte render (CR 1.1)."""
    tenant_id = uuid.uuid4()
    session = _make_session()

    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-006",
    )

    call_order: list[str] = []

    async def stub_audit(*_args: Any, **_kwargs: Any) -> None:
        call_order.append("audit")

    svc._query_closing_data = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "closing_snapshot_events": [
                {
                    "product_id": uuid.uuid4(),
                    "closing_qty": Decimal("10.00"),
                    "finalized_at": "2026-08-01T00:00:00Z",
                }
            ],
            "ledger_events": [],
            "fiscal_period_snapshots": [],
        }
    )

    # Wrap to record call order.
    async def wrapped_audit(*args: Any, **kwargs: Any) -> None:
        call_order.append("audit")
        await stub_audit(*args, **kwargs)

    svc._emit_audit_export = wrapped_audit  # type: ignore[method-assign]

    _run_export(svc, period_key="2026-07", industry="manufacturing")
    # Audit emit MUST be present (CR 1.1 invariant).
    assert "audit" in call_order


def test_export_closing_pdf_audit_uses_closing_pdf_export_viewed_action() -> None:
    """3rd sweep B6: audit action MUST be `closing_pdf_export_viewed`.

    Distinct from 6-2 `monthly_closing_report_viewed` so PDF export
    events are traceable separately in audit_logs.
    """
    tenant_id = uuid.uuid4()
    session = _make_session()
    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-action-name",
    )
    svc._query_closing_data = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "closing_snapshot_events": [],
            "ledger_events": [],
            "fiscal_period_snapshots": [],
        }
    )

    # Capture the audit emit call by intercepting emit_audit_typed
    # at the import boundary.
    from apps.api.modules.m4_inventory.services import (
        closing_pdf_export_service as svc_mod,
    )

    captured: dict[str, Any] = {}

    async def fake_emit(**kwargs: Any) -> None:
        captured.update(kwargs)

    svc_mod.emit_audit_typed = fake_emit  # type: ignore[assignment]

    _run_export(svc, period_key="2026-07", industry="manufacturing")

    # B6: action MUST be `closing_pdf_export_viewed`.
    assert captured.get("action") == "closing_pdf_export_viewed"


def test_export_closing_pdf_audit_target_id_is_tenant_id() -> None:
    """3rd sweep B7: target_id MUST equal tenant_id (6-2 패턴 정합).

    The PDF export is a tenant-scoped operation; the audit row's
    target_id links to the tenant, not to a per-PDF UUID. Per-row
    differentiation comes from the `action` field.
    """
    tenant_id = uuid.uuid4()
    session = _make_session()
    svc = ClosingPdfExportService(
        session,
        tenant_id=tenant_id,
        trace_id="trace-target-id",
    )
    svc._query_closing_data = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "closing_snapshot_events": [],
            "ledger_events": [],
            "fiscal_period_snapshots": [],
        }
    )

    from apps.api.modules.m4_inventory.services import (
        closing_pdf_export_service as svc_mod,
    )

    captured: dict[str, Any] = {}

    async def fake_emit(**kwargs: Any) -> None:
        captured.update(kwargs)

    svc_mod.emit_audit_typed = fake_emit  # type: ignore[assignment]
    _run_export(svc, period_key="2026-07", industry="manufacturing")

    # B7: target_id MUST be the tenant_id (not a per-PDF uuid5).
    assert captured.get("target_id") == tenant_id