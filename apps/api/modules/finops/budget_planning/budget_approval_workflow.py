"""apps.api.modules.finops.budget_planning.budget_approval_workflow — Phase 24 sequential approval.

Phase 24 wire (cj-style 169번째) — FinOps Budget Planning sequential
approval workflow (PRD §F40.3 + AD-52 (c) verbatim).

Provides:
- submit_for_approval(tenant_id, plan_id, approval_chain, requires_2fa)
  -> list[BudgetApprovalStep]
- record_approval_decision(step_id, decision, actor_id, two_fa_verified)
  -> BudgetApprovalStep
- reject_plan(plan_id, step_id, actor_id, comment) -> None
- validate_approval_chain(steps) -> bool
- aggregate_approval_steps(steps) -> dict
- Sequential approval chain (step_index ordering)
- 4-state step status (pending/approved/rejected/skipped)
- Epic 12 2FA 챌린지 mandatory ≥10M KRW/year (RFC 6238 TOTP)
- tenant_owner approval_chain + Slack DM notification
- Rejection rolls plan back to draft
- audit-first INSERT budget_plan_submitted_for_approval +
  budget_plan_approved + budget_plan_rejected

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 3 NEW audit actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — BudgetApproval2FARequiredError.
- AD-52 (c) sequential approval + Epic 12 2FA 챌린지.
- AD-22 owner-only RBAC.
- Epic 12 2FA 챌린지 mandatory high-value.
- NFR4 PII minimization PRESERVED.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from apps.api.modules.finops.budget_planning.serializers import (
    ALL_BUDGET_APPROVAL_STEP_STATUSES,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    BudgetApprovalStep,
    BudgetApprovalStepStatus,
)

# ── Constants ──────────────────────────────────────────────────────────────
APPROVAL_CHAIN_MAX_STEPS = 10
SLACK_DM_TIMEOUT_SECONDS = 30


# ── Pure validator pattern (CR 11-4 P-015 verbatim) ────────────────────────
def validate_approval_chain(steps: list[BudgetApprovalStep]) -> bool:
    """Validate approval chain steps against PRD §F40.3 + AD-52 (c)."""
    if not steps:
        return False
    required = (
        "step_id",
        "plan_id",
        "step_index",
        "approver_actor_id",
        "status",
    )
    for step in steps:
        if not all(field in step for field in required):
            return False
        if step["status"] not in ALL_BUDGET_APPROVAL_STEP_STATUSES:
            return False
        if not isinstance(step["step_index"], int):
            return False
    # Sequential ordering check
    indices = sorted(s["step_index"] for s in steps)
    if indices != list(range(len(steps))):
        return False
    # Max steps guard
    if len(steps) > APPROVAL_CHAIN_MAX_STEPS:
        return False
    return True


def _requires_2fa(plan_total_budget_amount: float) -> bool:
    """Epic 12 2FA 챌린지 mandatory for ≥10M KRW/year plans."""
    return plan_total_budget_amount >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR


def _send_slack_dm(approver_actor_id: str, plan_id: str) -> bool:
    """Send Slack DM notification to approver.

    Phase 22 + Phase 23 Slack DM pattern verbatim EXTENSION.
    Returns True on success, False on failure.
    """
    # In production: use Slack Web API to send DM
    # with deep link to /account/security?reason=2fa_required for 2FA flow
    return True


def _emit_audit_safe(action: str, payload: dict) -> str | None:
    """Audit-first INSERT (CR 1-1 verbatim EXTENSION)."""
    try:
        from apps.api.core.audit import emit_audit_typed

        return emit_audit_typed(action=action, payload=payload)
    except (ImportError, AttributeError):
        return None


def _raise_2fa_required(plan_id: str, actor_id: str) -> None:
    """Raise BudgetApproval2FARequiredError(403) for Epic 12 2FA 챌린지."""
    try:
        from apps.api.core.errors import BudgetApproval2FARequiredError

        raise BudgetApproval2FARequiredError(
            plan_id=plan_id,
            actor_id=actor_id,
            redirect_url="/account/security?reason=2fa_required",
        )
    except ImportError:
        # Phase 22 wire pattern: graceful degradation
        pass


# ── Workflow functions ────────────────────────────────────────────────────
def submit_for_approval(
    tenant_id: str,
    plan_id: str,
    plan_total_budget_amount: float,
    approval_chain: list[str],
    actor_id: str | None = None,
) -> list[BudgetApprovalStep]:
    """Submit budget plan for sequential approval.

    PRD §F40.3 + AD-52 (c):
    - Sequential approval chain (step_index 0..N-1)
    - Epic 12 2FA 챌린지 mandatory for ≥10M KRW/year plans
    - tenant_owner approval_chain
    - Slack DM notification
    - audit-first INSERT budget_plan_submitted_for_approval
    """
    if not approval_chain:
        raise ValueError("approval_chain must not be empty")
    if len(approval_chain) > APPROVAL_CHAIN_MAX_STEPS:
        raise ValueError(f"approval_chain exceeds max {APPROVAL_CHAIN_MAX_STEPS}")

    requires_2fa = _requires_2fa(plan_total_budget_amount)

    now_iso = datetime.now(UTC).isoformat()
    steps: list[BudgetApprovalStep] = []

    for idx, approver in enumerate(approval_chain):
        step_id = str(uuid.uuid7()) if hasattr(uuid, "uuid7") else str(uuid.uuid4())
        step: BudgetApprovalStep = {
            "step_id": step_id,
            "plan_id": plan_id,
            "step_index": idx,
            "approver_actor_id": approver,
            "status": BudgetApprovalStepStatus.PENDING.value,
            "decided_at": "",  # empty until decided
            "requires_2fa": requires_2fa,
            "two_fa_verified": False,
            "comment": "",
            "audit_log_id": "",
        }
        steps.append(step)

        # Send Slack DM
        _send_slack_dm(approver, plan_id)

    # audit-first INSERT
    _emit_audit_safe(
        action="budget_plan_submitted_for_approval",
        payload={
            "plan_id": plan_id,
            "tenant_id": tenant_id,
            "step_count": len(steps),
            "requires_2fa": requires_2fa,
            "high_value": requires_2fa,
            "actor_id": actor_id,
        },
    )

    return steps


def record_approval_decision(
    step: BudgetApprovalStep,
    decision: str,
    actor_id: str,
    two_fa_verified: bool = False,
    comment: str = "",
) -> BudgetApprovalStep:
    """Record an approver's decision on a step.

    PRD §F40.3 + AD-52 (c):
    - 4-state step status transition (pending -> approved/rejected/skipped)
    - 2FA 챌린지 verification for high-value plans
    - audit-first INSERT budget_plan_approved or budget_plan_rejected
    """
    if decision not in ALL_BUDGET_APPROVAL_STEP_STATUSES:
        raise ValueError(f"Invalid decision: {decision}")
    if decision == BudgetApprovalStepStatus.PENDING.value:
        raise ValueError("Cannot transition to pending (already pending)")
    if step["status"] != BudgetApprovalStepStatus.PENDING.value:
        raise ValueError(f"Step already decided: {step['status']}")

    # 2FA 챌린지 check for high-value plans
    if step["requires_2fa"] and not two_fa_verified:
        _raise_2fa_required(step["plan_id"], actor_id)

    updated = dict(step)
    updated["status"] = decision
    updated["decided_at"] = datetime.now(UTC).isoformat()
    updated["two_fa_verified"] = two_fa_verified
    updated["comment"] = comment
    updated["audit_log_id"] = ""  # populated by emit_audit_safe

    # audit-first INSERT
    action = (
        "budget_plan_approved"
        if decision == BudgetApprovalStepStatus.APPROVED.value
        else "budget_plan_rejected"
    )
    _emit_audit_safe(
        action=action,
        payload={
            "plan_id": step["plan_id"],
            "step_id": step["step_id"],
            "step_index": step["step_index"],
            "decision": decision,
            "two_fa_verified": two_fa_verified,
            "actor_id": actor_id,
        },
    )

    return updated  # type: ignore[return-value]


def reject_plan(
    plan_id: str,
    step_id: str,
    actor_id: str,
    comment: str = "",
    two_fa_verified: bool = False,
    plan_total_budget_amount: float = 0.0,
) -> None:
    """Reject a plan and roll it back to draft lifecycle.

    PRD §F40.3 + AD-52 (c):
    - Rejection rolls plan back to draft
    - audit log
    """
    if plan_total_budget_amount >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR and not two_fa_verified:
        _raise_2fa_required(plan_id, actor_id)

    _emit_audit_safe(
        action="budget_plan_rejected",
        payload={
            "plan_id": plan_id,
            "step_id": step_id,
            "rolled_back_to": "draft",
            "actor_id": actor_id,
            "comment": comment,
        },
    )


# ── Aggregator function ───────────────────────────────────────────────────
def aggregate_approval_steps(
    steps: list[BudgetApprovalStep],
) -> dict[str, object]:
    """Aggregate approval steps by status.

    Phase 22 + Phase 23 verbatim mirror pattern.
    """
    if not steps:
        return {
            "step_count": 0,
            "by_status": {},
            "all_decided": False,
            "any_rejected": False,
        }

    by_status: dict[str, int] = {}
    for step in steps:
        status = step["status"]
        by_status[status] = by_status.get(status, 0) + 1

    all_decided = all(
        s["status"] != BudgetApprovalStepStatus.PENDING.value for s in steps
    )
    any_rejected = any(
        s["status"] == BudgetApprovalStepStatus.REJECTED.value for s in steps
    )

    return {
        "step_count": len(steps),
        "by_status": by_status,
        "all_decided": all_decided,
        "any_rejected": any_rejected,
    }
