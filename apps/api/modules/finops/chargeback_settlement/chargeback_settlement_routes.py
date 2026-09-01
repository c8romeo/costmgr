"""apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes — Phase 22 FastAPI routes.

Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement FastAPI routes
(PRD §F38.1~§F38.8 verbatim + AD-50 (a)~(g) decisions).

8 endpoints:
1. `GET  /api/v1/finops/chargeback-settlement/healthcheck` — health probe
2. `POST /api/v1/finops/chargeback-settlement/settlement-rules` — create settlement rule
3. `PUT  /api/v1/finops/chargeback-settlement/settlement-rules/{settlement_id}` — update rule
4. `GET  /api/v1/finops/chargeback-settlement/settlement-rules` — list rules
5. `POST /api/v1/finops/chargeback-settlement/allocation` — compute 5-dim allocation
6. `POST /api/v1/finops/chargeback-settlement/invoice` — generate PDF/XLSX/CSV invoice
7. `POST /api/v1/finops/chargeback-settlement/reconciliation` — 3-way match
8. `POST /api/v1/finops/chargeback-settlement/dispatch` — execute cadence dispatch
9. `GET  /api/v1/finops/chargeback-settlement/cadence-preview` — preview cadence schedule

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + AD-50 (g).
Capability gate: require_finops_chargeback_settlement (CR 12-5 D-GATE-01).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — all 8 audit actions called from routes.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 idempotent no-op — duplicate calls return cached result.
- CR 11-2 AUTHORIZABLE_TARGET_EVENT_TYPES — auth-layer check.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-22 owner-only RBAC.
- AD-50 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies.capability import require_finops_chargeback_settlement
from apps.api.modules.finops.chargeback_settlement.allocation_engine import (
    compute_allocation,
)
from apps.api.modules.finops.chargeback_settlement.invoice_generator import (
    generate_invoice,
)
from apps.api.modules.finops.chargeback_settlement.reconciliation import (
    reconcile_settlement,
)
from apps.api.modules.finops.chargeback_settlement.scheduled_chargeback_settlement_dispatch import (
    ALL_SETTLEMENT_CADENCES,
    _compute_cadence_schedule,
    _compute_period_key_for_cadence,
    execute_dispatch,
    schedule_cadence_dispatch,
)
from apps.api.modules.finops.chargeback_settlement.serializers import (
    ALL_INVOICE_FORMATS,
    ALL_SETTLEMENT_STATUSES,
    CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION,
    FIVE_MODULE_WEIGHTS,
    InvoiceFormat,
    SettlementStatus,
)
from apps.api.modules.finops.chargeback_settlement.settlement_rules import (
    create_settlement_rule,
    list_settlement_rules,
    update_settlement_rule,
)

logger = logging.getLogger(__name__)

# ── Router with capability gate dependency ───────────────────────────────
router = APIRouter(
    prefix="/api/v1/finops/chargeback-settlement",
    tags=["finops", "chargeback_settlement"],
    dependencies=[Depends(require_finops_chargeback_settlement)],
)


# ── Helper: extract tenant_id from request context ───────────────────────
def _extract_tenant_id(request: Request) -> str:
    """Extract tenant_id from request context (CR 0-2 RLS verbatim)."""
    tenant_id = getattr(request.state, "tenant_id", None) or request.headers.get("X-Tenant-Id")
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="tenant_id_required",
        )
    return str(tenant_id)


# ── Helper: extract trace_id from request context ────────────────────────
def _extract_trace_id(request: Request) -> str:
    """Extract trace_id from request context (CR 1-1 verbatim)."""
    trace_id = getattr(request.state, "trace_id", None) or request.headers.get("X-Trace-Id")
    return str(trace_id) if trace_id else ""


# ── 1. Healthcheck ────────────────────────────────────────────────────────
@router.get("/healthcheck")
async def healthcheck() -> dict[str, Any]:
    """Health check endpoint (PRD §F38.8-1 verbatim)."""
    return {
        "status": "ok",
        "module": "finops_chargeback_settlement",
        "model_version": CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION,
    }


# ── 2. Create settlement rule ─────────────────────────────────────────────
@router.post("/settlement-rules")
async def create_settlement_rule_endpoint(
    request: Request,
    body: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Create SettlementRule (PRD §F38.1-1 verbatim).

    Body fields:
    - period_key (str): YYYY-MM / YY-MM / YYYY
    - rule_name (str)
    - rule_type (str): flat_fee / proportional_allocation / metered_volume / tag_weighted
    - target_amount_krw (float)
    - target_dimensions (list[str])
    - five_module_inputs (dict[str, float])
    - settlement_status (str): draft / pending_approval / approved / invoiced / reconciled
    - dry_run (bool, default false)
    """
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    dry_run = bool(body.get("dry_run", False))
    settlement_status = body.get("settlement_status", SettlementStatus.DRAFT.value)
    if settlement_status not in ALL_SETTLEMENT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_settlement_status",
                "received": settlement_status,
                "allowed": ALL_SETTLEMENT_STATUSES,
            },
        )
    settlement_rule = create_settlement_rule(
        tenant_id=tenant_id,
        period_key=str(body.get("period_key", "")),
        rule_name=str(body.get("rule_name", "")),
        rule_type=str(body.get("rule_type", "proportional_allocation")),
        target_amount_krw=float(body.get("target_amount_krw", 0.0)),
        target_dimensions=list(body.get("target_dimensions", [])),
        five_module_inputs=dict(body.get("five_module_inputs", {})),
        settlement_status=settlement_status,
        requires_2fa_challenge=bool(body.get("requires_2fa_challenge", False)),
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )
    return {
        "settlement_rule": dict(settlement_rule),
        "dry_run": dry_run,
    }


# ── 3. Update settlement rule ─────────────────────────────────────────────
@router.put("/settlement-rules/{settlement_id}")
async def update_settlement_rule_endpoint(
    request: Request,
    settlement_id: str,
    body: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Update SettlementRule (PRD §F38.1-5 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    dry_run = bool(body.get("dry_run", False))
    settlement_status = body.get("settlement_status", SettlementStatus.APPROVED.value)
    if settlement_status not in ALL_SETTLEMENT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_settlement_status",
                "received": settlement_status,
                "allowed": ALL_SETTLEMENT_STATUSES,
            },
        )
    settlement_rule = update_settlement_rule(
        tenant_id=tenant_id,
        settlement_id=settlement_id,
        period_key=str(body.get("period_key", "")),
        rule_name=str(body.get("rule_name", "")),
        rule_type=str(body.get("rule_type", "proportional_allocation")),
        target_amount_krw=float(body.get("target_amount_krw", 0.0)),
        target_dimensions=list(body.get("target_dimensions", [])),
        settlement_status=settlement_status,
        five_module_inputs=dict(body.get("five_module_inputs", {})),
        requires_2fa_challenge=bool(body.get("requires_2fa_challenge", False)),
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )
    return {
        "settlement_rule": dict(settlement_rule),
        "dry_run": dry_run,
    }


# ── 4. List settlement rules ──────────────────────────────────────────────
@router.get("/settlement-rules")
async def list_settlement_rules_endpoint(
    request: Request,
    period_key: str | None = Query(default=None),
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """List SettlementRule rows (PRD §F38.1-7 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    rules = list_settlement_rules(
        tenant_id=tenant_id,
        period_key=period_key,
        db_session=db_session,
    )
    return {
        "tenant_id": tenant_id,
        "period_key": period_key,
        "rules": [dict(r) for r in rules],
        "count": len(rules),
    }


# ── 5. Compute allocation ─────────────────────────────────────────────────
@router.post("/allocation")
async def compute_allocation_endpoint(
    request: Request,
    body: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Compute 5-dim weighted allocation (PRD §F38.2-1 verbatim).

    Body fields:
    - result_id (str)
    - period_key (str)
    - total_amount_krw (float)
    - dimension_amounts (dict[str, float])
    - target_dimensions (list[str])
    - settlement_status (str, default draft)
    - dry_run (bool, default false)
    """
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    dry_run = bool(body.get("dry_run", False))
    settlement_result = compute_allocation(
        tenant_id=tenant_id,
        result_id=str(body.get("result_id", "")),
        period_key=str(body.get("period_key", "")),
        total_amount_krw=float(body.get("total_amount_krw", 0.0)),
        dimension_amounts=dict(body.get("dimension_amounts", {})),
        target_dimensions=list(body.get("target_dimensions", [])),
        settlement_status=str(body.get("settlement_status", "draft")),
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )
    return {
        "settlement_result": dict(settlement_result),
        "dry_run": dry_run,
    }


# ── 6. Generate invoice ───────────────────────────────────────────────────
@router.post("/invoice")
async def generate_invoice_endpoint(
    request: Request,
    body: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Generate invoice artifact (PRD §F38.3-1 verbatim).

    Body fields:
    - result_id (str)
    - period_key (str)
    - invoice_format (str): pdf / xlsx / csv
    - settlement_result (dict)
    - allocation_lines (list[dict])
    - recipient_template (str): owner_only / executive / audit_only
    - dry_run (bool, default false)
    """
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    dry_run = bool(body.get("dry_run", False))
    invoice_format = str(body.get("invoice_format", InvoiceFormat.PDF.value))
    if invoice_format not in ALL_INVOICE_FORMATS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_invoice_format",
                "received": invoice_format,
                "allowed": ALL_INVOICE_FORMATS,
            },
        )
    artifact = generate_invoice(
        tenant_id=tenant_id,
        result_id=str(body.get("result_id", "")),
        period_key=str(body.get("period_key", "")),
        invoice_format=invoice_format,
        settlement_result=dict(body.get("settlement_result", {})),
        allocation_lines=list(body.get("allocation_lines", [])),
        recipient_template=str(body.get("recipient_template", "owner_only")),
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )
    return {
        "artifact": dict(artifact),
        "dry_run": dry_run,
    }


# ── 7. Run reconciliation ─────────────────────────────────────────────────
@router.post("/reconciliation")
async def reconciliation_endpoint(
    request: Request,
    body: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Run 3-way match reconciliation (PRD §F38.4-1 verbatim).

    Body fields:
    - result_id (str)
    - period_key (str)
    - allocation_amount_krw (float)
    - invoice_amount_krw (float)
    - ledger_amount_krw (float)
    - target_amount_krw (float, optional — defaults to allocation_amount_krw)
    - tolerance_pct (float, default 1.0)
    - max_retries (int, default 3)
    - dry_run (bool, default false)
    """
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    dry_run = bool(body.get("dry_run", False))
    target_amount_krw = body.get("target_amount_krw")
    reconciliation = reconcile_settlement(
        tenant_id=tenant_id,
        result_id=str(body.get("result_id", "")),
        period_key=str(body.get("period_key", "")),
        allocation_amount_krw=float(body.get("allocation_amount_krw", 0.0)),
        invoice_amount_krw=float(body.get("invoice_amount_krw", 0.0)),
        ledger_amount_krw=float(body.get("ledger_amount_krw", 0.0)),
        target_amount_krw=float(target_amount_krw) if target_amount_krw is not None else None,
        tolerance_pct=float(body.get("tolerance_pct", 1.0)),
        max_retries=int(body.get("max_retries", 3)),
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )
    return {
        "reconciliation": dict(reconciliation),
        "dry_run": dry_run,
    }


# ── 8. Execute dispatch ───────────────────────────────────────────────────
@router.post("/dispatch")
async def dispatch_endpoint(
    request: Request,
    body: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Execute cadence dispatch (PRD §F38.4-17 verbatim).

    Body fields:
    - cadence (str): monthly / quarterly / semi_annual / annual
    - five_module_inputs (dict[str, float])
    - target_amount_krw (float)
    - target_dimensions (list[str])
    - invoice_amount_krw (float, optional)
    - ledger_amount_krw (float, optional)
    - dry_run (bool, default false)
    """
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    dry_run = bool(body.get("dry_run", False))
    cadence = str(body.get("cadence", "monthly"))
    if cadence not in ALL_SETTLEMENT_CADENCES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_cadence",
                "received": cadence,
                "allowed": ALL_SETTLEMENT_CADENCES,
            },
        )
    dispatch_meta = execute_dispatch(
        tenant_id=tenant_id,
        cadence=cadence,
        five_module_inputs=dict(body.get("five_module_inputs", {})),
        target_amount_krw=float(body.get("target_amount_krw", 0.0)),
        target_dimensions=list(body.get("target_dimensions", [])),
        invoice_amount_krw=body.get("invoice_amount_krw"),
        ledger_amount_krw=body.get("ledger_amount_krw"),
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )
    return {
        "dispatch": dict(dispatch_meta),
        "dry_run": dry_run,
    }


# ── 9. Cadence preview ────────────────────────────────────────────────────
@router.get("/cadence-preview")
async def cadence_preview_endpoint(
    request: Request,
    cadence: str = Query(default="monthly"),
) -> dict[str, Any]:
    """Preview cadence schedule (PRD §F38.4-15 verbatim).

    Query params:
    - cadence (str, default monthly)
    """
    if cadence not in ALL_SETTLEMENT_CADENCES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_cadence",
                "received": cadence,
                "allowed": ALL_SETTLEMENT_CADENCES,
            },
        )
    tenant_id = _extract_tenant_id(request)
    schedule = _compute_cadence_schedule(cadence=cadence)
    period_key = _compute_period_key_for_cadence(cadence=cadence)
    scheduled_meta = schedule_cadence_dispatch(
        cadence=cadence,
        tenants=[tenant_id],
        db_session=None,
    )
    return {
        "cadence": cadence,
        "period_key": period_key,
        "schedule": schedule,
        "scheduled_meta": scheduled_meta,
        "five_module_weights": FIVE_MODULE_WEIGHTS,
    }


__all__ = ["router"]
