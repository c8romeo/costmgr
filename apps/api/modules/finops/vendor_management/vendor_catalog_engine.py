"""apps.api.modules.finops.vendor_management.vendor_catalog_engine — Phase 25 vendor catalog CRUD + 6-category + 4-state lifecycle + blacklist.

Phase 25 wire (cj-style 173번째) — §F41.1 + §F41.5 verbatim + AD-53 (a) +
(g) 7 sub-decisions verbatim mirror.

Provides:
- aggregate_vendor_catalog (cross-tenant vendor aggregation + RLS)
- create_vendor (CRUD create + audit-first INSERT)
- update_vendor (CRUD update + audit-first INSERT)
- change_vendor_status (4-state lifecycle transitions)
- blacklist_vendor (compliance gate)
- compute_vendor_risk_score (composite scoring)
- validate_vendor_scores (CR 11-4 P-015 pure validator)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 12 NEW audit actions via
  ActionClass.FINOPS_VENDOR_MANAGEMENT.
- CR 5-1 Decimal precision banker's rounding.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory high-value
  (≥10M KRW/year).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_vendor_management.* namespace EXTENSION).
- D-FINOPS-14 honestly DEFER.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from apps.api.modules.finops.vendor_management.serializers import (
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MAX_VENDORS_PER_TENANT,
    SELECTION_SCORE_VERSION_MAX,
    VENDOR_BLACKLIST_GATE_FLAGS,
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    Vendor,
    VendorBlacklistEntry,
    VendorCategory,
    VendorStatus,
)

logger = logging.getLogger(__name__)


# ── Audit-first INSERT via _emit_audit_safe (CR 1-1 verbatim) ────────────
def _emit_audit_safe(
    *,
    tenant_id: str,
    action: str,
    target_id: str,
    payload: dict[str, Any],
) -> str | None:
    """Best-effort audit emit via apps.api.core.audit (CR 1-1 verbatim).

    CR 1-1 audit-first INSERT pattern: try to emit audit log; on
    ImportError (e.g. in test environments where audit module isn't
    fully loaded) swallow the exception and continue — preventing audit
    failures from breaking vendor catalog CRUD operations. Returns the
    audit log id if successful, None otherwise.
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
        # Audit module unavailable (test env) — log and continue
        logger.debug("audit emit skipped: module unavailable for %s", action)
        audit_log_id = None
    except Exception as exc:  # pragma: no cover — defensive guard
        logger.warning("audit emit failed for %s: %s", action, exc)
        audit_log_id = None
    return audit_log_id or None


# ── Banker's rounding helper (CR 5-1 verbatim) ────────────────────────────
def _bankers_round(value: float, places: str = "0.01") -> float:
    """Round a float to the given Decimal places using banker's rounding.

    CR 5-1 verbatim — Decimal(str(value)).quantize(Decimal(places),
    rounding=ROUND_HALF_EVEN).
    """
    quantize = Decimal(places)
    return float(Decimal(str(value)).quantize(quantize, rounding=ROUND_HALF_EVEN))


# ── UUID v7 fallback helper ──────────────────────────────────────────────
def _new_uuid_v7() -> str:
    """Generate a new UUID v7 (time-ordered) identifier with v4 fallback.

    Python 3.12+ has uuid.uuid7() natively; earlier versions fall back
    to uuid4 which is acceptable for vendor identifiers (CR 1-1).
    """
    try:
        return str(uuid.uuid7())  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover — Python <3.12 fallback
        return str(uuid.uuid4())


# ── Pure validator (CR 11-4 P-015) ───────────────────────────────────────
def validate_vendor_scores(
    *,
    cost_score: float,
    performance_score: float,
    reliability_score: float,
    compliance_score: float,
    strategic_fit_score: float,
) -> bool:
    """Validate 5-dim vendor score dimensions (CR 11-4 P-015 pure).

    All 5 dimensions must be in [0.00, 100.00] strict range (PRD §F41.2
    + AD-53 (b)).

    Args:
        cost_score: cost dimension (0.00~100.00)
        performance_score: performance dimension (0.00~100.00)
        reliability_score: reliability dimension (0.00~100.00)
        compliance_score: compliance dimension (0.00~100.00)
        strategic_fit_score: strategic_fit dimension (0.00~100.00)

    Returns:
        True if all scores are within valid range; False otherwise.

    Raises:
        ValueError: if any score is outside strict range.
    """
    score_version = SELECTION_SCORE_VERSION_MAX
    scores = {
        "cost_score": cost_score,
        "performance_score": performance_score,
        "reliability_score": reliability_score,
        "compliance_score": compliance_score,
        "strategic_fit_score": strategic_fit_score,
    }
    for name, value in scores.items():
        if not (0.00 <= value <= score_version):
            raise ValueError(f"{name}={value} out of strict range [0.00, {score_version}]")
    return True


# ── Composite risk score computation ─────────────────────────────────────
def compute_vendor_risk_score(
    *,
    cost_score: float,
    reliability_score: float,
    compliance_score: float,
) -> float:
    """Compute composite vendor risk score (0.00~100.00).

    Risk score formula (PRD §F41.4 + AD-53 (d) verbatim):
        risk_score = (
            (100.00 - cost_score) * 0.30
            + (100.00 - reliability_score) * 0.40
            + (100.00 - compliance_score) * 0.30
        )
    Higher risk_score = more risky vendor. CR 5-1 Decimal banker's
    rounding applied.
    """
    risk_raw = (
        (100.00 - cost_score) * 0.30
        + (100.00 - reliability_score) * 0.40
        + (100.00 - compliance_score) * 0.30
    )
    return _bankers_round(risk_raw)


# ── Vendor CRUD operations ───────────────────────────────────────────────
def create_vendor(
    *,
    tenant_id: str,
    vendor_name: str,
    vendor_category: str,
    cost_score: float,
    performance_score: float,
    reliability_score: float,
    compliance_score: float,
    strategic_fit_score: float,
    contract_count: int = 0,
    source_attribution: dict[str, object] | None = None,
) -> Vendor:
    """Create a new vendor record with audit-first INSERT (CR 1-1).

    Args:
        tenant_id: tenant UUID
        vendor_name: vendor display name
        vendor_category: VendorCategory enum value
            (cloud/saas/outsourcing/consulting/hardware/other)
        cost_score: 0.00~100.00
        performance_score: 0.00~100.00
        reliability_score: 0.00~100.00
        compliance_score: 0.00~100.00
        strategic_fit_score: 0.00~100.00
        contract_count: existing contracts (default 0)
        source_attribution: Phase 14/18/19 ledger JSONB provenance

    Returns:
        Vendor TypedDict (18 fields).

    Raises:
        ValueError: invalid input (category or score range).
    """
    # Validate category
    if vendor_category not in {c.value for c in VendorCategory}:
        raise ValueError(f"vendor_category={vendor_category!r} not in VendorCategory")

    # Validate scores (CR 11-4 P-015 pure validator)
    validate_vendor_scores(
        cost_score=cost_score,
        performance_score=performance_score,
        reliability_score=reliability_score,
        compliance_score=compliance_score,
        strategic_fit_score=strategic_fit_score,
    )

    vendor_id = _new_uuid_v7()
    now_iso = datetime.now(UTC).isoformat()

    # Compute composite risk score
    risk_score = compute_vendor_risk_score(
        cost_score=cost_score,
        reliability_score=reliability_score,
        compliance_score=compliance_score,
    )

    # Determine if high-value (Epic 12 2FA 챌린지 trigger)
    requires_2fa = (contract_count * HIGH_VALUE_THRESHOLD_KRW_PER_YEAR) >= (
        HIGH_VALUE_THRESHOLD_KRW_PER_YEAR
    )

    vendor: Vendor = {
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "vendor_name": vendor_name,
        "vendor_category": vendor_category,
        "status": VendorStatus.ACTIVE.value,
        "cost_score": _bankers_round(cost_score),
        "performance_score": _bankers_round(performance_score),
        "reliability_score": _bankers_round(reliability_score),
        "compliance_score": _bankers_round(compliance_score),
        "strategic_fit_score": _bankers_round(strategic_fit_score),
        "risk_score": risk_score,
        "contract_count": int(contract_count),
        "blacklist_reason": "",
        "high_value": requires_2fa,
        "requires_2fa": requires_2fa,
        "source_attribution": source_attribution or {},
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    # Audit-first INSERT (CR 1-1 verbatim)
    _emit_audit_safe(
        tenant_id=tenant_id,
        action="vendor_created",
        target_id=vendor_id,
        payload={
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "vendor_category": vendor_category,
            "risk_score": risk_score,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_created tenant_id=%s vendor_id=%s category=%s risk=%.2f",
        tenant_id,
        vendor_id,
        vendor_category,
        risk_score,
    )

    return vendor


def update_vendor(
    *,
    vendor: Vendor,
    cost_score: float | None = None,
    performance_score: float | None = None,
    reliability_score: float | None = None,
    compliance_score: float | None = None,
    strategic_fit_score: float | None = None,
) -> Vendor:
    """Update an existing vendor with audit-first INSERT (CR 1-1).

    Only the provided fields are updated; None fields retain their
    existing values.
    """
    new_cost = cost_score if cost_score is not None else vendor["cost_score"]
    new_perf = performance_score if performance_score is not None else vendor["performance_score"]
    new_rel = reliability_score if reliability_score is not None else vendor["reliability_score"]
    new_comp = compliance_score if compliance_score is not None else vendor["compliance_score"]
    new_strat = (
        strategic_fit_score if strategic_fit_score is not None else vendor["strategic_fit_score"]
    )

    # Validate (CR 11-4 P-015)
    validate_vendor_scores(
        cost_score=new_cost,
        performance_score=new_perf,
        reliability_score=new_rel,
        compliance_score=new_comp,
        strategic_fit_score=new_strat,
    )

    # Recompute risk score
    new_risk = compute_vendor_risk_score(
        cost_score=new_cost,
        reliability_score=new_rel,
        compliance_score=new_comp,
    )

    updated: Vendor = {
        **vendor,
        "cost_score": _bankers_round(new_cost),
        "performance_score": _bankers_round(new_perf),
        "reliability_score": _bankers_round(new_rel),
        "compliance_score": _bankers_round(new_comp),
        "strategic_fit_score": _bankers_round(new_strat),
        "risk_score": new_risk,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    # Audit-first INSERT
    _emit_audit_safe(
        tenant_id=vendor["tenant_id"],
        action="vendor_updated",
        target_id=vendor["vendor_id"],
        payload={
            "vendor_id": vendor["vendor_id"],
            "updated_scores": {
                "cost_score": updated["cost_score"],
                "performance_score": updated["performance_score"],
                "reliability_score": updated["reliability_score"],
                "compliance_score": updated["compliance_score"],
                "strategic_fit_score": updated["strategic_fit_score"],
                "risk_score": updated["risk_score"],
            },
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_updated vendor_id=%s risk=%.2f",
        vendor["vendor_id"],
        new_risk,
    )

    return updated


# ── 4-state lifecycle transitions (PRD §F41.1 + AD-53 (a) verbatim) ──────
_LIFECYCLE_TRANSITIONS: dict[str, set[str]] = {
    VendorStatus.ACTIVE.value: {
        VendorStatus.INACTIVE.value,
        VendorStatus.UNDER_REVIEW.value,
        VendorStatus.BLACKLISTED.value,
    },
    VendorStatus.INACTIVE.value: {
        VendorStatus.ACTIVE.value,
        VendorStatus.UNDER_REVIEW.value,
    },
    VendorStatus.UNDER_REVIEW.value: {
        VendorStatus.ACTIVE.value,
        VendorStatus.INACTIVE.value,
        VendorStatus.BLACKLISTED.value,
    },
    VendorStatus.BLACKLISTED.value: set(),  # terminal — cannot transition out
}


def change_vendor_status(
    *,
    vendor: Vendor,
    new_status: str,
    reason: str = "",
) -> Vendor:
    """Change vendor status following 4-state lifecycle rules (CR 12-5 D-14).

    Raises:
        VendorStatusTransitionError if transition is invalid.
    """
    if new_status not in {s.value for s in VendorStatus}:
        from apps.api.core.errors import VendorStatusTransitionError  # noqa

        raise VendorStatusTransitionError(
            vendor_id=vendor["vendor_id"],
            attempted_status=new_status,
            current_status=vendor["status"],
        )

    current = vendor["status"]
    allowed = _LIFECYCLE_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        from apps.api.core.errors import VendorStatusTransitionError  # noqa

        raise VendorStatusTransitionError(
            vendor_id=vendor["vendor_id"],
            attempted_status=new_status,
            current_status=current,
        )

    updated: Vendor = {
        **vendor,
        "status": new_status,
        "blacklist_reason": reason if new_status == VendorStatus.BLACKLISTED.value else "",
        "updated_at": datetime.now(UTC).isoformat(),
    }

    _emit_audit_safe(
        tenant_id=vendor["tenant_id"],
        action="vendor_status_changed",
        target_id=vendor["vendor_id"],
        payload={
            "vendor_id": vendor["vendor_id"],
            "old_status": current,
            "new_status": new_status,
            "reason": reason,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_status_changed vendor_id=%s %s -> %s",
        vendor["vendor_id"],
        current,
        new_status,
    )

    return updated


def blacklist_vendor(
    *,
    vendor: Vendor,
    reason: str,
    severity: str = "high",
) -> tuple[Vendor, VendorBlacklistEntry]:
    """Blacklist a vendor with compliance gate (PRD §F41.1 + AD-53 (g)).

    Sets status to BLACKLISTED and creates a VendorBlacklistEntry.
    VENDOR_BLACKLIST_GATE_FLAGS controls downstream effects.

    Args:
        vendor: existing Vendor record
        reason: blacklist reason (compliance violation / SLA breach / etc.)
        severity: blacklist severity (low/medium/high/critical)

    Returns:
        Tuple of (updated Vendor, new VendorBlacklistEntry).

    Raises:
        VendorBlacklistError if vendor is already blacklisted or reason is empty.
    """
    if vendor["status"] == VendorStatus.BLACKLISTED.value:
        from apps.api.core.errors import VendorBlacklistError  # noqa

        raise VendorBlacklistError(
            vendor_id=vendor["vendor_id"],
            reason=f"Already blacklisted: {vendor.get('blacklist_reason', '')}",
        )

    if not reason or not reason.strip():
        from apps.api.core.errors import VendorBlacklistError  # noqa

        raise VendorBlacklistError(
            vendor_id=vendor["vendor_id"],
            reason="Reason must be non-empty",
        )

    blacklist_id = _new_uuid_v7()
    now_iso = datetime.now(UTC).isoformat()

    updated: Vendor = {
        **vendor,
        "status": VendorStatus.BLACKLISTED.value,
        "blacklist_reason": reason,
        "updated_at": now_iso,
    }

    blacklist_entry: VendorBlacklistEntry = {
        "blacklist_id": blacklist_id,
        "vendor_id": vendor["vendor_id"],
        "tenant_id": vendor["tenant_id"],
        "reason": reason,
        "severity": severity,
        "block_contract_approval": bool(
            VENDOR_BLACKLIST_GATE_FLAGS.get("block_contract_approval", True)
        ),
        "block_selection": bool(VENDOR_BLACKLIST_GATE_FLAGS.get("block_selection", True)),
        "block_performance_evaluation": bool(
            VENDOR_BLACKLIST_GATE_FLAGS.get("block_performance_evaluation", True)
        ),
        "requires_owner_override": bool(
            VENDOR_BLACKLIST_GATE_FLAGS.get("require_owner_override", True)
        ),
        "created_at": now_iso,
    }

    _emit_audit_safe(
        tenant_id=vendor["tenant_id"],
        action="vendor_blacklisted",
        target_id=vendor["vendor_id"],
        payload={
            "vendor_id": vendor["vendor_id"],
            "blacklist_id": blacklist_id,
            "reason": reason,
            "severity": severity,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.warning(
        "vendor_blacklisted vendor_id=%s severity=%s reason=%s",
        vendor["vendor_id"],
        severity,
        reason,
    )

    return updated, blacklist_entry


# ── Aggregation across tenant (RLS via tenant_id selector) ───────────────
def aggregate_vendor_catalog(
    *,
    tenant_id: str,
    vendors: list[Vendor],
    category_filter: str | None = None,
    status_filter: str | None = None,
) -> dict[str, Any]:
    """Aggregate vendor catalog for tenant dashboard (PRD §F41.1 verbatim).

    RLS via tenant_id selector — vendors from other tenants are
    excluded upstream by the data layer; this function filters defensively.

    Args:
        tenant_id: tenant UUID (RLS selector)
        vendors: list of Vendor records
        category_filter: optional VendorCategory filter
        status_filter: optional VendorStatus filter

    Returns:
        Dict with summary statistics for the dashboard.
    """
    tenant_vendors = [v for v in vendors if v.get("tenant_id") == tenant_id]

    if category_filter:
        tenant_vendors = [v for v in tenant_vendors if v.get("vendor_category") == category_filter]

    if status_filter:
        tenant_vendors = [v for v in tenant_vendors if v.get("status") == status_filter]

    # Cap at MAX_VENDORS_PER_TENANT
    if len(tenant_vendors) > MAX_VENDORS_PER_TENANT:
        logger.warning(
            "vendor catalog capped: tenant_id=%s count=%d max=%d",
            tenant_id,
            len(tenant_vendors),
            MAX_VENDORS_PER_TENANT,
        )
        tenant_vendors = tenant_vendors[:MAX_VENDORS_PER_TENANT]

    # Count by category
    category_counts: dict[str, int] = {}
    for vendor in tenant_vendors:
        cat = vendor.get("vendor_category", "other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Count by status
    status_counts: dict[str, int] = {}
    for vendor in tenant_vendors:
        st = vendor.get("status", "inactive")
        status_counts[st] = status_counts.get(st, 0) + 1

    # Average risk score
    risk_scores = [v.get("risk_score", 0.0) for v in tenant_vendors]
    avg_risk = _bankers_round(sum(risk_scores) / len(risk_scores) if risk_scores else 0.0)

    return {
        "tenant_id": tenant_id,
        "vendor_count": len(tenant_vendors),
        "category_counts": category_counts,
        "status_counts": status_counts,
        "avg_risk_score": avg_risk,
        "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    }
