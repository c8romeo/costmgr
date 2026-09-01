"""apps.api.scripts.cli.finops_budget_planning_over_budget_alert_dry_run — Phase 24 alert dry-run CLI.

Phase 24 wire (cj-style 169번째) — FinOps Budget Planning over-budget
alert dry-run CLI script (PRD §F40.5 + AD-52 (d) verbatim EXTENSION +
Phase 23 finops_unit_economics_dry_run pattern).

Provides:
- `--finops-budget-planning-over-budget-alert-dry-run` 1 NEW CLI flag
- Executes over-budget alert flow in dry-run mode (no notification
  channels dispatched + no auto-escalation chain triggered).
- Demonstrates warning (10%+) → Slack DM flow.
- Demonstrates critical (25%+) → admin email + Slack #critical-alerts flow.
- Demonstrates escalation chain for high-value (≥10M KRW/year) plans.

Usage:
    python -m apps.api.scripts.cli.finops_budget_planning_over_budget_alert_dry_run \
        --tenant-id <UUID> --plan-id <UUID> --variance-pct 28 \
        --plan-total-budget-amount 15000000

CR lessons applied:
- CR 0-2 RLS — tenant_id selector.
- CR 1-1 audit-first INSERT — `budget_alert_triggered` (dry-run).
- AD-52 (d) over-budget alert + auto-escalation chain detail.
- AD-22 owner-only RBAC.
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year).
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from apps.api.modules.finops.budget_planning.budget_alert import (
    acknowledge_alert,
    aggregate_budget_alerts,
    escalate_alert,
    trigger_over_budget_alert,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 24 FinOps Budget Planning over-budget alert dry-run CLI"
    )
    parser.add_argument(
        "--finops-budget-planning-over-budget-alert-dry-run",
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
        "--plan-id",
        required=True,
        help="Budget plan UUID",
    )
    parser.add_argument(
        "--variance-pct",
        type=float,
        required=True,
        help="Variance percentage (e.g. 12 = 12%% over budget)",
    )
    parser.add_argument(
        "--plan-total-budget-amount",
        type=float,
        required=True,
        help="Plan total budget amount in KRW",
    )
    parser.add_argument(
        "--actor-id",
        default="alert-dry-run-cli",
        help="Actor ID (default: alert-dry-run-cli)",
    )
    return parser.parse_args(argv)


async def run_alert_dry_run(args: argparse.Namespace) -> int:
    """Execute the over-budget alert dry-run flow.

    Returns 0 on success, 1 on error.
    """
    print("[alert-dry-run] Starting Phase 24 over-budget alert dry-run")
    print(f"[alert-dry-run] tenant_id={args.tenant_id}")
    print(f"[alert-dry-run] plan_id={args.plan_id}")
    print(f"[alert-dry-run] variance_pct={args.variance_pct}")
    print(f"[alert-dry-run] plan_total_budget_amount={args.plan_total_budget_amount}")

    try:
        # 1) Trigger initial alert (dry_run=True)
        alert = trigger_over_budget_alert(
            tenant_id=args.tenant_id,
            plan_id=args.plan_id,
            variance_pct=args.variance_pct,
            plan_total_budget_amount=args.plan_total_budget_amount,
            actor_id=args.actor_id,
            dry_run=True,
        )
        print(f"[alert-dry-run] Initial alert: severity={alert.get('severity')}")
        print(f"[alert-dry-run] Escalation level: {alert.get('escalation_level')}")
        print(f"[alert-dry-run] High-value: {alert.get('high_value')}")
        print(f"[alert-dry-run] Requires 2FA: {alert.get('requires_2fa')}")
        print(f"[alert-dry-run] Channels notified: {alert.get('channels_notified')}")

        # 2) If critical → escalate to on-call chain (dry_run)
        if alert.get("severity") == "critical" and alert.get("high_value"):
            escalated = escalate_alert(
                alert=alert,
                target_level=2,  # ESCALATION_LEVEL_ONCALL
                actor_id=args.actor_id,
            )
            print("[alert-dry-run] Escalated to on-call chain (level 2)")
            print(
                f"[alert-dry-run] Channels after escalation: {escalated.get('channels_notified')}"
            )
            final_alert = escalated
        else:
            final_alert = alert

        # 3) Acknowledge alert (dry-run)
        acknowledged = acknowledge_alert(
            alert=final_alert,
            actor_id=args.actor_id,
        )
        print(f"[alert-dry-run] Alert acknowledged by: {acknowledged.get('acknowledged_by')}")

        # 4) Aggregate summary
        alert_summary = aggregate_budget_alerts([acknowledged])

        output = {
            "status": "ok",
            "dry_run": True,
            "alert": acknowledged,
            "alert_summary": alert_summary,
            "audit_action": "budget_alert_triggered",
        }
        print(
            f"[alert-dry-run] Output: {json.dumps(output, indent=2, ensure_ascii=False, default=str)}"
        )
        print("[alert-dry-run] ✅ Phase 24 over-budget alert dry-run completed successfully")
        return 0
    except Exception as e:
        print(f"[alert-dry-run] ❌ Error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(run_alert_dry_run(args))


if __name__ == "__main__":
    sys.exit(main())
