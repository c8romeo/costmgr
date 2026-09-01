"""apps.api.modules.finops.vendor_management.vendor_spend_attribution — Phase 25 vendor spend attribution + cross-budget reconciliation.

Phase 25 wire (cj-style 173번째) — §F41.7 + AD-53 (d) verbatim + Phase 22
settlement_results JOIN + Phase 24 budget_plan JOIN.

Provides:
- aggregate_vendor_spend_attribution (cross-tenant dashboard aggregation)
- compute_vendor_spend_attribution (per-vendor spend + variance)
- reconcile_cross_budget (Phase 24 budget reconciliation)

CR lessons applied:
- CR 0-2 RLS.
- CR 1-1 audit-first INSERT.
- CR 5-1 Decimal precision banker's rounding.
- CR 11-4 P-015.
- CR 12-1 L4 industry-agnostic.
- CR 12-5 D-14.
- AD-22 owner-only RBAC.
- AD-53 (d).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
- D-FINOPS-14 honestly DEFER.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from apps.api.modules.finops.vendor_management.serializers import (
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    VendorSpendAttribution,
)

logger = logging.getLogger(__name__)


# ── Audit-first INSERT (CR 1-1 verbatim) ──────────────────────────────────
def _emit_audit_safe(
    *,
    tenant_id: str,
    action: str,
    target_id: str,
    payload: dict[str, Any],
) -> str | None:
    """Best-effort audit emit via apps.api.core.audit (CR 1-1 verbatim)."""
    audit_log_id: str | None = None
    try:
        from apps.api.core.audit import emit_audit  # type: ignore[import-not-found]

        result = emit_audit(
            tenant_id=tenant_id,
            action=action,
            target_id=target_id,
            payload=payload,
        )
        if isinstance(result, dict):
            audit_log_id = str(result.get("audit_log_id", ""))
        else:
            audit_log_id = str(result)
    except ImportError:
        logger.debug("audit emit skipped: module unavailable for %s", action)
        audit_log_id = None
    except Exception as exc:  # pragma: no cover — defensive guard
        logger.warning("audit emit failed for %s: %s", action, exc)
        audit_log_id = None
    return audit_log_id or None


def _bankers_round(value: float, places: str = "0.01") -> float:
    """CR 5-1 verbatim — Decimal(str(value)).quantize + ROUND_HALF_EVEN."""
    quantize = Decimal(places)
    return float(Decimal(str(value)).quantize(quantize, rounding=ROUND_HALF_EVEN))


def _new_uuid_v7() -> str:
    """UUID v7 with v4 fallback (CR 1-1)."""
    try:
        return str(uuid.uuid7())  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover — Python <3.12 fallback
        return str(uuid.uuid4())


# ── Per-vendor spend attribution ─────────────────────────────────────────
def compute_vendor_spend_attribution(
    *,
    tenant_id: str,
    vendor_id: str,
    period_key: str,
    actual_amount: float,
    budget_amount: float,
) -> VendorSpendAttribution:
    """Compute vendor spend attribution with variance (PRD §F41.7 verbatim).

    Args:
        tenant_id: tenant UUID
        vendor_id: parent Vendor vendor_id
        period_key: "YYYY" / "YYYY-Qn" / "YYYY-MM"
        actual_amount: KRW actual spend (from Phase 22 settlement_results)
        budget_amount: KRW budget (from Phase 24 budget_plan)

    Returns:
        VendorSpendAttribution TypedDict (12 fields).
    """
    # Variance
    variance_amount = _bankers_round(budget_amount - actual_amount)
    variance_pct = (
        _bankers_round((variance_amount / budget_amount) * 100.0) if budget_amount > 0 else 0.0
    )
    over_budget = actual_amount > budget_amount

    attribution_id = _new_uuid_v7()
    now_iso = datetime.now(UTC).isoformat()

    attribution: VendorSpendAttribution = {
        "attribution_id": attribution_id,
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "period_key": period_key,
        "actual_amount": _bankers_round(actual_amount),
        "budget_amount": _bankers_round(budget_amount),
        "variance_amount": variance_amount,
        "variance_pct": variance_pct,
        "over_budget": over_budget,
        "cross_budget_reconciled": False,
        "audit_log_id": "",
        "computed_at": now_iso,
    }

    audit_log_id = _emit_audit_safe(
        tenant_id=tenant_id,
        action="vendor_spend_attributed",
        target_id=attribution_id,
        payload={
            "attribution_id": attribution_id,
            "vendor_id": vendor_id,
            "period_key": period_key,
            "actual_amount": actual_amount,
            "budget_amount": budget_amount,
            "variance_amount": variance_amount,
            "over_budget": over_budget,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )
    if audit_log_id is not None:
        attribution["audit_log_id"] = audit_log_id

    logger.info(
        "vendor_spend_attributed attribution_id=%s vendor_id=%s actual=%.2f budget=%.2f variance=%.2f",
        attribution_id,
        vendor_id,
        actual_amount,
        budget_amount,
        variance_amount,
    )

    return attribution


# ── Cross-budget reconciliation (Phase 22 + Phase 24 JOIN) ───────────────
def reconcile_cross_budget(
    *,
    attribution: VendorSpendAttribution,
    settlement_results_total: float,
    budget_plan_total: float,
) -> VendorSpendAttribution:
    """Reconcile vendor spend against Phase 22 + Phase 24 ledger data.

    PRD §F41.7 verbatim — Phase 22 settlement_results + Phase 24
    budget_plan cross-join. Sets cross_budget_reconciled=True if
    actual_amount matches settlement_results_total within tolerance.

    Args:
        attribution: existing VendorSpendAttribution
        settlement_results_total: KRW total from Phase 22
        budget_plan_total: KRW total from Phase 24

    Returns:
        Updated VendorSpendAttribution with cross_budget_reconciled
        flag and possibly adjusted variance.
    """
    # Cross-verify actual_amount vs settlement_results_total
    actual_matches = abs(attribution["actual_amount"] - settlement_results_total) < 0.01
    budget_matches = abs(attribution["budget_amount"] - budget_plan_total) < 0.01

    reconciled = actual_matches and budget_matches

    updated: VendorSpendAttribution = {
        **attribution,
        "budget_amount": _bankers_round(budget_plan_total),
        "variance_amount": _bankers_round(budget_plan_total - attribution["actual_amount"]),
        "cross_budget_reconciled": reconciled,
    }

    _emit_audit_safe(
        tenant_id=attribution["tenant_id"],
        action="vendor_spend_attributed",
        target_id=attribution["attribution_id"],
        payload={
            "attribution_id": attribution["attribution_id"],
            "vendor_id": attribution["vendor_id"],
            "reconciled": reconciled,
            "settlement_results_total": settlement_results_total,
            "budget_plan_total": budget_plan_total,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_spend_reconciled attribution_id=%s reconciled=%s",
        attribution["attribution_id"],
        reconciled,
    )

    return updated


# ── Aggregation across tenant ─────────────────────────────────────────────
def aggregate_vendor_spend_attribution(
    *,
    tenant_id: str,
    attributions: list[VendorSpendAttribution],
) -> dict[str, Any]:
    """Aggregate vendor spend attribution for tenant dashboard.

    RLS via tenant_id selector.
    """
    tenant_attributions = [a for a in attributions if a.get("tenant_id") == tenant_id]

    total_actual = 0.0
    total_budget = 0.0
    over_budget_count = 0
    reconciled_count = 0

    for attr in tenant_attributions:
        total_actual += attr.get("actual_amount", 0.0)
        total_budget += attr.get("budget_amount", 0.0)
        if attr.get("over_budget", False):
            over_budget_count += 1
        if attr.get("cross_budget_reconciled", False):
            reconciled_count += 1

    total_variance = _bankers_round(total_budget - total_actual)
    variance_pct = (
        _bankers_round((total_variance / total_budget) * 100.0) if total_budget > 0 else 0.0
    )

    return {
        "tenant_id": tenant_id,
        "attribution_count": len(tenant_attributions),
        "total_actual_krw": _bankers_round(total_actual),
        "total_budget_krw": _bankers_round(total_budget),
        "total_variance_krw": total_variance,
        "total_variance_pct": variance_pct,
        "over_budget_count": over_budget_count,
        "reconciled_count": reconciled_count,
        "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    }
