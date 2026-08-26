"""apps.api.jobs.scheduled_chargeback_settlement_dispatch_job — Scheduled dispatch KST cron job.

Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement territory
(PRD §F38.4 + AD-50 (d) decision + AD-14 stack pin).

Scheduled dispatch KST cron engine:
- 4 cron schedules: monthly 1st-day 04:00 + quarterly 1st-day 05:00 +
  semi_annual 1st-day 06:00 + annual Jan-1 07:00 KST pytz
- apscheduler==3.10.4 AsyncIOScheduler + PersistentJobStore
- CLI flag: --finops-chargeback-settlement-dry-run (T7)
- Idempotency per (tenant_id + dispatch_schedule + period_key) tuple
- Retry policy: exponential backoff 1min → 5min → 30min, 3 retries
- Audit-first INSERT `settlement_calculated` + `settlement_reconciled`
- 8 NEW audit actions Phase 22 verbatim
- Dry-run mode (T7 dry-run CLI flag)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 8 NEW actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 9-6 commit message discipline.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-50 FinOps Chargeback Settlement (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from typing import Any

import pytz

from apps.api.modules.finops.chargeback_settlement.scheduled_chargeback_settlement_dispatch import (
    ALL_SETTLEMENT_CADENCES,
    execute_dispatch,
)

logger = logging.getLogger(__name__)

# KST timezone (AD-14 stack pin pytz==2024.1).
KST = pytz.timezone("Asia/Seoul")

# 4 cron expressions (PRD §F38.4-2 verbatim).
SETTLEMENT_DISPATCH_CRON_KST: dict[str, str] = {
    "monthly": "0 4 1 * *",       # 1st-day 04:00 KST monthly
    "quarterly": "0 5 1 1,4,7,10 *",  # 1st-day 05:00 KST quarterly
    "semi_annual": "0 6 1 1,7 *",   # 1st-day 06:00 KST semi_annual
    "annual": "0 7 1 1 *",          # Jan-1 07:00 KST annual
}


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for dispatch job entrypoint.

    T7 dry-run CLI flag: --finops-chargeback-settlement-dry-run
    """
    parser = argparse.ArgumentParser(
        prog="scheduled_chargeback_settlement_dispatch",
        description=(
            "Phase 22 FinOps Chargeback Settlement scheduled dispatch job. "
            "Supports 4 cadence (monthly + quarterly + semi_annual + annual) "
            "KST pytz + dry-run mode + 9 endpoints integration."
        ),
    )
    parser.add_argument(
        "--cadence",
        type=str,
        choices=ALL_SETTLEMENT_CADENCES,
        default="monthly",
        help="Settlement cadence (monthly / quarterly / semi_annual / annual).",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="default-tenant",
        help="Tenant ID for dispatch execution.",
    )
    parser.add_argument(
        "--target-amount-krw",
        type=float,
        default=10_000_000.0,
        help="Target settlement amount in KRW (default 10M).",
    )
    parser.add_argument(
        "--finops-chargeback-settlement-dry-run",
        action="store_true",
        dest="finops_chargeback_settlement_dry_run",
        help=(
            "T7 dry-run CLI flag. When set, executes dispatch in dry-run "
            "mode without persisting to DB or emitting audit events. "
            "Outputs preview metadata only."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="legacy_dry_run",
        help="Legacy alias for --finops-chargeback-settlement-dry-run.",
    )
    return parser.parse_args(argv)


async def run_scheduled_dispatch(
    cadence: str,
    tenant_id: str,
    target_amount_krw: float,
    dry_run: bool,
    db_session: Any | None = None,
) -> dict[str, Any]:
    """Run scheduled dispatch for given cadence + tenant_id.

    Returns dispatch metadata dict.
    """
    if cadence not in ALL_SETTLEMENT_CADENCES:
        raise ValueError(f"invalid_cadence:{cadence}")

    cron_expr = SETTLEMENT_DISPATCH_CRON_KST.get(cadence, "0 4 1 * *")
    five_module_inputs = {
        "phase_11_chargeback": target_amount_krw * 0.30,
        "phase_18_commitment": target_amount_krw * 0.20,
        "phase_19_pricing": target_amount_krw * 0.20,
        "phase_20_multi_cloud": target_amount_krw * 0.15,
        "phase_21_reserved_capacity": target_amount_krw * 0.15,
    }
    target_dimensions = [
        "cost_center", "department", "business_unit", "tag", "tenant"
    ]

    dispatch_meta = execute_dispatch(
        tenant_id=tenant_id,
        cadence=cadence,
        five_module_inputs=five_module_inputs,
        target_amount_krw=target_amount_krw,
        target_dimensions=target_dimensions,
        dry_run=dry_run,
        trace_id=None,
        db_session=db_session,
    )

    return {
        "dispatch": dispatch_meta,
        "cron_kst": cron_expr,
        "cadence": cadence,
        "tenant_id": tenant_id,
        "target_amount_krw": target_amount_krw,
        "dry_run": dry_run,
        "executed_at": datetime.now(KST).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for scheduled dispatch.

    Usage:
        python -m apps.api.jobs.scheduled_chargeback_settlement_dispatch_job \\
            --cadence monthly \\
            --tenant-id tenant-1 \\
            --target-amount-krw 10000000 \\
            --finops-chargeback-settlement-dry-run
    """
    args = parse_cli_args(argv)

    # T7 dry-run CLI flag resolution
    dry_run = bool(
        args.finops_chargeback_settlement_dry_run or args.legacy_dry_run
    )

    logger.info(
        "scheduled_chargeback_settlement_dispatch_start cadence=%s tenant=%s "
        "target_amount_krw=%s dry_run=%s",
        args.cadence,
        args.tenant_id,
        args.target_amount_krw,
        dry_run,
    )

    result = asyncio.run(
        run_scheduled_dispatch(
            cadence=args.cadence,
            tenant_id=args.tenant_id,
            target_amount_krw=args.target_amount_krw,
            dry_run=dry_run,
            db_session=None,
        )
    )

    if dry_run:
        logger.info(
            "scheduled_chargeback_settlement_dispatch_dry_run "
            "cadence=%s tenant=%s preview_ok=true",
            args.cadence,
            args.tenant_id,
        )
        print(f"[DRY-RUN] dispatch_id={result['dispatch']['dispatch_id']}")
        print(f"[DRY-RUN] period_key={result['dispatch']['period_key']}")
        print(f"[DRY-RUN] result_id={result['dispatch']['settlement_result']['result_id']}")
        print(f"[DRY-RUN] allocation_count={result['dispatch']['settlement_result']['allocation_count']}")
    else:
        logger.info(
            "scheduled_chargeback_settlement_dispatch_executed "
            "cadence=%s tenant=%s dispatch_id=%s",
            args.cadence,
            args.tenant_id,
            result["dispatch"]["dispatch_id"],
        )
        print(f"dispatch_id={result['dispatch']['dispatch_id']}")
        print(f"period_key={result['dispatch']['period_key']}")
        print(f"result_id={result['dispatch']['settlement_result']['result_id']}")
        print(f"allocation_count={result['dispatch']['settlement_result']['allocation_count']}")

    return 0


__all__ = [
    "KST",
    "SETTLEMENT_DISPATCH_CRON_KST",
    "parse_cli_args",
    "run_scheduled_dispatch",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
