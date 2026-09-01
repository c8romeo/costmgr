"""apps.api.modules.finops.reserved_capacity — Phase 21 FinOps Reserved Capacity Planning module.

Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning territory
(PRD §F37.1~§F37.8 verbatim + AD-49 (a)~(g) 7 sub-decisions).

This package provides the COMPOSITION LAYER across 5 prior FinOps modules:
- Phase 13 forecast — FinOps Forecasting & Capacity Planning (m21)
- Phase 14 optimization — FinOps Optimization & Rightsizing (m22)
- Phase 18 commitment — FinOps Cloud Commitment Management (m26)
- Phase 19 pricing — FinOps Pricing & Rate Cards (m27)
- Phase 20 multi_cloud — FinOps Multi-Cloud Cost Unified Reconciliation (m28)

Phase 21 wires these 5 modules into a single reserved_capacity composition
layer that produces a unified demand_forecast_id + capacity_plan_id +
commitment_recommendation_id + orchestration_id.

This package provides:
- `serializers` — m29_finops_reserved_capacity serializers NEW
  (Phase 20 wire `52dad7f` m28_finops_multi_cloud.multi_cloud_serializers EXTENSION
  pattern verbatim).
- `demand_forecast_aggregator` — 5-module cross-join (Phase 13+14+18+19+20
  weighted average) → ReservedCapacityDemandForecast TypedDict 16 fields
  (PRD §F37.1 verbatim).
- `capacity_planning_aggregator` — 6 reserved_capacity_tier enum (1y/3y ×
  no/partial/all upfront) + break_even_utilization_pct + capacity_headroom_pct
  + MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M →
  ReservedCapacityPlan TypedDict 18 fields (PRD §F37.2 verbatim).
- `commitment_recommendation_engine` — confidence_score (utilization_stability
  × 0.4 + historical_accuracy × 0.3 + demand_forecast_confidence_pct × 0.3) +
  risk_score (savings_pct × 0.4 + commitment_term × 0.3 + commitment_flexibility
  × 0.3) + execution_strategy 4 enum + high-value threshold (>= 10M KRW/year)
  → Epic 12 2FA 챌린지 mandatory → CommitmentRecommendation TypedDict 17 fields
  (PRD §F37.3 verbatim).
- `reserved_capacity_orchestrator` — composition_step_chain 5 step
  (demand_forecast → capacity_planning → commitment_recommendation → approval
  → execute) + 4 cadence schedule (daily 02:00 + weekly Mon 03:00 + monthly
  1st-day 04:00 + quarterly 1st-day 05:00 KST pytz) + dry-run mode →
  ReservedCapacityOrchestration TypedDict 19 fields (PRD §F37.4 verbatim).
- `scheduled_reserved_capacity_dispatch` — apscheduler==3.10.4 + pytz==2024.1 +
  4 cadence schedule KST + recipient resolver Slack + Email + S3 archive +
  LISTEN/NOTIFY 4 channel cross-tenant invalidation EXTENSION (Phase 13 wire
  `8b98030` LISTEN/NOTIFY pattern verbatim).
- `reserved_capacity_routes` — 8 endpoints (healthcheck + demand-forecast +
  capacity-plan + commitment-recommendation + orchestrate + dispatches +
  cadence-preview + dry-run) — P0 CRITICAL: created from start to avoid
  Phase 20 forgetting → Phase 20.5 retrofit pattern.

CR lessons applied (18종):
- CR 0-2 RLS — 8 tables + 1 preview table tenant_id selector + multi-tenant
  isolation.
- CR 1-1 audit-first INSERT — 8 NEW actions via emit_audit_typed
  (reserved_capacity_dashboard_viewed + demand_forecast_calculated +
  capacity_planning_recommended + commitment_recommendation_generated +
  reserved_capacity_dry_run_executed + reserved_capacity_kpi_refreshed +
  reserved_capacity_commitment_executed + reserved_capacity_orchestrator_triggered).
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — Client-only dashboard delegation.
- CR 4-3/4-4 — ReservedCapacityDemandForecast golden_diff + tenant-scoped
  result_hash.
- CR 9-6 commit message discipline.
- CR 11-3 honest-DEFER 41번째 — D-FINOPS-10 honestly DEFER 보존 (7개 세부 항목
  모두 Phase 21 territory 흡수 완료).
- CR 11-4 D-001~D-005 + P-015 — pure validator + SSOT.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
- A19 cohesion pattern 9 surface EXTENSION PASS.
- A36 SDR 검증 4-step 자동 적용.
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 + openpyxl==3.1.2
  + pandas==2.1.4 + xlsxwriter==3.1.9 + apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-49 FinOps Reserved Capacity Planning 신규 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

from apps.api.modules.finops.reserved_capacity.capacity_planning_aggregator import (
    plan_reserved_capacity,
    validate_capacity_plan,
)
from apps.api.modules.finops.reserved_capacity.commitment_recommendation_engine import (
    generate_commitment_recommendation,
    validate_commitment_recommendation,
)

# Phase 21 wire (cj-style 151번째) — Re-export aggregator functions from
# reserved_capacity submodules. Pattern mirrors Phase 20.5 wire (cj-style 147번째)
# multi_cloud/__init__.py re-export convention verbatim.
from apps.api.modules.finops.reserved_capacity.demand_forecast_aggregator import (
    aggregate_demand_forecast,
    validate_demand_forecast,
)
from apps.api.modules.finops.reserved_capacity.reserved_capacity_orchestrator import (
    orchestrate_reserved_capacity,
    validate_orchestration,
)
from apps.api.modules.finops.reserved_capacity.scheduled_reserved_capacity_dispatch import (
    dispatch_reserved_capacity_orchestration,
    validate_reserved_capacity_dispatch,
)
from apps.api.modules.finops.reserved_capacity.serializers import (
    ALL_EXECUTION_STRATEGIES,
    ALL_ORCHESTRATION_SCOPES,
    ALL_RESERVED_CAPACITY_CADENCES,
    ALL_RESERVED_CAPACITY_TIERS,
    RESERVED_CAPACITY_DEFAULTS,
    RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
    CommitmentRecommendation,
    ExecutionStrategy,
    OrchestrationScope,
    ReservedCapacityCadence,
    ReservedCapacityDemandForecast,
    ReservedCapacityOrchestration,
    ReservedCapacityPlan,
    ReservedCapacityTier,
)

__all__ = [
    "RESERVED_CAPACITY_ENGINE_MODEL_VERSION",
    "RESERVED_CAPACITY_DEFAULTS",
    "ReservedCapacityDemandForecast",
    "ReservedCapacityPlan",
    "CommitmentRecommendation",
    "ReservedCapacityOrchestration",
    "ReservedCapacityTier",
    "ALL_RESERVED_CAPACITY_TIERS",
    "ExecutionStrategy",
    "ALL_EXECUTION_STRATEGIES",
    "ReservedCapacityCadence",
    "ALL_RESERVED_CAPACITY_CADENCES",
    "OrchestrationScope",
    "ALL_ORCHESTRATION_SCOPES",
    # Phase 21 wire (cj-style 151번째) — aggregator function re-exports.
    "aggregate_demand_forecast",
    "validate_demand_forecast",
    "plan_reserved_capacity",
    "validate_capacity_plan",
    "generate_commitment_recommendation",
    "validate_commitment_recommendation",
    "orchestrate_reserved_capacity",
    "validate_orchestration",
    "dispatch_reserved_capacity_orchestration",
    "validate_reserved_capacity_dispatch",
]
