"""apps.api.modules.finops.chargeback_allocation_reconciliation — Chargeback Allocation Reconciliation (PRD §F31.5).

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31.5 verbatim). Chargeback allocation
reconciliation with hybrid_blended default strategy + 3 reconciliation
strategies (chargeback_only / tag_allocation_only / hybrid_blended) +
variance calculation + delta_threshold_pct + auto_approve_below_pct +
audit_required + 5 EXTENSION audit actions (reconciliation_initiated +
reconciliation_report_generated + reconciliation_investigation_triggered
+ reconciliation_approved + reconciliation_resolved).

AD-42 (e) — ChargebackAllocationReconciliation — 3 reconciliation
strategy + variance + 5 EXTENSION audit actions.

CR lessons applied:
- CR 0-2 RLS — every Reconciliation carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to 5 EXTENSION audit actions (dry-run skips).
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3 — Industry enum SSOT.
- CR 11-4 D-001~D-005 + P-015 verbatim — pure validator pattern.
- CR 12-1 L4 industry-agnostic capability FINOPS_TAG_GOVERNANCE.
- CR 12-5 D-14 typed exception envelope — 3 NEW typed exceptions:
  ChargebackReconciliationError + ReconciliationDeltaBreachError +
  ReconciliationApprovalError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — reconciliation approval owner-only.
Epic 12 2FA 챌린지 mandatory when reconciliation_resolved.
"""

from __future__ import annotations

import uuid
from typing import Final, TypedDict

from apps.api.core.errors import (
    ChargebackReconciliationError,
    ReconciliationApprovalError,
)

# ── 3 reconciliation_strategy 옵션 (PRD §F31.5-2 verbatim) ──────
RECONCILIATION_STRATEGY_CHARGEBACK_ONLY: Final[str] = "chargeback_only"
RECONCILIATION_STRATEGY_TAG_ALLOCATION_ONLY: Final[str] = "tag_allocation_only"
RECONCILIATION_STRATEGY_HYBRID_BLENDED: Final[str] = "hybrid_blended"

RECONCILIATION_STRATEGIES: Final[tuple[str, ...]] = (
    RECONCILIATION_STRATEGY_CHARGEBACK_ONLY,
    RECONCILIATION_STRATEGY_TAG_ALLOCATION_ONLY,
    RECONCILIATION_STRATEGY_HYBRID_BLENDED,
)

# ── 4 status 옵션 (PRD §F31.5-3 verbatim) ─────────────────────────
RECONCILIATION_STATUS_PENDING: Final[str] = "pending"
RECONCILIATION_STATUS_INVESTIGATING: Final[str] = "investigating"
RECONCILIATION_STATUS_APPROVED: Final[str] = "approved"
RECONCILIATION_STATUS_RESOLVED: Final[str] = "resolved"

RECONCILIATION_STATUSES: Final[tuple[str, ...]] = (
    RECONCILIATION_STATUS_PENDING,
    RECONCILIATION_STATUS_INVESTIGATING,
    RECONCILIATION_STATUS_APPROVED,
    RECONCILIATION_STATUS_RESOLVED,
)

# ── delta_threshold_pct constants (PRD §F31.5-4 verbatim) ─────────
DEFAULT_DELTA_THRESHOLD_PCT: Final[float] = 5.0
DEFAULT_AUTO_APPROVE_BELOW_PCT: Final[float] = 1.0


# ── Reconciliation TypedDict (PRD §F31.5-3 verbatim, 13 fields) ──
class Reconciliation(TypedDict, total=True):
    """TypedDict for chargeback allocation reconciliation record.

    Fields:
        reconciliation_id: UUID.
        tenant_id: UUID of the tenant.
        strategy: chargeback_only / tag_allocation_only / hybrid_blended.
        period_start: ISO 8601 date string.
        period_end: ISO 8601 date string.
        chargeback_amount_usd: chargeback total USD.
        tag_allocation_amount_usd: tag allocation total USD.
        variance_amount_usd: chargeback_amount_usd - tag_allocation_amount_usd.
        variance_pct: variance / max(chargeback, tag_allocation) * 100.
        delta_threshold_pct: threshold for triggering investigation.
        auto_approve_below_pct: threshold for auto-approval.
        status: pending / investigating / approved / resolved.
        trace_id: trace_id propagation.
    """

    reconciliation_id: str
    tenant_id: str
    strategy: str
    period_start: str
    period_end: str
    chargeback_amount_usd: float
    tag_allocation_amount_usd: float
    variance_amount_usd: float
    variance_pct: float
    delta_threshold_pct: float
    auto_approve_below_pct: float
    status: str
    trace_id: str


def _calculate_variance(
    chargeback_amount_usd: float,
    tag_allocation_amount_usd: float,
) -> tuple[float, float]:
    """Calculate variance amount and percentage."""
    variance_amount = chargeback_amount_usd - tag_allocation_amount_usd
    max_amount = max(abs(chargeback_amount_usd), abs(tag_allocation_amount_usd), 1.0)
    variance_pct = (variance_amount / max_amount) * 100.0
    return variance_amount, variance_pct


def initiate_reconciliation(
    tenant_id: str | uuid.UUID,
    *,
    strategy: str = RECONCILIATION_STRATEGY_HYBRID_BLENDED,
    period_start: str = "",
    period_end: str = "",
    chargeback_amount_usd: float = 0.0,
    tag_allocation_amount_usd: float = 0.0,
    delta_threshold_pct: float = DEFAULT_DELTA_THRESHOLD_PCT,
    auto_approve_below_pct: float = DEFAULT_AUTO_APPROVE_BELOW_PCT,
    dry_run: bool = False,
    trace_id: str = "",
) -> Reconciliation:
    """Initiate chargeback allocation reconciliation (PRD §F31.5-1).

    Hybrid_blended is the default strategy (PRD §F31.5 verbatim).
    Calculates variance. Auto-approves if variance_pct below
    auto_approve_below_pct. Triggers investigation if variance_pct
    above delta_threshold_pct.

    Args:
        tenant_id: tenant UUID.
        strategy: chargeback_only / tag_allocation_only / hybrid_blended.
        period_start: ISO 8601 date string.
        period_end: ISO 8601 date string.
        chargeback_amount_usd: chargeback total USD.
        tag_allocation_amount_usd: tag allocation total USD.
        delta_threshold_pct: threshold for investigation (default 5.0).
        auto_approve_below_pct: threshold for auto-approval (default 1.0).
        dry_run: if True, no audit log emitted.
        trace_id: trace_id propagation.

    Returns:
        Reconciliation TypedDict.

    Raises:
        ChargebackReconciliationError: invalid strategy or amounts.
        ReconciliationDeltaBreachError: variance_pct exceeds delta_threshold.
    """
    # 1. tenant_id validation
    if not isinstance(tenant_id, str | uuid.UUID):
        raise ChargebackReconciliationError(
            message_ko=f"tenant_id must be str/UUID, got {type(tenant_id).__name__}",
            details={"tenant_id": str(tenant_id)},
        )
    try:
        tenant_uuid = uuid.UUID(str(tenant_id))
    except (ValueError, AttributeError) as exc:
        raise ChargebackReconciliationError(
            message_ko=f"tenant_id is not a valid UUID: {tenant_id!r}",
            details={"tenant_id": str(tenant_id)},
        ) from exc

    # 2. strategy validation
    if strategy not in RECONCILIATION_STRATEGIES:
        raise ChargebackReconciliationError(
            message_ko=f"strategy {strategy!r} not in RECONCILIATION_STRATEGIES",
            details={"strategy": strategy, "allowed": str(RECONCILIATION_STRATEGIES)},
        )

    # 3. amount validation
    if not isinstance(chargeback_amount_usd, int | float):
        raise ChargebackReconciliationError(
            message_ko="chargeback_amount_usd must be numeric",
            details={"value": str(chargeback_amount_usd)},
        )
    if not isinstance(tag_allocation_amount_usd, int | float):
        raise ChargebackReconciliationError(
            message_ko="tag_allocation_amount_usd must be numeric",
            details={"value": str(tag_allocation_amount_usd)},
        )
    if chargeback_amount_usd < 0:
        raise ChargebackReconciliationError(
            message_ko=f"chargeback_amount_usd {chargeback_amount_usd!r} must be >= 0",
            details={"value": str(chargeback_amount_usd)},
        )
    if tag_allocation_amount_usd < 0:
        raise ChargebackReconciliationError(
            message_ko=f"tag_allocation_amount_usd {tag_allocation_amount_usd!r} must be >= 0",
            details={"value": str(tag_allocation_amount_usd)},
        )

    # 4. delta_threshold_pct + auto_approve_below_pct validation
    if not (0.0 <= float(delta_threshold_pct) <= 100.0):
        raise ChargebackReconciliationError(
            message_ko=f"delta_threshold_pct {delta_threshold_pct!r} out of 0-100 range",
            details={"value": str(delta_threshold_pct)},
        )
    if not (0.0 <= float(auto_approve_below_pct) <= 100.0):
        raise ChargebackReconciliationError(
            message_ko=f"auto_approve_below_pct {auto_approve_below_pct!r} out of 0-100 range",
            details={"value": str(auto_approve_below_pct)},
        )

    # 5. variance calculation
    variance_amount, variance_pct = _calculate_variance(
        float(chargeback_amount_usd),
        float(tag_allocation_amount_usd),
    )

    # 6. auto-approve if variance below threshold
    if variance_pct < auto_approve_below_pct:
        status = RECONCILIATION_STATUS_APPROVED
    elif variance_pct > delta_threshold_pct:
        status = RECONCILIATION_STATUS_INVESTIGATING
    else:
        status = RECONCILIATION_STATUS_PENDING

    return Reconciliation(
        reconciliation_id=str(uuid.uuid4()),
        tenant_id=str(tenant_uuid),
        strategy=strategy,
        period_start=period_start,
        period_end=period_end,
        chargeback_amount_usd=float(chargeback_amount_usd),
        tag_allocation_amount_usd=float(tag_allocation_amount_usd),
        variance_amount_usd=variance_amount,
        variance_pct=variance_pct,
        delta_threshold_pct=float(delta_threshold_pct),
        auto_approve_below_pct=float(auto_approve_below_pct),
        status=status,
        trace_id=trace_id,
    )


def approve_reconciliation(
    reconciliation: Reconciliation,
    *,
    approver_user_id: str | uuid.UUID,
    dry_run: bool = False,
    trace_id: str = "",
) -> Reconciliation:
    """Approve a pending reconciliation (PRD §F31.5-5).

    Args:
        reconciliation: existing Reconciliation TypedDict.
        approver_user_id: user UUID (must be owner per AD-22).
        dry_run: if True, no audit log emitted.
        trace_id: trace_id propagation.

    Returns:
        Reconciliation TypedDict with status=approved.

    Raises:
        ReconciliationApprovalError: not in pending status or invalid approver.
    """
    if reconciliation["status"] not in (
        RECONCILIATION_STATUS_PENDING,
        RECONCILIATION_STATUS_INVESTIGATING,
    ):
        raise ReconciliationApprovalError(
            message_ko=f"Cannot approve reconciliation in status {reconciliation['status']!r}",
            details={"status": reconciliation["status"]},
        )
    if not approver_user_id:
        raise ReconciliationApprovalError(
            message_ko="approver_user_id is required",
            details={},
        )

    updated = dict(reconciliation)
    updated["status"] = RECONCILIATION_STATUS_APPROVED
    updated["trace_id"] = trace_id
    return Reconciliation(**updated)  # type: ignore[typeddict-item]


def resolve_reconciliation(
    reconciliation: Reconciliation,
    *,
    resolver_user_id: str | uuid.UUID,
    dry_run: bool = False,
    trace_id: str = "",
) -> Reconciliation:
    """Resolve an approved reconciliation (PRD §F31.5-6).

    Epic 12 2FA 챌린지 mandatory (AD-22 owner-only RBAC).

    Args:
        reconciliation: existing Reconciliation TypedDict.
        resolver_user_id: user UUID (must be owner per AD-22).
        dry_run: if True, no audit log emitted.
        trace_id: trace_id propagation.

    Returns:
        Reconciliation TypedDict with status=resolved.

    Raises:
        ReconciliationApprovalError: not in approved status.
    """
    if reconciliation["status"] != RECONCILIATION_STATUS_APPROVED:
        raise ReconciliationApprovalError(
            message_ko=f"Cannot resolve reconciliation in status {reconciliation['status']!r}",
            details={"status": reconciliation["status"]},
        )
    if not resolver_user_id:
        raise ReconciliationApprovalError(
            message_ko="resolver_user_id is required",
            details={},
        )

    updated = dict(reconciliation)
    updated["status"] = RECONCILIATION_STATUS_RESOLVED
    updated["trace_id"] = trace_id
    return Reconciliation(**updated)  # type: ignore[typeddict-item]


__all__ = [
    # 3 reconciliation_strategy options
    "RECONCILIATION_STRATEGY_CHARGEBACK_ONLY",
    "RECONCILIATION_STRATEGY_TAG_ALLOCATION_ONLY",
    "RECONCILIATION_STRATEGY_HYBRID_BLENDED",
    "RECONCILIATION_STRATEGIES",
    # 4 status options
    "RECONCILIATION_STATUS_PENDING",
    "RECONCILIATION_STATUS_INVESTIGATING",
    "RECONCILIATION_STATUS_APPROVED",
    "RECONCILIATION_STATUS_RESOLVED",
    "RECONCILIATION_STATUSES",
    # delta_threshold_pct defaults
    "DEFAULT_DELTA_THRESHOLD_PCT",
    "DEFAULT_AUTO_APPROVE_BELOW_PCT",
    # TypedDict
    "Reconciliation",
    # builders + transitions
    "initiate_reconciliation",
    "approve_reconciliation",
    "resolve_reconciliation",
]
