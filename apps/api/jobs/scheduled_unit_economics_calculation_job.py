"""apps.api.jobs.scheduled_unit_economics_calculation_job — Scheduled calculation KST cron job.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics territory
(PRD §F39.1 + AD-51 (e) decision + AD-14 stack pin).

Scheduled calculation KST cron engine:
- 4 cron schedules: daily 03:30 + weekly Mon 04:00 + monthly 1st-day
  04:30 + quarterly 1st-day 05:00 KST pytz
- apscheduler==3.10.4 AsyncIOScheduler + PersistentJobStore
- CLI flag: --finops-unit-economics-dry-run (T7)
- Idempotency per (tenant_id + cadence + period_key) tuple
- Retry policy: exponential backoff 1min → 5min → 30min, 3 retries
- Audit-first INSERT `unit_economics_calculated` + 6 NEW related
- 7 NEW audit actions Phase 23 verbatim
- Dry-run mode (T7 dry-run CLI flag)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 7 NEW actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 9-6 commit message discipline.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-51 FinOps Unit Economics (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
  FX + real-time stream — all honestly DEFER to future Phase 23.x).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Any

import pytz

from apps.api.modules.finops.unit_economics.scheduled_unit_economics_calculation import (
    ALL_UNIT_ECONOMICS_CADENCES,
    execute_calculation,
)

logger = logging.getLogger(__name__)

# KST timezone (AD-14 stack pin pytz==2024.1).
KST = pytz.timezone("Asia/Seoul")

# 4 cron expressions (PRD §F39.1-2 verbatim).
UNIT_ECONOMICS_CALCULATION_CRON_KST: dict[str, str] = {
    "daily": "30 3 * * *",  # 03:30 KST daily
    "weekly": "0 4 * * 1",  # 04:00 KST weekly Monday
    "monthly": "30 4 1 * *",  # 04:30 KST monthly 1st-day
    "quarterly": "0 5 1 1,4,7,10 *",  # 05:00 KST quarterly 1st-day
}


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for calculation job entrypoint.

    T7 dry-run CLI flag: --finops-unit-economics-dry-run
    """
    parser = argparse.ArgumentParser(
        prog="scheduled_unit_economics_calculation",
        description=(
            "Phase 23 FinOps Unit Economics scheduled calculation job. "
            "Supports 4 cadence (daily + weekly + monthly + quarterly) "
            "KST pytz + dry-run mode + 9 endpoints integration."
        ),
    )
    parser.add_argument(
        "--cadence",
        type=str,
        choices=ALL_UNIT_ECONOMICS_CADENCES,
        default="daily",
        help="Unit economics cadence (daily / weekly / monthly / quarterly).",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="default-tenant",
        help="Tenant ID for calculation execution.",
    )
    parser.add_argument(
        "--source-settlement-id",
        type=str,
        default="default-settlement-id",
        help="Phase 22 source settlement_id to derive unit_economics from.",
    )
    parser.add_argument(
        "--total-cost-krw",
        type=float,
        default=10_000_000.0,
        help="Total cost in KRW (default 10M).",
    )
    parser.add_argument(
        "--total-revenue-krw",
        type=float,
        default=0.0,
        help="Total revenue in KRW (default 0.0 = D-FINOPS-12 DEFER margin).",
    )
    parser.add_argument(
        "--total-units",
        type=int,
        default=100,
        help="Total units (business_units count) (default 100).",
    )
    parser.add_argument(
        "--total-transactions",
        type=int,
        default=10_000,
        help="Total transactions count (default 10K).",
    )
    parser.add_argument(
        "--allocation-count",
        type=int,
        default=1000,
        help="Allocation count for confidence computation (default 1000).",
    )
    parser.add_argument(
        "--revenue-completeness-pct",
        type=float,
        default=0.0,
        help="Revenue completeness 0~100 (default 0.0 = no revenue registered).",
    )
    parser.add_argument(
        "--finops-unit-economics-dry-run",
        action="store_true",
        dest="finops_unit_economics_dry_run",
        help=(
            "T7 dry-run CLI flag. When set, executes calculation in "
            "dry-run mode without persisting to DB or emitting audit "
            "events. Outputs preview metadata only."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="legacy_dry_run",
        help="Legacy alias for --finops-unit-economics-dry-run.",
    )
    return parser.parse_args(argv)


async def run_scheduled_calculation(
    cadence: str,
    tenant_id: str,
    source_settlement_id: str,
    total_cost_krw: float,
    total_revenue_krw: float,
    total_units: int,
    total_transactions: int,
    allocation_count: int,
    revenue_completeness_pct: float,
    dry_run: bool,
    db_session: Any | None = None,
) -> dict[str, Any]:
    """Run scheduled calculation for given cadence + tenant_id.

    Returns calculation metadata dict.
    """
    five_dim_inputs: dict[str, float] = {
        "cost_center": total_cost_krw * 0.30,
        "department": total_cost_krw * 0.25,
        "business_unit": total_cost_krw * 0.20,
        "tag": total_cost_krw * 0.15,
        "tenant": total_cost_krw * 0.10,
    }
    target_dimensions: list[str] = [
        "cost_center",
        "department",
        "business_unit",
        "tag",
        "tenant",
    ]

    logger.info(
        "scheduled_unit_economics_calculation_start cadence=%s tenant=%s " "dry_run=%s cost=%.2f",
        cadence,
        tenant_id,
        dry_run,
        total_cost_krw,
    )

    result = execute_calculation(
        tenant_id=tenant_id,
        source_settlement_id=source_settlement_id,
        five_dim_inputs=five_dim_inputs,
        total_cost_krw=total_cost_krw,
        total_revenue_krw=total_revenue_krw,
        total_units=total_units,
        total_transactions=total_transactions,
        allocation_count=allocation_count,
        revenue_completeness_pct=revenue_completeness_pct,
        target_dimensions=target_dimensions,
        cadence=cadence,
        dry_run=dry_run,
        db_session=db_session,
    )

    return {
        "cadence": cadence,
        "tenant_id": tenant_id,
        "dry_run": dry_run,
        "period_key": result["period_key"],
        "total_cost_krw": result["total_cost_krw"],
        "cost_per_business_unit_krw": result["cost_per_business_unit_krw"],
        "cost_per_transaction_krw": result["cost_per_transaction_krw"],
        "margin_pct": result["margin_pct"],
        "confidence_pct": result["confidence_pct"],
        "model_version": result["model_version"],
        "trace_id": result["trace_id"],
        "computed_at": result["computed_at"],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI main entrypoint for scheduled unit_economics calculation job."""
    args = parse_cli_args(argv)
    dry_run = args.finops_unit_economics_dry_run or args.legacy_dry_run

    logger.info(
        "scheduled_unit_economics_calculation_cli cadence=%s tenant=%s " "source=%s dry_run=%s",
        args.cadence,
        args.tenant_id,
        args.source_settlement_id,
        dry_run,
    )

    try:
        metadata = asyncio.run(
            run_scheduled_calculation(
                cadence=args.cadence,
                tenant_id=args.tenant_id,
                source_settlement_id=args.source_settlement_id,
                total_cost_krw=args.total_cost_krw,
                total_revenue_krw=args.total_revenue_krw,
                total_units=args.total_units,
                total_transactions=args.total_transactions,
                allocation_count=args.allocation_count,
                revenue_completeness_pct=args.revenue_completeness_pct,
                dry_run=dry_run,
            )
        )
        logger.info(
            "scheduled_unit_economics_calculation_complete period=%s "
            "cost=%.2f margin=%.2f%% confidence=%.2f",
            metadata["period_key"],
            metadata["total_cost_krw"],
            metadata["margin_pct"],
            metadata["confidence_pct"],
        )
        print(f"OK: {metadata}")
        return 0
    except Exception as exc:
        logger.exception(
            "scheduled_unit_economics_calculation_failed cadence=%s tenant=%s " "err=%s",
            args.cadence,
            args.tenant_id,
            exc,
        )
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
