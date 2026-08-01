"""packages.services.m2_input — Monthly Input Capture (Story 3.1 + 3.2 + 3.3).

Pure-Python orchestration for the six-stream monthly input domain.
Mirrors the architecture pattern of `m0_onboarding` (Story 1.2):
- stdlib-only modules under this package
- no DB / no clock / no random (AD-1 / AD-5)
- consumed by `apps/api/modules/m2_input/*` (FastAPI routers) AND
  the TS mirror at `apps/web/lib/{m2-input-completion,l2-input-fte,l2-input-warnings}.ts`
  (drift verified by `tests/integration/test_m2_input_label_consistency.py`)

Public surface:

Stream completion (Story 3.1):
- `stream_completion.STREAM_LABELS_KO` — PRD §8.M2(b) Korean labels
- `stream_completion.STREAM_ORDER` — tab order (주문 → 생산 → … → 인원)
- `stream_completion.STREAMS_FOR_INDUSTRY` — capability_mask by Industry
- `stream_completion.compute_stream_completion` — per-stream completion bool
- `stream_completion.is_all_streams_complete` — aggregate gate
- `stream_completion.format_fte_headcount` — FTE 환산 (read-only helper)
- `stream_completion.compute_fte_wage_krw` — basis 환산 (monthly mode)

Labor conversion (Story 3.2):
- `labor_conversion.PayType` — 'monthly' | 'daily' enum
- `labor_conversion.PayrollSettings` — (monthly_salary_basis, workdays, hours, burden_rate)
- `labor_conversion.DEFAULT_PAYROLL` — PRD §6.1 defaults
- `labor_conversion.merge_payroll_settings` — partial override merge
- `labor_conversion.compute_pay_type_breakdown` — 5-field aggregator
- `labor_conversion.compute_fte_for_daily` — daily mode FTE 환산 (payroll-aware)
- `labor_conversion.compute_fte_for_monthly` — monthly mode FTE (workers as-is)
- `labor_conversion.compute_fte_wage_for_daily` — direct sum path (NEW vs Story 3.1)
- `labor_conversion.compute_fte_wage_for_monthly` — basis × workers
- `labor_conversion.rollup_daily_fte` — Σ sum for mode='daily'
- `labor_conversion.build_fte_display` — single composition function

Inventory projection (Story 3.3):
- `inventory_projection.INVENTORY_PRODUCT_TYPES` — material / semi_product / product
- `inventory_projection.InventoryMovement` — per-product aggregate NamedTuple
- `inventory_projection.compute_opening_inventory` — cj-style default 0
- `inventory_projection.compute_closing_inventory` — PRD §6.2 수불 공식
- `inventory_projection.build_inventory_projection` — per-stream mapping
- `inventory_projection.LEDGER_REFERENCE_QUERY_STUB` — Epic 5 marker

Operating rate (Story 3.3):
- `operating_rate.DEFAULT_UNIT_TIME_HOURS` — MVP 1.0h per product
- `operating_rate.OPERATING_RATE_LIMIT_PCT` — 100 (PRD §V5)
- `operating_rate.compute_total_available_hours` — fte × standard_monthly_hours
- `operating_rate.compute_production_required_hours` — Σ(qty × unit_time)
- `operating_rate.compute_operating_rate` — required / available × 100

Warnings (Story 3.3):
- `warnings.WarningCode` — NEGATIVE_CLOSING_INVENTORY | OVERCAPACITY_OPERATING_RATE
- `warnings.SEVERITY_ORDER` — error > warning > info (PRD §A11)
- `warnings.Warning` — NamedTuple (code, severity, message_ko, details, stream, trace_id, timestamp)
- `warnings.build_inventory_warnings` — PRD §V3 fire
- `warnings.build_operating_rate_warning` — PRD §V5 fire
- `warnings.aggregate_warnings` — sort + dispatch
- `warnings.format_inventory_warning_ko` — Korean message
- `warnings.format_operating_rate_ko` — Korean message

Future (not in Story 3.1/3.2/3.3):
- `MonthInputAdapter` — AD-13 engine-input normalization; written when
  Epic 4 first_calc endpoint is in scope.
- `InputPromoter.promote` — AD-17 promotion from AI drafts; Story 3.4+.
"""

from __future__ import annotations

# Re-export public API at the package level so callers can do:
#   from packages.services.m2_input import compute_fte_for_daily
# rather than:
#   from packages.services.m2_input.labor_conversion import compute_fte_for_daily

from packages.services.m2_input.inventory_projection import (
    INVENTORY_PRODUCT_TYPES,
    LEDGER_REFERENCE_QUERY_STUB,
    InventoryMovement,
    build_inventory_projection,
    compute_closing_inventory,
    compute_opening_inventory,
)
from packages.services.m2_input.labor_conversion import (
    DEFAULT_PAYROLL,
    FteDisplay,
    PayType,
    PayTypeBreakdown,
    PayrollSettings,
    build_fte_display,
    compute_fte_for_daily,
    compute_fte_for_monthly,
    compute_fte_wage_for_daily,
    compute_fte_wage_for_monthly,
    compute_pay_type_breakdown,
    merge_payroll_settings,
    rollup_daily_fte,
)
from packages.services.m2_input.operating_rate import (
    DEFAULT_UNIT_TIME_HOURS,
    OPERATING_RATE_LIMIT_PCT,
    compute_operating_rate,
    compute_production_required_hours,
    compute_total_available_hours,
)
from packages.services.m2_input.stream_completion import (
    STREAM_LABELS_KO,
    STREAM_ORDER,
    STREAMS_FOR_INDUSTRY,
    MonthlyCompletionStatus,
    StreamCompletionStatus,
    compute_fte_wage_krw,
    compute_stream_completion,
    format_fte_headcount,
    is_all_streams_complete,
)
from packages.services.m2_input.warnings import (
    SEVERITY_ORDER,
    Warning,
    WarningCode,
    aggregate_warnings,
    build_inventory_warnings,
    build_operating_rate_warning,
    format_inventory_warning_ko,
    format_operating_rate_ko,
)

__all__ = [
    # stream_completion (Story 3.1)
    "STREAM_LABELS_KO",
    "STREAM_ORDER",
    "STREAMS_FOR_INDUSTRY",
    "MonthlyCompletionStatus",
    "StreamCompletionStatus",
    "compute_stream_completion",
    "is_all_streams_complete",
    "format_fte_headcount",
    "compute_fte_wage_krw",
    # labor_conversion (Story 3.2)
    "PayType",
    "PayrollSettings",
    "PayTypeBreakdown",
    "FteDisplay",
    "DEFAULT_PAYROLL",
    "merge_payroll_settings",
    "compute_pay_type_breakdown",
    "compute_fte_for_daily",
    "compute_fte_for_monthly",
    "compute_fte_wage_for_daily",
    "compute_fte_wage_for_monthly",
    "rollup_daily_fte",
    "build_fte_display",
    # inventory_projection (Story 3.3)
    "INVENTORY_PRODUCT_TYPES",
    "LEDGER_REFERENCE_QUERY_STUB",
    "InventoryMovement",
    "compute_opening_inventory",
    "compute_closing_inventory",
    "build_inventory_projection",
    # operating_rate (Story 3.3)
    "DEFAULT_UNIT_TIME_HOURS",
    "OPERATING_RATE_LIMIT_PCT",
    "compute_total_available_hours",
    "compute_production_required_hours",
    "compute_operating_rate",
    # warnings (Story 3.3)
    "SEVERITY_ORDER",
    "WarningCode",
    "Warning",
    "build_inventory_warnings",
    "build_operating_rate_warning",
    "aggregate_warnings",
    "format_inventory_warning_ko",
    "format_operating_rate_ko",
]
