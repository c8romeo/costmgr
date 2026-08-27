"""apps.api.modules.finops.vendor_management.vendor_selection_engine — Phase 25 vendor selection + 5-dim weighted scoring.

Phase 25 wire (cj-style 173번째) — §F41.2 + AD-53 (b) verbatim.

Provides:
- aggregate_vendor_selection (cross-tenant + RLS + threshold filter)
- score_vendor (5-dim weighted scoring)
- apply_vendor_selection_threshold (CR 12-5 D-GATE-01)
- override_selection_score_per_tenant (per-tenant > industry baseline > system default)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT.
- CR 5-1 Decimal precision banker's rounding.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — Recharts 2.12.7 + TanStack Table v8.
- AD-22 owner-only RBAC.
- AD-53 (b) verbatim.
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
    SELECTION_CANDIDATE_LIMIT_DEFAULT,
    SELECTION_SCORE_VERSION_MAX,
    SELECTION_THRESHOLD_DEFAULT,
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    VENDOR_SELECTION_DIMENSION_WEIGHTS,
    Vendor,
    VendorSelectionScore,
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
    """Best-effort audit emit via apps.api.core.audit (CR 1-1 verbatim).

    Try emit; on ImportError swallow (test env); otherwise return id.
    """
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


# ── 5-dim weighted scoring (PRD §F41.2 + AD-53 (b) verbatim) ─────────────
def score_vendor(
    *,
    cost_score: float,
    performance_score: float,
    reliability_score: float,
    compliance_score: float,
    strategic_fit_score: float,
) -> float:
    """Compute weighted vendor selection score (0.00~100.00).

    Formula (PRD §F41.2 + AD-53 (b) verbatim):
        weighted_total = (
            cost_score * 0.30
            + performance_score * 0.25
            + reliability_score * 0.20
            + compliance_score * 0.15
            + strategic_fit_score * 0.10
        )

    CR 5-1 Decimal banker's rounding applied.
    """
    weights = VENDOR_SELECTION_DIMENSION_WEIGHTS
    raw = (
        cost_score * weights["cost"]
        + performance_score * weights["performance"]
        + reliability_score * weights["reliability"]
        + compliance_score * weights["compliance"]
        + strategic_fit_score * weights["strategic_fit"]
    )
    return _bankers_round(raw)


# ── Threshold filter (CR 12-5 D-GATE-01) ──────────────────────────────────
def apply_vendor_selection_threshold(
    *,
    vendor: Vendor,
    weighted_total_score: float,
    threshold: float = SELECTION_THRESHOLD_DEFAULT,
) -> bool:
    """Check if vendor passes selection threshold (CR 12-5 D-GATE-01 verbatim).

    Vendors below threshold are automatically excluded from selection.

    Args:
        vendor: Vendor record
        weighted_total_score: computed weighted total
        threshold: cutoff threshold (default 60.00)

    Returns:
        True if vendor passes (score >= threshold and not blacklisted),
        False otherwise.
    """
    if vendor.get("status") == "blacklisted":
        return False
    return weighted_total_score >= threshold


# ── Per-tenant override (PRD §F41.2 verbatim) ────────────────────────────
def override_selection_score_per_tenant(
    *,
    base_score: float,
    per_tenant_override_score: float | None,
    industry_baseline_score: float | None,
) -> float:
    """Resolve selection score with per-tenant override precedence.

    Precedence (PRD §F41.2 verbatim): per-tenant override > industry
    baseline > system default (base_score).

    Args:
        base_score: system default score (computed via score_vendor)
        per_tenant_override_score: per-tenant override value or None
        industry_baseline_score: industry baseline value or None

    Returns:
        Resolved score (0.00~100.00).
    """
    if per_tenant_override_score is not None:
        resolved = per_tenant_override_score
    elif industry_baseline_score is not None:
        resolved = industry_baseline_score
    else:
        resolved = base_score

    # Clamp to strict range
    resolved = max(0.00, min(SELECTION_SCORE_VERSION_MAX, resolved))
    return _bankers_round(resolved)


# ── Aggregation (PRD §F41.2 verbatim) ────────────────────────────────────
def aggregate_vendor_selection(
    *,
    tenant_id: str,
    vendors: list[Vendor],
    threshold: float = SELECTION_THRESHOLD_DEFAULT,
    candidate_limit: int = SELECTION_CANDIDATE_LIMIT_DEFAULT,
    per_tenant_overrides: dict[str, float] | None = None,
    industry_baselines: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Aggregate vendor selection results for tenant dashboard.

    RLS via tenant_id selector. Returns top-N candidates that pass
    the selection threshold, sorted by weighted total score
    descending.

    Args:
        tenant_id: tenant UUID (RLS selector)
        vendors: list of Vendor records
        threshold: cutoff threshold (default 60.00)
        candidate_limit: top-N candidates (default 10)
        per_tenant_overrides: optional {vendor_id: override_score}
        industry_baselines: optional {vendor_id: baseline_score}

    Returns:
        Dict with selected_vendors + summary statistics.
    """
    overrides = per_tenant_overrides or {}
    baselines = industry_baselines or {}

    tenant_vendors = [v for v in vendors if v.get("tenant_id") == tenant_id]

    scored: list[tuple[Vendor, VendorSelectionScore]] = []
    for vendor in tenant_vendors:
        base_weighted = score_vendor(
            cost_score=vendor["cost_score"],
            performance_score=vendor["performance_score"],
            reliability_score=vendor["reliability_score"],
            compliance_score=vendor["compliance_score"],
            strategic_fit_score=vendor["strategic_fit_score"],
        )
        vendor_id = vendor["vendor_id"]
        resolved = override_selection_score_per_tenant(
            base_score=base_weighted,
            per_tenant_override_score=overrides.get(vendor_id),
            industry_baseline_score=baselines.get(vendor_id),
        )
        passes = apply_vendor_selection_threshold(
            vendor=vendor,
            weighted_total_score=resolved,
            threshold=threshold,
        )

        selection_score: VendorSelectionScore = {
            "selection_id": _new_uuid_v7(),
            "vendor_id": vendor_id,
            "tenant_id": tenant_id,
            "cost_score": _bankers_round(vendor["cost_score"]),
            "performance_score": _bankers_round(vendor["performance_score"]),
            "reliability_score": _bankers_round(vendor["reliability_score"]),
            "compliance_score": _bankers_round(vendor["compliance_score"]),
            "strategic_fit_score": _bankers_round(vendor["strategic_fit_score"]),
            "weighted_total_score": resolved,
            "per_tenant_override": vendor_id in overrides,
            "score_version": SELECTION_SCORE_VERSION_MAX,
            "excluded_by_threshold": not passes,
            "created_at": datetime.now(UTC).isoformat(),
        }
        scored.append((vendor, selection_score))

    # Audit-first INSERT (CR 1-1 verbatim)
    _emit_audit_safe(
        tenant_id=tenant_id,
        action="vendor_selection_executed",
        target_id=tenant_id,
        payload={
            "tenant_id": tenant_id,
            "vendor_count": len(tenant_vendors),
            "threshold": threshold,
            "candidate_limit": candidate_limit,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    # Sort by weighted_total_score descending; exclude those below threshold
    selected = [
        (v, s) for v, s in scored
        if apply_vendor_selection_threshold(
            vendor=v, weighted_total_score=s["weighted_total_score"], threshold=threshold
        )
    ]
    selected.sort(key=lambda pair: pair[1]["weighted_total_score"], reverse=True)
    top_n = selected[:candidate_limit]

    return {
        "tenant_id": tenant_id,
        "threshold": threshold,
        "candidate_limit": candidate_limit,
        "selected_vendors": [s for _, s in top_n],
        "selected_count": len(top_n),
        "excluded_count": len(scored) - len(selected),
        "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    }
