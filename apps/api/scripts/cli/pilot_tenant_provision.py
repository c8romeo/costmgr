"""apps.api.scripts.cli.pilot_tenant_provision — Pilot tenant onboarding CLI (cj-304 wire).

cj-304 wire sprint (cj-style 310번째 epic 연속 정직 회복 source+docs atomic
single sprint) — Pilot program 8 weeks (2026-09-14 ~ 2026-11-09 KST,
5-10 SaaS 제조 스타트업 무료). Each pilot customer tenant must be onboarded
with:
  1. tenants row (idempotent — re-runs safe)
  2. owner user with TWO_FACTOR_AUTH capability (AD-22 verbatim)
  3. 4 capability grants: EXPORT_CSV + EXPORT_PDF + EXPORT_EMAIL + EXPORT_SCHEDULED
     (capability matrix v1.54 EXTENSION preserved, cj-285 + cj-299 + cj-300 결정 wire)
  4. audit log row `pilot_tenant_provisioned` (CR 1-1 verbatim + ActionClass.REPORTS)

Usage:
    # Dry-run (mandatory default for safety — review before applying):
    uv run python apps/api/scripts/cli/pilot_tenant_provision.py \\
        --tenant-id="$(uuidgen)" \\
        --industry="saas_manufacturing" \\
        --admin-email="cfo@customer.com" \\
        --admin-display-name="Customer Admin" \\
        --finance-contact-email="finance@customer.com" \\
        --dry-run

    # Apply (only after dry-run output reviewed):
    uv run python apps/api/scripts/cli/pilot_tenant_provision.py \\
        --tenant-id="$(uuidgen)" \\
        --industry="saas_manufacturing" \\
        --admin-email="cfo@customer.com" \\
        --admin-display-name="Customer Admin" \\
        --finance-contact-email="finance@customer.com"

Industries (capability matrix v1.54 EXTENSION preserved):
    saas_manufacturing | saas_retail | saas_logistics | saas_finance

CR 11-3 honest-DEFER 252번째 (cj-304 entry 의 251번째 → cj-304 wire 의 252번째).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from dataclasses import dataclass
from typing import Final

# Capabilities to grant for pilot tenants (capability matrix v1.54 EXTENSION preserved).
PILOT_CAPABILITIES: Final[tuple[str, ...]] = (
    "EXPORT_CSV",
    "EXPORT_PDF",
    "EXPORT_EMAIL",
    "EXPORT_SCHEDULED",
)

# Supported industries (4-industry grants per capability matrix v1.54).
VALID_INDUSTRIES: Final[tuple[str, ...]] = (
    "saas_manufacturing",
    "saas_retail",
    "saas_logistics",
    "saas_finance",
)


@dataclass(frozen=True)
class PilotTenantProvisionArgs:
    """Parsed CLI args for pilot tenant provisioning."""

    tenant_id: uuid.UUID
    industry: str
    admin_email: str
    admin_display_name: str
    finance_contact_email: str
    dry_run: bool


def parse_cli_args(argv: list[str] | None = None) -> PilotTenantProvisionArgs:
    """Parse CLI arguments with validation."""
    parser = argparse.ArgumentParser(
        prog="pilot_tenant_provision",
        description=(
            "Pilot tenant onboarding CLI (cj-304 wire). "
            "Default is --dry-run for safety. Review output before applying."
        ),
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        required=True,
        help="Tenant UUID (use $(uuidgen) to generate).",
    )
    parser.add_argument(
        "--industry",
        type=str,
        required=True,
        choices=VALID_INDUSTRIES,
        help="Industry vertical (4-industry grants per capability matrix v1.54).",
    )
    parser.add_argument(
        "--admin-email",
        type=str,
        required=True,
        help="Owner admin email (must be valid email).",
    )
    parser.add_argument(
        "--admin-display-name",
        type=str,
        required=True,
        help="Admin display name (e.g., 'CFO Kim').",
    )
    parser.add_argument(
        "--finance-contact-email",
        type=str,
        required=True,
        help="Finance contact email (scheduled report recipient).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry-run mode (default — no DB mutations).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Apply mode (actually execute DB mutations).",
    )
    args = parser.parse_args(argv)

    # Validate tenant_id is a UUID.
    try:
        tenant_uuid = uuid.UUID(args.tenant_id)
    except ValueError as exc:
        raise SystemExit(f"ERROR: --tenant-id must be a valid UUID: {exc}") from exc

    # Validate emails contain '@' (basic check).
    for email_field, email_value in (
        ("--admin-email", args.admin_email),
        ("--finance-contact-email", args.finance_contact_email),
    ):
        if "@" not in email_value or "." not in email_value.split("@")[-1]:
            raise SystemExit(f"ERROR: {email_field} must be a valid email: {email_value!r}")

    # --apply overrides --dry-run default.
    dry_run = not args.apply

    return PilotTenantProvisionArgs(
        tenant_id=tenant_uuid,
        industry=args.industry,
        admin_email=args.admin_email,
        admin_display_name=args.admin_display_name,
        finance_contact_email=args.finance_contact_email,
        dry_run=dry_run,
    )


def render_plan(args: PilotTenantProvisionArgs) -> dict:
    """Render the planned operations as a structured dict (for dry-run output + audit log)."""
    return {
        "operation": "pilot_tenant_provision",
        "dry_run": args.dry_run,
        "tenant": {
            "id": str(args.tenant_id),
            "industry": args.industry,
            "admin_email": args.admin_email,
            "admin_display_name": args.admin_display_name,
            "finance_contact_email": args.finance_contact_email,
        },
        "planned_actions": [
            {
                "step": 1,
                "action": "INSERT INTO tenants (id, industry, status, created_at)",
                "table": "tenants",
                "idempotent": True,
                "values": {
                    "id": str(args.tenant_id),
                    "industry": args.industry,
                    "status": "active",
                },
            },
            {
                "step": 2,
                "action": "INSERT INTO users (id, tenant_id, email, role, display_name, two_factor_required)",
                "table": "users",
                "idempotent": True,
                "values": {
                    "tenant_id": str(args.tenant_id),
                    "email": args.admin_email,
                    "role": "owner",
                    "display_name": args.admin_display_name,
                    "two_factor_required": True,
                },
            },
            {
                "step": 3,
                "action": "INSERT INTO capability_grants (tenant_id, capability, industry)",
                "table": "capability_grants",
                "idempotent": True,
                "values": [
                    {
                        "tenant_id": str(args.tenant_id),
                        "capability": capability,
                        "industry": args.industry,
                    }
                    for capability in PILOT_CAPABILITIES
                ],
            },
            {
                "step": 4,
                "action": "INSERT INTO audit_logs (action_class, action, tenant_id, payload)",
                "table": "audit_logs",
                "idempotent": False,
                "values": {
                    "action_class": "REPORTS",
                    "action": "pilot_tenant_provisioned",
                    "tenant_id": str(args.tenant_id),
                    "payload": {
                        "industry": args.industry,
                        "admin_email": args.admin_email,
                        "capabilities": list(PILOT_CAPABILITIES),
                    },
                },
            },
        ],
    }


async def apply_plan(args: PilotTenantProvisionArgs) -> int:
    """Apply the provisioning plan to the database.

    Connects via DATABASE_URL (asyncpg) and executes the 4 steps in order:
      1. UPSERT tenants (idempotent)
      2. UPSERT users (idempotent on tenant_id + email)
      3. UPSERT capability_grants (idempotent on tenant_id + capability + industry)
      4. INSERT audit_logs (always insert — non-idempotent by design)

    Returns exit code 0 on success, 1 on error.
    """
    # Lazy import to avoid hard dependency for --dry-run-only usage.
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
    except ImportError as exc:
        print(f"ERROR: sqlalchemy not available: {exc}", file=sys.stderr)
        return 2

    import os

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL env var is required for --apply mode.", file=sys.stderr)
        return 2

    if not database_url.startswith("postgresql+asyncpg://"):
        print(
            f"ERROR: DATABASE_URL must use postgresql+asyncpg driver for async engine: {database_url[:50]}...",
            file=sys.stderr,
        )
        return 2

    print(f"[apply] Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    try:
        async with engine.begin() as conn:
            # Step 1: UPSERT tenants.
            print(f"[apply] Step 1: UPSERT tenants (id={args.tenant_id}, industry={args.industry})")
            await conn.execute(
                text(
                    """
                    INSERT INTO tenants (id, industry, status, created_at)
                    VALUES (:id, :industry, 'active', NOW())
                    ON CONFLICT (id) DO UPDATE SET industry = EXCLUDED.industry
                    """
                ),
                {"id": str(args.tenant_id), "industry": args.industry},
            )

            # Step 2: UPSERT users (owner role + 2FA mandatory).
            print(
                f"[apply] Step 2: UPSERT users (tenant_id={args.tenant_id}, email={args.admin_email})"
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO users (id, tenant_id, email, role, display_name, two_factor_required, created_at)
                    VALUES (:user_id, :tenant_id, :email, 'owner', :display_name, true, NOW())
                    ON CONFLICT (tenant_id, email) DO UPDATE
                      SET display_name = EXCLUDED.display_name,
                          two_factor_required = true
                    """
                ),
                {
                    "user_id": str(uuid.uuid4()),
                    "tenant_id": str(args.tenant_id),
                    "email": args.admin_email,
                    "display_name": args.admin_display_name,
                },
            )

            # Step 3: UPSERT capability_grants (4 capabilities).
            print(
                f"[apply] Step 3: UPSERT capability_grants (4 capabilities × industry={args.industry})"
            )
            for capability in PILOT_CAPABILITIES:
                await conn.execute(
                    text(
                        """
                        INSERT INTO capability_grants (tenant_id, capability, industry, created_at)
                        VALUES (:tenant_id, :capability, :industry, NOW())
                        ON CONFLICT (tenant_id, capability, industry) DO NOTHING
                        """
                    ),
                    {
                        "tenant_id": str(args.tenant_id),
                        "capability": capability,
                        "industry": args.industry,
                    },
                )

            # Step 4: INSERT audit_logs (non-idempotent by design).
            print(
                f"[apply] Step 4: INSERT audit_logs (action_class=REPORTS, action=pilot_tenant_provisioned)"
            )
            payload = json.dumps(
                {
                    "industry": args.industry,
                    "admin_email": args.admin_email,
                    "capabilities": list(PILOT_CAPABILITIES),
                }
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO audit_logs (id, action_class, action, tenant_id, payload, created_at)
                    VALUES (:id, :action_class, :action, :tenant_id, :payload, NOW())
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "action_class": "REPORTS",
                    "action": "pilot_tenant_provisioned",
                    "tenant_id": str(args.tenant_id),
                    "payload": payload,
                },
            )

        print(f"[apply] SUCCESS — tenant {args.tenant_id} provisioned for {args.admin_email}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[apply] ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


async def main_async(argv: list[str] | None = None) -> int:
    """CLI main entrypoint."""
    args = parse_cli_args(argv)
    plan = render_plan(args)

    if args.dry_run:
        # Dry-run mode: print planned operations as structured JSON.
        print(f"[dry-run] pilot_tenant_provision start")
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        print(f"[dry-run] Review the planned actions above.")
        print(f"[dry-run] To apply, re-run with --apply flag.")
        return 0

    # Apply mode.
    print(f"[apply] pilot_tenant_provision start (DRY-RUN SKIPPED)")
    return await apply_plan(args)


def main() -> int:
    """Sync entrypoint for setup.py console_scripts compatibility."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
