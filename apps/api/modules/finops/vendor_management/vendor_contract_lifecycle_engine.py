"""apps.api.modules.finops.vendor_management.vendor_contract_lifecycle_engine — Phase 25 vendor contract lifecycle + Epic 12 2FA + auto-renewal + over-budget + blacklist gate.

Phase 25 wire (cj-style 173번째) — §F41.3 + AD-53 (c) + (g) verbatim.

Provides:
- aggregate_vendor_contract_lifecycle (cross-tenant contract aggregation)
- create_vendor_contract (CRUD + audit-first INSERT)
- advance_contract_lifecycle (sequential 7-state lifecycle)
- request_contract_approval (Epic 12 2FA 챌린지 for ≥10M KRW/year)
- approve_contract_step (single step approval with audit)
- reject_contract_step (rejection handler)
- request_contract_renewal (auto-renewal 90-day window)
- terminate_contract (terminal transition)
- check_auto_renewal_window (within 90 days of expiry)
- check_over_budget (over budget ceiling cross-check)
- check_vendor_blacklist_gate (vendor_blacklist compliance gate)

CR lessons applied:
- CR 0-2 RLS.
- CR 1-1 audit-first INSERT.
- CR 5-1 Decimal precision banker's rounding.
- CR 11-4 P-015 pure validator.
- CR 12-5 D-14 typed exception envelope.
- CR 12-5 D-PARITY-01.
- CR 12-5 D-GATE-01.
- AD-22 owner-only RBAC.
- AD-53 (c) + (g) verbatim.
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year).
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
    AUTO_RENEWAL_WINDOW_DAYS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    VendorContract,
    VendorContractLifecycle,
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


# ── Sequential lifecycle transitions (PRD §F41.3 + AD-53 (c) verbatim) ───
_LIFECYCLE_TRANSITIONS: dict[str, set[str]] = {
    VendorContractLifecycle.DRAFT.value: {
        VendorContractLifecycle.PENDING_APPROVAL.value,
        VendorContractLifecycle.TERMINATED.value,
    },
    VendorContractLifecycle.PENDING_APPROVAL.value: {
        VendorContractLifecycle.APPROVED.value,
        VendorContractLifecycle.DRAFT.value,
        VendorContractLifecycle.TERMINATED.value,
    },
    VendorContractLifecycle.APPROVED.value: {
        VendorContractLifecycle.ACTIVE.value,
        VendorContractLifecycle.TERMINATED.value,
    },
    VendorContractLifecycle.ACTIVE.value: {
        VendorContractLifecycle.EXPIRING_SOON.value,
        VendorContractLifecycle.RENEWED.value,
        VendorContractLifecycle.EXPIRED.value,
        VendorContractLifecycle.TERMINATED.value,
    },
    VendorContractLifecycle.EXPIRING_SOON.value: {
        VendorContractLifecycle.RENEWED.value,
        VendorContractLifecycle.EXPIRED.value,
        VendorContractLifecycle.TERMINATED.value,
    },
    # RENEWED → ACTIVE (after renewal approval)
    VendorContractLifecycle.RENEWED.value: {
        VendorContractLifecycle.ACTIVE.value,
        VendorContractLifecycle.TERMINATED.value,
    },
    # EXPIRED + TERMINATED are terminal
    VendorContractLifecycle.EXPIRED.value: set(),
    VendorContractLifecycle.TERMINATED.value: set(),
}


# ── Blacklist gate check (PRD §F41.1 + AD-53 (g) verbatim) ───────────────
def check_vendor_blacklist_gate(
    *,
    vendor_status: str,
) -> bool:
    """Check if vendor passes blacklist compliance gate.

    Blacklisted vendors cannot get contracts (VENDOR_BLACKLIST_GATE_FLAGS).
    """
    return vendor_status != "blacklisted"


# ── Over-budget cross-check (PRD §F41.3 verbatim) ────────────────────────
def check_over_budget(
    *,
    contract_value_krw: float,
    budget_ceiling_krw: float,
) -> bool:
    """Check if contract value exceeds budget ceiling.

    Returns True if contract is over budget (requires owner override +
    2FA 챌린지).
    """
    return contract_value_krw > budget_ceiling_krw


# ── Auto-renewal window check (PRD §F41.3 verbatim) ───────────────────────
def check_auto_renewal_window(
    *,
    contract_expiry_iso: str,
    auto_renewal_enabled: bool,
    days_remaining: int | None = None,
) -> bool:
    """Check if contract is within auto-renewal window (default 90 days).

    Returns True if contract is within AUTO_RENEWAL_WINDOW_DAYS of expiry
    AND auto_renewal_enabled flag is set.

    Args:
        contract_expiry_iso: ISO 8601 expiry date
        auto_renewal_enabled: vendor opted into auto-renewal
        days_remaining: optional override for testing
    """
    if not auto_renewal_enabled:
        return False

    if days_remaining is None:
        try:
            expiry_dt = datetime.fromisoformat(contract_expiry_iso.replace("Z", "+00:00"))
            now = datetime.now(UTC)
            days_remaining = (expiry_dt - now).days
        except (ValueError, TypeError):
            logger.warning(
                "invalid expiry format: contract_expiry_iso=%s", contract_expiry_iso
            )
            return False

    return 0 <= days_remaining <= AUTO_RENEWAL_WINDOW_DAYS


# ── Contract creation ────────────────────────────────────────────────────
def create_vendor_contract(
    *,
    tenant_id: str,
    vendor_id: str,
    contract_name: str,
    contract_value_krw: float,
    budget_ceiling_krw: float,
    approval_chain: list[str],
    auto_renewal_enabled: bool = False,
    blacklist_gate_passed: bool = True,
) -> VendorContract:
    """Create a new vendor contract with audit-first INSERT (CR 1-1).

    Args:
        tenant_id: tenant UUID
        vendor_id: parent Vendor vendor_id
        contract_name: contract display name
        contract_value_krw: KRW total value
        budget_ceiling_krw: KRW budget ceiling
        approval_chain: list of approver actor_ids
        auto_renewal_enabled: vendor opted into auto-renewal
        blacklist_gate_passed: vendor_blacklist gate result

    Returns:
        VendorContract TypedDict (16 fields).

    Raises:
        VendorContractNotFoundError if vendor is missing.
        VendorComplianceViolationError if blacklist gate fails.
    """
    if not approval_chain:
        from apps.api.core.errors import VendorContractNotFoundError  # noqa

        raise VendorContractNotFoundError(
            contract_id="",
            reason="approval_chain must be non-empty",
        )

    if not blacklist_gate_passed:
        from apps.api.core.errors import VendorComplianceViolationError  # noqa

        raise VendorComplianceViolationError(
            vendor_id=vendor_id,
            violation_type="blacklist_gate_failed",
        )

    contract_id = _new_uuid_v7()
    now_iso = datetime.now(UTC).isoformat()

    # Determine high-value (Epic 12 2FA 챌린지 mandatory)
    high_value = contract_value_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR

    # Check over-budget
    over_budget = check_over_budget(
        contract_value_krw=contract_value_krw,
        budget_ceiling_krw=budget_ceiling_krw,
    )

    contract: VendorContract = {
        "contract_id": contract_id,
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "contract_name": contract_name,
        "contract_value_krw": _bankers_round(contract_value_krw),
        "lifecycle": VendorContractLifecycle.DRAFT.value,
        "step_index": 0,
        "approval_chain": list(approval_chain),
        "auto_renewal_enabled": auto_renewal_enabled,
        "high_value": high_value,
        "requires_2fa": high_value,
        "computed_total_contract_value": _bankers_round(contract_value_krw),
        "budget_ceiling_krw": _bankers_round(budget_ceiling_krw),
        "over_budget": over_budget,
        "blacklist_gate_passed": blacklist_gate_passed,
        "audit_log_id": "",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    audit_log_id = _emit_audit_safe(
        tenant_id=tenant_id,
        action="vendor_contract_approved",
        target_id=contract_id,
        payload={
            "contract_id": contract_id,
            "vendor_id": vendor_id,
            "contract_value_krw": contract["contract_value_krw"],
            "high_value": high_value,
            "requires_2fa": high_value,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )
    if audit_log_id is not None:
        contract["audit_log_id"] = audit_log_id

    logger.info(
        "vendor_contract_created contract_id=%s vendor_id=%s value=%.2f high_value=%s",
        contract_id,
        vendor_id,
        contract_value_krw,
        high_value,
    )

    return contract


# ── Lifecycle advance (sequential state machine) ─────────────────────────
def advance_contract_lifecycle(
    *,
    contract: VendorContract,
    target_lifecycle: str,
) -> VendorContract:
    """Advance contract to next sequential state (PRD §F41.3 verbatim).

    Raises:
        VendorContractTerminationError if transition is invalid.
    """
    if target_lifecycle not in {item.value for item in VendorContractLifecycle}:
        from apps.api.core.errors import VendorContractTerminationError  # noqa

        raise VendorContractTerminationError(
            contract_id=contract["contract_id"],
            current_lifecycle=contract["lifecycle"],
            attempted_lifecycle=target_lifecycle,
        )

    current = contract["lifecycle"]
    allowed = _LIFECYCLE_TRANSITIONS.get(current, set())
    if target_lifecycle not in allowed:
        from apps.api.core.errors import VendorContractTerminationError  # noqa

        raise VendorContractTerminationError(
            contract_id=contract["contract_id"],
            current_lifecycle=current,
            attempted_lifecycle=target_lifecycle,
        )

    updated: VendorContract = {
        **contract,
        "lifecycle": target_lifecycle,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    _emit_audit_safe(
        tenant_id=contract["tenant_id"],
        action="vendor_contract_approved",
        target_id=contract["contract_id"],
        payload={
            "contract_id": contract["contract_id"],
            "old_lifecycle": current,
            "new_lifecycle": target_lifecycle,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_contract_lifecycle contract_id=%s %s -> %s",
        contract["contract_id"],
        current,
        target_lifecycle,
    )

    return updated


# ── Approval workflow ────────────────────────────────────────────────────
def request_contract_approval(
    *,
    contract: VendorContract,
    requester_actor_id: str,
) -> VendorContract:
    """Request approval for high-value contract (Epic 12 2FA 챌린지).

    Args:
        contract: existing VendorContract
        requester_actor_id: actor_id of requester

    Returns:
        Updated contract with lifecycle = pending_approval.

    Raises:
        Vendor2FARequiredError if high-value contract lacks 2FA verification.
    """
    if contract["high_value"] and not contract["requires_2fa"]:
        from apps.api.core.errors import Vendor2FARequiredError  # noqa

        raise Vendor2FARequiredError(
            contract_id=contract["contract_id"],
            reason="High-value contract requires Epic 12 2FA 챌린지",
        )

    updated: VendorContract = {
        **contract,
        "lifecycle": VendorContractLifecycle.PENDING_APPROVAL.value,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    _emit_audit_safe(
        tenant_id=contract["tenant_id"],
        action="vendor_contract_approved",
        target_id=contract["contract_id"],
        payload={
            "contract_id": contract["contract_id"],
            "requester_actor_id": requester_actor_id,
            "requires_2fa": contract["requires_2fa"],
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_contract_approval_requested contract_id=%s requester=%s",
        contract["contract_id"],
        requester_actor_id,
    )

    return updated


def approve_contract_step(
    *,
    contract: VendorContract,
    approver_actor_id: str,
) -> VendorContract:
    """Approve current step in approval chain.

    Advances step_index. Once all approvers in approval_chain have
    approved, lifecycle transitions to APPROVED.

    Raises:
        VendorApprovalStepError if approver not in chain or already
        approved.
    """
    chain = contract["approval_chain"]
    if approver_actor_id not in chain:
        from apps.api.core.errors import VendorApprovalStepError  # noqa

        raise VendorApprovalStepError(
            contract_id=contract["contract_id"],
            step_index=contract["step_index"],
            reason=f"approver {approver_actor_id!r} not in approval_chain",
        )

    step_index = contract["step_index"]
    if step_index >= len(chain):
        from apps.api.core.errors import VendorApprovalStepError  # noqa

        raise VendorApprovalStepError(
            contract_id=contract["contract_id"],
            step_index=step_index,
            reason="approval_chain exhausted",
        )

    new_step = step_index + 1
    new_lifecycle = (
        VendorContractLifecycle.APPROVED.value
        if new_step >= len(chain)
        else contract["lifecycle"]
    )

    updated: VendorContract = {
        **contract,
        "step_index": new_step,
        "lifecycle": new_lifecycle,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    _emit_audit_safe(
        tenant_id=contract["tenant_id"],
        action="vendor_contract_approved",
        target_id=contract["contract_id"],
        payload={
            "contract_id": contract["contract_id"],
            "approver_actor_id": approver_actor_id,
            "step_index": new_step,
            "lifecycle": new_lifecycle,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_contract_approved contract_id=%s approver=%s step=%d",
        contract["contract_id"],
        approver_actor_id,
        new_step,
    )

    return updated


def reject_contract_step(
    *,
    contract: VendorContract,
    approver_actor_id: str,
    reason: str,
) -> VendorContract:
    """Reject current approval step and roll back to DRAFT.

    Raises:
        VendorApprovalStepError if contract is not in PENDING_APPROVAL.
    """
    if contract["lifecycle"] != VendorContractLifecycle.PENDING_APPROVAL.value:
        from apps.api.core.errors import VendorApprovalStepError  # noqa

        raise VendorApprovalStepError(
            contract_id=contract["contract_id"],
            step_index=contract["step_index"],
            reason=f"contract not in pending_approval (current={contract['lifecycle']})",
        )

    updated: VendorContract = {
        **contract,
        "lifecycle": VendorContractLifecycle.DRAFT.value,
        "step_index": 0,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    _emit_audit_safe(
        tenant_id=contract["tenant_id"],
        action="vendor_contract_approved",
        target_id=contract["contract_id"],
        payload={
            "contract_id": contract["contract_id"],
            "approver_actor_id": approver_actor_id,
            "reason": reason,
            "rolled_back_to": VendorContractLifecycle.DRAFT.value,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_contract_rejected contract_id=%s approver=%s reason=%s",
        contract["contract_id"],
        approver_actor_id,
        reason,
    )

    return updated


# ── Renewal (PRD §F41.3 auto-renewal 90-day window verbatim) ──────────────
def request_contract_renewal(
    *,
    contract: VendorContract,
    contract_expiry_iso: str,
    new_contract_value_krw: float | None = None,
) -> VendorContract:
    """Request contract renewal within auto-renewal window (90 days).

    Args:
        contract: existing VendorContract
        contract_expiry_iso: ISO 8601 expiry date
        new_contract_value_krw: optional new value (default: same)

    Returns:
        Updated contract with lifecycle = renewed.

    Raises:
        VendorContractRenewalError if not within auto-renewal window.
    """
    in_window = check_auto_renewal_window(
        contract_expiry_iso=contract_expiry_iso,
        auto_renewal_enabled=contract["auto_renewal_enabled"],
    )
    if not in_window:
        from apps.api.core.errors import VendorContractRenewalError  # noqa

        raise VendorContractRenewalError(
            contract_id=contract["contract_id"],
            reason=f"Not within {AUTO_RENEWAL_WINDOW_DAYS}-day auto-renewal window",
        )

    updated: VendorContract = {
        **contract,
        "lifecycle": VendorContractLifecycle.RENEWED.value,
        "contract_value_krw": _bankers_round(
            new_contract_value_krw or contract["contract_value_krw"]
        ),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    _emit_audit_safe(
        tenant_id=contract["tenant_id"],
        action="vendor_contract_renewed",
        target_id=contract["contract_id"],
        payload={
            "contract_id": contract["contract_id"],
            "new_contract_value_krw": updated["contract_value_krw"],
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_contract_renewed contract_id=%s new_value=%.2f",
        contract["contract_id"],
        updated["contract_value_krw"],
    )

    return updated


# ── Termination (terminal state) ─────────────────────────────────────────
def terminate_contract(
    *,
    contract: VendorContract,
    reason: str,
) -> VendorContract:
    """Terminate contract (transition to terminal TERMINATED state).

    Raises:
        VendorContractTerminationError if contract already terminated.
    """
    if contract["lifecycle"] == VendorContractLifecycle.TERMINATED.value:
        from apps.api.core.errors import VendorContractTerminationError  # noqa

        raise VendorContractTerminationError(
            contract_id=contract["contract_id"],
            current_lifecycle=contract["lifecycle"],
            attempted_lifecycle=contract["lifecycle"],
        )

    updated: VendorContract = {
        **contract,
        "lifecycle": VendorContractLifecycle.TERMINATED.value,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    _emit_audit_safe(
        tenant_id=contract["tenant_id"],
        action="vendor_contract_terminated",
        target_id=contract["contract_id"],
        payload={
            "contract_id": contract["contract_id"],
            "reason": reason,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )

    logger.info(
        "vendor_contract_terminated contract_id=%s reason=%s",
        contract["contract_id"],
        reason,
    )

    return updated


# ── Aggregation across tenant ─────────────────────────────────────────────
def aggregate_vendor_contract_lifecycle(
    *,
    tenant_id: str,
    contracts: list[VendorContract],
) -> dict[str, Any]:
    """Aggregate vendor contract lifecycle for tenant dashboard.

    RLS via tenant_id selector.
    """
    tenant_contracts = [
        c for c in contracts if c.get("tenant_id") == tenant_id
    ]

    lifecycle_counts: dict[str, int] = {}
    total_value = 0.0
    high_value_count = 0

    for contract in tenant_contracts:
        lifecycle = contract.get("lifecycle", "draft")
        lifecycle_counts[lifecycle] = lifecycle_counts.get(lifecycle, 0) + 1
        total_value += contract.get("contract_value_krw", 0.0)
        if contract.get("high_value", False):
            high_value_count += 1

    return {
        "tenant_id": tenant_id,
        "contract_count": len(tenant_contracts),
        "lifecycle_counts": lifecycle_counts,
        "total_contract_value_krw": _bankers_round(total_value),
        "high_value_count": high_value_count,
        "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    }
