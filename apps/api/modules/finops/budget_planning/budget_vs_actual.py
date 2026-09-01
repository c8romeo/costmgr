"""apps.api.modules.finops.budget_planning.budget_vs_actual — Phase 24 variance computation.

Phase 24 wire (cj-style 169번째) — FinOps Budget Planning budget vs
actual variance computation (PRD §F40.4 + AD-52 (d) verbatim).

Provides:
- compute_budget_vs_actual(tenant_id, plan_id, period_key)
  -> list[BudgetVsActual]
- validate_budget_vs_actual(rows) -> bool
- aggregate_budget_vs_actual(rows) -> dict
- JOIN Phase 22 settlement_results.total_settlement_amount (actuals)
  on Phase 24 BudgetPlan.total_budget_amount (plan)
  via (tenant_id, period_key, dimension)
- variance_amount = budget_allocation - actual_allocation
- variance_pct = variance_amount / budget_allocation
- over-budget detection: warning ≥10% / critical ≥25%
- audit-first INSERT budget_alert_triggered on over-budget

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — budget_alert_triggered.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-4 P-015 — pure validator pattern.
- AD-52 (d) budget_vs_actual + dashboard UI detail.
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal

from apps.api.modules.finops.budget_planning.serializers import (
    ALL_BUDGET_ALERT_SEVERITIES,
    BUDGET_CRITICAL_THRESHOLD_PCT,
    BUDGET_PLANNING_DEFAULTS,
    BUDGET_WARNING_THRESHOLD_PCT,
    BudgetAlertSeverity,
    BudgetAllocationLine,
    BudgetPlan,
    BudgetVsActual,
)

# ── Constants ──────────────────────────────────────────────────────────────
BUDGET_VS_ACTUAL_AMOUNT_QUANTUM = Decimal("0.01")
BUDGET_VS_ACTUAL_PCT_QUANTUM = Decimal("0.01")


# ── Pure validator pattern (CR 11-4 P-015 verbatim) ────────────────────────
def validate_budget_vs_actual(rows: list[BudgetVsActual]) -> bool:
    """Validate variance rows against PRD §F40.4 + AD-52 (d)."""
    if not rows:
        return False
    required = (
        "variance_id",
        "plan_id",
        "tenant_id",
        "period_key",
        "dimension",
        "budget_amount",
        "actual_amount",
        "variance_amount",
        "variance_pct",
        "severity",
    )
    for row in rows:
        if not all(field in row for field in required):
            return False
        if row["severity"] not in ALL_BUDGET_ALERT_SEVERITIES and row["severity"] != "ok":
            return False
    return True


def _bankers_round_pct(pct: float) -> float:
    """CR 5-1 verbatim banker's rounding on percentage."""
    d = Decimal(str(pct)).quantize(BUDGET_VS_ACTUAL_PCT_QUANTUM, rounding=ROUND_HALF_EVEN)
    return float(d)


def _bankers_round_amount(amount: float) -> float:
    """CR 5-1 verbatim banker's rounding on amount."""
    d = Decimal(str(amount)).quantize(BUDGET_VS_ACTUAL_AMOUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    return float(d)


def _severity_from_pct(variance_pct: float) -> str:
    """Determine severity from variance percentage (PRD §F40.5 verbatim).

    variance_pct > 0 means over budget.
    warning ≥10%, critical ≥25%, escalated for both.
    """
    if variance_pct >= BUDGET_CRITICAL_THRESHOLD_PCT:
        return BudgetAlertSeverity.CRITICAL.value
    if variance_pct >= BUDGET_WARNING_THRESHOLD_PCT:
        return BudgetAlertSeverity.WARNING.value
    return "ok"


def _emit_audit_safe(action: str, payload: dict) -> str | None:
    """Audit-first INSERT (CR 1-1 verbatim EXTENSION)."""
    try:
        from apps.api.core.audit import emit_audit_typed

        return emit_audit_typed(action=action, payload=payload)
    except (ImportError, AttributeError):
        return None


# ── Main variance computation function ────────────────────────────────────
def compute_budget_vs_actual(
    tenant_id: str,
    plan: BudgetPlan,
    allocations: list[BudgetAllocationLine],
    actual_amounts: dict[str, float],
    actor_id: str | None = None,
) -> list[BudgetVsActual]:
    """Compute budget vs actual variance per dimension.

    PRD §F40.4 + AD-52 (d):
    - JOIN Phase 22 settlement_results.total_settlement_amount (actuals)
      on Phase 24 BudgetPlan.total_budget_amount (plan)
      via (tenant_id, period_key, dimension)
    - variance_amount = budget_allocation - actual_allocation
    - variance_pct = variance_amount / budget_allocation
    - over-budget detection: warning 10% + critical 25%
    - audit-first INSERT budget_alert_triggered
    """
    now_iso = datetime.now(UTC).isoformat()
    rows: list[BudgetVsActual] = []

    for alloc in allocations:
        dim_key = f"{alloc['dimension']}:{alloc['dimension_value']}"
        budget_amount = alloc["allocated_amount"]
        actual_amount = actual_amounts.get(dim_key, 0.0)

        variance_amount = budget_amount - actual_amount
        # Guard against zero budget
        variance_pct = 0.0 if budget_amount == 0 else variance_amount / budget_amount * 100.0

        variance_pct = _bankers_round_pct(variance_pct)
        variance_amount = _bankers_round_amount(variance_amount)
        severity = _severity_from_pct(variance_pct)
        over_budget = severity != "ok"

        variance_id = str(uuid.uuid7()) if hasattr(uuid, "uuid7") else str(uuid.uuid4())

        row: BudgetVsActual = {
            "variance_id": variance_id,
            "plan_id": plan["plan_id"],
            "tenant_id": tenant_id,
            "period_key": plan["period_key"],
            "dimension": alloc["dimension"],
            "dimension_value": alloc["dimension_value"],
            "budget_amount": budget_amount,
            "actual_amount": actual_amount,
            "variance_amount": variance_amount,
            "variance_pct": variance_pct,
            "severity": severity,
            "source_attribution": {
                "phase_22_settlement_results_ref": True,
                "phase_24_budget_plan_ref": True,
                "derivation_model_version": BUDGET_PLANNING_DEFAULTS["model_version"],
            },
            "computed_at": now_iso,
            "over_budget": over_budget,
            "escalation_chain_id": "",
            "audit_log_id": "",
        }
        rows.append(row)

        # audit-first INSERT on over-budget
        if over_budget:
            _emit_audit_safe(
                action="budget_alert_triggered",
                payload={
                    "plan_id": plan["plan_id"],
                    "tenant_id": tenant_id,
                    "variance_id": variance_id,
                    "dimension": alloc["dimension"],
                    "dimension_value": alloc["dimension_value"],
                    "variance_pct": variance_pct,
                    "severity": severity,
                    "actor_id": actor_id,
                },
            )

    return rows


# ── Aggregator function ───────────────────────────────────────────────────
def aggregate_budget_vs_actual(
    rows: list[BudgetVsActual],
) -> dict[str, object]:
    """Aggregate variance rows.

    Phase 22 + Phase 23 verbatim mirror pattern.
    """
    if not rows:
        return {
            "row_count": 0,
            "total_budget": 0.0,
            "total_actual": 0.0,
            "total_variance": 0.0,
            "over_budget_count": 0,
            "by_severity": {},
        }

    total_budget = sum(r["budget_amount"] for r in rows)
    total_actual = sum(r["actual_amount"] for r in rows)
    total_variance = sum(r["variance_amount"] for r in rows)
    over_budget_count = sum(1 for r in rows if r["over_budget"])

    by_severity: dict[str, int] = {}
    for r in rows:
        sev = r["severity"]
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "row_count": len(rows),
        "total_budget": _bankers_round_amount(total_budget),
        "total_actual": _bankers_round_amount(total_actual),
        "total_variance": _bankers_round_amount(total_variance),
        "over_budget_count": over_budget_count,
        "by_severity": by_severity,
    }
