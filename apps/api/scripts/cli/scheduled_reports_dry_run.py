"""scheduled_reports_dry_run — T7 dry-run CLI script for Story 30.4 scheduled reports.

cj-300 wire sprint (cj-style 302번째) — dry-run CLI flag
--scheduled-reports-dry-run. Outputs preview metadata without persisting
to DB or emitting audit events.

Usage:
    python -m apps.api.scripts.cli.scheduled_reports_dry_run \\
        --tenant-id <uuid> \\
        --dispatch-schedule monthly \\
        --recipient-strategy finance_and_admin

CR 11-3 honest-DEFER 244번째.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from apps.api.jobs.scheduled_reports import parse_cli_args, run_scheduled_dispatch


async def main_async(argv: list[str] | None = None) -> int:
    """CLI main entrypoint for scheduled reports dry-run."""
    args = parse_cli_args(argv)
    dry_run = args.scheduled_reports_dry_run or args.legacy_dry_run

    if not dry_run:
        print(
            "ERROR: --scheduled-reports-dry-run flag is required for dry-run mode.",
            file=sys.stderr,
        )
        return 2

    print(f"[dry-run] scheduled_reports_dry_run start")
    print(f"[dry-run] tenant_id={args.tenant_id}")
    print(f"[dry-run] dispatch_schedule={args.dispatch_schedule}")
    print(f"[dry-run] recipient_strategy={args.recipient_strategy}")
    print(f"[dry-run] report_type={args.report_type}")
    print(f"[dry-run] period_key={args.period_key or 'auto'}")

    metadata = await run_scheduled_dispatch(
        tenant_id=args.tenant_id,
        dispatch_schedule=args.dispatch_schedule,
        recipient_strategy=args.recipient_strategy,
        finance_contact_email=args.finance_contact_email,
        report_type=args.report_type,
        period_key=args.period_key,
        dry_run=True,
    )

    print(f"[dry-run] OK: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Sync wrapper for async main."""
    return asyncio.run(main_async(argv))


if __name__ == "__main__":
    sys.exit(main())
