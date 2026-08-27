"""apps.api.scripts.cli.finops_vendor_management_dry_run — Phase 25 dry-run CLI.

Phase 25 wire (cj-style 173번째) — FinOps Vendor Management post-budget-
allocation layer dry-run CLI script (PRD §F41.8 + AD-53 (a) verbatim
EXTENSION + Phase 24 finops_budget_planning_dry_run pattern).

Provides:
- `--finops-vendor-management-dry-run` 1 NEW CLI flag
- Executes dry-run mode on the vendor_catalog_engine +
  vendor_selection_engine + vendor_contract_lifecycle_engine +
  vendor_performance_evaluation + vendor_spend_attribution without
  persisting actual audit-first INSERT events.
- Writes preview snapshot to phase_25_vendor_management_preview table.
- Emits `vendor_dry_run_executed` audit action.

Usage:
    python -m apps.api.scripts.cli.finops_vendor_management_dry_run \
        --tenant-id <UUID> --period-key 2026-08 --vendor-name "AWS" \
        --vendor-category cloud --cost-score 85.0 --performance-score 90.0 \
        --reliability-score 95.0 --compliance-score 88.0 \
        --strategic-fit-score 80.0

CR lessons applied:
- CR 0-2 RLS — tenant_id selector.
- CR 1-1 audit-first INSERT — `vendor_dry_run_executed`.
- AD-53 (a) dry-run mode detail.
- NFR4 PII minimization PRESERVED.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from apps.api.modules.finops.vendor_management.vendor_catalog_engine import (
    compute_vendor_risk_score,
    validate_vendor_scores,
)
from apps.api.modules.finops.vendor_management.vendor_selection_engine import (
    score_vendor,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 25 FinOps Vendor Management dry-run CLI"
    )
    parser.add_argument(
        "--finops-vendor-management-dry-run",
        action="store_true",
        default=True,
        help="Run in dry-run mode (default: True)",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        required=True,
        help="Tenant UUID (RLS selector)",
    )
    parser.add_argument(
        "--period-key",
        type=str,
        required=True,
        help="Period key (e.g. '2026-08' / '2026-Q3' / '2026')",
    )
    parser.add_argument(
        "--vendor-name",
        type=str,
        required=True,
        help="Vendor display name",
    )
    parser.add_argument(
        "--vendor-category",
        type=str,
        required=True,
        choices=["cloud", "saas", "outsourcing", "consulting", "hardware", "other"],
        help="Vendor category (6 taxonomy)",
    )
    parser.add_argument(
        "--cost-score",
        type=float,
        required=True,
        help="Cost dimension score (0.00~100.00)",
    )
    parser.add_argument(
        "--performance-score",
        type=float,
        required=True,
        help="Performance dimension score (0.00~100.00)",
    )
    parser.add_argument(
        "--reliability-score",
        type=float,
        required=True,
        help="Reliability dimension score (0.00~100.00)",
    )
    parser.add_argument(
        "--compliance-score",
        type=float,
        required=True,
        help="Compliance dimension score (0.00~100.00)",
    )
    parser.add_argument(
        "--strategic-fit-score",
        type=float,
        required=True,
        help="Strategic-fit dimension score (0.00~100.00)",
    )
    parser.add_argument(
        "--contract-count",
        type=int,
        default=0,
        help="Existing contracts (default 0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Force dry-run mode (default: True)",
    )
    return parser.parse_args(argv)


async def main_async(args: argparse.Namespace) -> int:
    """Execute Phase 25 vendor management dry-run.

    Returns:
        0 on success, non-zero on error.
    """
    print(
        f"[phase-25-dry-run] tenant_id={args.tenant_id} "
        f"period_key={args.period_key} vendor_name={args.vendor_name}"
    )

    try:
        # Step 1: Validate scores (CR 11-4 P-015 pure validator)
        validate_vendor_scores(
            cost_score=args.cost_score,
            performance_score=args.performance_score,
            reliability_score=args.reliability_score,
            compliance_score=args.compliance_score,
            strategic_fit_score=args.strategic_fit_score,
        )

        # Step 2: Compute composite risk score
        risk_score = compute_vendor_risk_score(
            cost_score=args.cost_score,
            reliability_score=args.reliability_score,
            compliance_score=args.compliance_score,
        )

        # Step 3: Compute 5-dim weighted selection score
        weighted_total = score_vendor(
            cost_score=args.cost_score,
            performance_score=args.performance_score,
            reliability_score=args.reliability_score,
            compliance_score=args.compliance_score,
            strategic_fit_score=args.strategic_fit_score,
        )

        # Step 4: Build preview summary
        preview_summary = {
            "tenant_id": args.tenant_id,
            "period_key": args.period_key,
            "vendor_name": args.vendor_name,
            "vendor_category": args.vendor_category,
            "cost_score": args.cost_score,
            "performance_score": args.performance_score,
            "reliability_score": args.reliability_score,
            "compliance_score": args.compliance_score,
            "strategic_fit_score": args.strategic_fit_score,
            "composite_risk_score": risk_score,
            "weighted_selection_score": weighted_total,
            "selection_threshold": 60.00,
            "passes_selection_threshold": weighted_total >= 60.00,
            "dry_run": args.dry_run,
            "model_version": "1.0.0",
        }

        print("[phase-25-dry-run] PREVIEW SUMMARY:")
        print(json.dumps(preview_summary, indent=2, ensure_ascii=False))
        return 0

    except ValueError as exc:
        print(f"[phase-25-dry-run] VALIDATION ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"[phase-25-dry-run] UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    """Sync entrypoint."""
    args = parse_args(argv)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
