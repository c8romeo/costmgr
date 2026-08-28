"""apps.api.scripts.cli.finops_interactive_dashboard_dry_run — Phase 28 dry-run CLI.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
dry-run mode CLI (PRD §F43.1~§F43.8 + AD-56 (a)~(g) 7 sub-decisions
verbatim + 1 NEW CLI flag `--finops-interactive-dashboard-dry-run`).

Usage:
    python -m apps.api.scripts.cli.finops_interactive_dashboard_dry_run \\
        --tenant-id <uuid> \\
        --finops-interactive-dashboard-dry-run

CR lessons applied:
- AD-22 owner-only RBAC.
- NFR18 ko-KR SSOT — Korean error messages.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal

from apps.api.modules.finops.interactive_dashboard import (
    CROSS_PHASE_ROLLUP_DIMENSIONS,
    DASHBOARD_CADENCE_HOURS_KST,
    DASHBOARD_DEFAULTS,
    DASHBOARD_RECIPIENT_TEMPLATES,
    EXPORT_MAX_RETRIES,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MAX_EXPORT_SIZE_BYTES,
    MAX_SAVED_VIEWS_PER_TENANT,
    PHASE_LEDGER_MAX_PHASE,
    PHASE_LEDGER_MIN_PHASE,
    PHASE_LEDGER_PHASE_COUNT,
    PREDEFINED_VIEW_TEMPLATES,
    SAVED_VIEW_CACHE_TTL_SECONDS,
    UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS,
    compute_unified_kpi,
    realtime_incremental_update_via_listen_notify,
)


def main() -> int:
    """Run dry-run mode for Phase 28 interactive_dashboard.

    Returns:
        Exit code (0 success, 1 error).
    """
    parser = argparse.ArgumentParser(
        description="Phase 28 FinOps Interactive Dashboard dry-run CLI",
    )
    parser.add_argument("--tenant-id", required=True, help="UUID tenant identifier")
    parser.add_argument(
        "--finops-interactive-dashboard-dry-run",
        action="store_true",
        default=True,
        help="Phase 28 dry-run mode flag (always True for this CLI)",
    )
    parser.add_argument(
        "--period-key",
        default="2026-08",
        help="Period key (default: 2026-08)",
    )
    parser.add_argument(
        "--dimension",
        default="tenant",
        choices=list(CROSS_PHASE_ROLLUP_DIMENSIONS),
        help="Cross-phase rollup dimension (default: tenant)",
    )
    args = parser.parse_args()

    if not args.tenant_id:
        print("오류: --tenant-id는 필수입니다.", file=sys.stderr)
        return 1

    try:
        # Dry-run mode: simulate unified KPI rollup without DB INSERT
        kpi_result = compute_unified_kpi(
            tenant_id=args.tenant_id,
            period_key=args.period_key,
            dimension=args.dimension,
        )
        is_subscribed = realtime_incremental_update_via_listen_notify()
    except (ValueError, TypeError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    output = {
        "dry_run": True,
        "tenant_id": args.tenant_id,
        "period_key": args.period_key,
        "dimension": args.dimension,
        "module_tag": "m28_finops_interactive_dashboard",
        # Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED INTEGRATED
        "phase_ledger_min_phase": PHASE_LEDGER_MIN_PHASE,
        "phase_ledger_max_phase": PHASE_LEDGER_MAX_PHASE,
        "phase_ledger_phase_count": PHASE_LEDGER_PHASE_COUNT,
        # 6-dim cross-rollup
        "cross_phase_rollup_dimensions": list(CROSS_PHASE_ROLLUP_DIMENSIONS),
        # 12 NEW pre-defined view templates
        "predefined_view_templates": list(PREDEFINED_VIEW_TEMPLATES),
        "predefined_view_template_count": len(PREDEFINED_VIEW_TEMPLATES),
        # LISTEN/NOTIFY 18 channels
        "listen_notify_channels": list(UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS),
        "listen_notify_channel_count": len(UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS),
        "listen_notify_subscribed": is_subscribed,
        # 4 cadences
        "dashboard_cadence_hours_kst": dict(DASHBOARD_CADENCE_HOURS_KST),
        # Recipient templates
        "recipient_templates": list(DASHBOARD_RECIPIENT_TEMPLATES.keys()),
        # Constants
        "saved_view_cache_ttl_seconds": SAVED_VIEW_CACHE_TTL_SECONDS,
        "max_saved_views_per_tenant": MAX_SAVED_VIEWS_PER_TENANT,
        "max_export_size_bytes": MAX_EXPORT_SIZE_BYTES,
        "export_max_retries": EXPORT_MAX_RETRIES,
        "high_value_threshold_krw_per_year": float(HIGH_VALUE_THRESHOLD_KRW_PER_YEAR),
        "dashboard_defaults": dict(DASHBOARD_DEFAULTS),
        # Dry-run KPI result (UnifiedKPI TypedDict — 18 unified KPI metrics)
        "kpi_unified_kpi_id": kpi_result.get("unified_kpi_id", ""),
        "kpi_period_key": kpi_result.get("period_key", ""),
        "kpi_dimension": kpi_result.get("dimension", ""),
        "kpi_dimension_value": kpi_result.get("dimension_value", ""),
        "kpi_value_krw": str(kpi_result.get("kpi_value_krw", Decimal("0.00"))),
        "kpi_trace_id": kpi_result.get("trace_id", ""),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
