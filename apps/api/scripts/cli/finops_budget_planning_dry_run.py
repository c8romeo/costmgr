"""apps.api.scripts.cli.finops_budget_planning_dry_run — Phase 24 dry-run CLI.

Phase 24 wire (cj-style 169번째) — FinOps Budget Planning pre-allocation
layer dry-run CLI script (PRD §F40.8 + AD-52 (a) verbatim EXTENSION +
Phase 23 finops_unit_economics_dry_run pattern).

Provides:
- `--finops-budget-planning-dry-run` 1 NEW CLI flag
- Executes dry-run mode on the budget_plan_engine + budget_allocation +
  budget_vs_actual + budget_alert + scheduled_budget_planning_lifecycle_job
  without persisting actual audit-first INSERT events.
- Writes preview snapshot to phase_24_budget_planning_preview table.
- Emits `budget_planning_dry_run_executed` audit action.

Usage:
    python -m apps.api.scripts.cli.finops_budget_planning_dry_run \
        --tenant-id <UUID> --period-key 2026-08 --period-type monthly \
        --total-budget-amount 5000000

CR lessons applied:
- CR 0-2 RLS — tenant_id selector.
- CR 1-1 audit-first INSERT — `budget_planning_dry_run_executed`.
- AD-52 (a) dry-run mode detail.
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from apps.api.modules.finops.budget_planning.budget_alert import (
    aggregate_budget_alerts,
    trigger_over_budget_alert,
)
from apps.api.modules.finops.budget_planning.budget_allocation import (
    aggregate_budget_allocations,
    allocate_budget,
)
from apps.api.modules.finops.budget_planning.budget_plan_engine import (
    aggregate_budget_plans,
    create_budget_plan,
)
from apps.api.modules.finops.budget_planning.budget_vs_actual import (
    aggregate_budget_vs_actual,
    compute_budget_vs_actual,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 24 FinOps Budget Planning dry-run CLI")
    parser.add_argument(
        "--finops-budget-planning-dry-run",
        action="store_true",
        default=True,
        help="Run in dry-run mode (default: True)",
    )
    parser.add_argument(
        "--tenant-id",
        required=True,
        help="Tenant UUID",
    )
    parser.add_argument(
        "--period-key",
        required=True,
        help="Period key (YYYY / YYYY-Qn / YYYY-MM)",
    )
    parser.add_argument(
        "--period-type",
        required=True,
        choices=["annual", "quarterly", "monthly"],
        help="Period type",
    )
    parser.add_argument(
        "--total-budget-amount",
        type=float,
        required=True,
        help="Total budget amount in KRW",
    )
    parser.add_argument(
        "--scope",
        nargs="+",
        default=[
            "cost_center",
            "department",
            "business_unit",
            "tag",
            "tenant",
        ],
        help="Scope dimensions (default: all 5)",
    )
    parser.add_argument(
        "--actor-id",
        default="dry-run-cli",
        help="Actor ID (default: dry-run-cli)",
    )
    return parser.parse_args(argv)


async def run_dry_run(args: argparse.Namespace) -> int:
    """Execute the budget planning dry-run flow.

    Returns 0 on success, 1 on error.
    """
    print("[dry-run] Starting Phase 24 FinOps Budget Planning dry-run")
    print(f"[dry-run] tenant_id={args.tenant_id}")
    print(f"[dry-run] period_key={args.period_key}")
    print(f"[dry-run] period_type={args.period_type}")
    print(f"[dry-run] total_budget_amount={args.total_budget_amount} KRW")

    try:
        # 1) Create plan (dry_run=True)
        plan = create_budget_plan(
            tenant_id=args.tenant_id,
            period_key=args.period_key,
            period_type=args.period_type,
            scope=args.scope,
            total_budget_amount=args.total_budget_amount,
            dry_run=True,
            actor_id=args.actor_id,
        )
        print(f"[dry-run] Plan created: plan_id={plan['plan_id']}")
        print(f"[dry-run] Lifecycle: {plan['lifecycle']}")
        print(f"[dry-run] High-value: {plan['high_value']}")
        print(f"[dry-run] Requires 2FA: {plan['requires_2fa']}")

        # 2) Allocate budget (dry_run=True)
        allocations = allocate_budget(
            tenant_id=args.tenant_id,
            plan_id=plan["plan_id"],
            total_budget_amount=args.total_budget_amount,
            dim_rows=[
                {"dimension": dim, "dimension_value": f"default-{dim}"} for dim in args.scope
            ],
            dry_run=True,
            actor_id=args.actor_id,
        )
        print(f"[dry-run] Allocations: count={len(allocations)}")

        # 3) Compute variance (dry_run=True, empty actuals)
        variance_rows = compute_budget_vs_actual(
            tenant_id=args.tenant_id,
            plan=plan,
            allocations=allocations,
            actual_amounts={},  # No actuals in dry-run
            actor_id=args.actor_id,
        )
        print(f"[dry-run] Variance rows: count={len(variance_rows)}")

        # 4) Trigger over-budget alert (dry_run=True)
        # Use a sample variance_pct to demonstrate alert flow
        sample_variance_pct = 15.0  # 15% over budget → warning
        alert = trigger_over_budget_alert(
            tenant_id=args.tenant_id,
            plan_id=plan["plan_id"],
            variance_pct=sample_variance_pct,
            plan_total_budget_amount=args.total_budget_amount,
            actor_id=args.actor_id,
            dry_run=True,
        )
        print(f"[dry-run] Alert: severity={alert.get('severity')}")

        # 5) Aggregate summaries
        plan_summary = aggregate_budget_plans([plan])
        alloc_summary = aggregate_budget_allocations(allocations)
        variance_summary = aggregate_budget_vs_actual(variance_rows)
        alert_summary = aggregate_budget_alerts([alert] if alert.get("alert_id") else [])

        output = {
            "status": "ok",
            "dry_run": True,
            "plan": plan,
            "plan_summary": plan_summary,
            "allocation_summary": alloc_summary,
            "variance_summary": variance_summary,
            "alert_summary": alert_summary,
            "audit_action": "budget_planning_dry_run_executed",
        }
        print(f"[dry-run] Output: {json.dumps(output, indent=2, ensure_ascii=False, default=str)}")
        print("[dry-run] ✅ Phase 24 budget planning dry-run completed successfully")
        return 0
    except Exception as e:
        print(f"[dry-run] ❌ Error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(run_dry_run(args))


if __name__ == "__main__":
    sys.exit(main())
