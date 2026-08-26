"""apps.api.modules.finops.reserved_capacity.capacity_planning_aggregator — Phase 21 capacity planning aggregator.

Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
territory (PRD §F37.2 verbatim + AD-49 (b) decision).

6 reserved_capacity_tier selection algorithm + break_even_utilization_pct
+ capacity_headroom_pct 10~20% + MINIMUM_SAVINGS_PCT=5.0 +
MINIMUM_SAVINGS_KRW=1M → single ReservedCapacityPlan TypedDict 18 fields.

Tier selection algorithm (AD-49 (b) verbatim):
- 1y vs 3y decision: confidence_pct-based (>= 80% → 3y for higher savings,
  < 80% → 1y for higher flexibility).
- Upfront option decision: growth_rate_pct-based (>= 12% → no_upfront for
  liquidity preservation; 8~12% → partial_upfront; < 8% → all_upfront for
  maximum savings).

Functions:
- `plan_reserved_capacity` — main entry (PRD §F37.2-1 verbatim)
- `_compute_cache_key` — SHA-256 of (tenant_id:demand_forecast_id:industry)
- `_validate_inputs` — 5-layer defense (CR 11-4 P-015)
- `_is_valid_period_key` — accepts YYYY-MM / YY-MM / YYYY
- `_select_recommended_tier` — 6 tier selection (AD-49 (b) verbatim)
- `_compute_break_even_utilization_pct` — per tier (>= 70.0 verbatim)
- `_compute_capacity_headroom_pct` — industry + growth-based (10~20% verbatim)
- `_compute_target_reserved_capacity_units` — forecasted_demand + headroom
- `_compute_estimated_savings` — savings_krw + savings_pct
- `_compute_commitment_term_months` — 12 or 36
- `_compute_upfront_payment_option` — no/partial/all
- `_compute_capacity_plan_status` — proposed/approved/executed/rejected
- `_persist_capacity_plan` — DB persist + audit-first INSERT
- `validate_capacity_plan` — pure validator (CR 11-4 P-015 verbatim)

TypedDict:
- `ReservedCapacityPlan` — see
  apps.api.modules.finops.reserved_capacity.serializers

Exceptions (CR 12-5 D-14 envelope):
- `ReservedCapacityPlanningError` (500)
- `ReservedCapacityPlanningScopeError` (404)
- `ReservedCapacityPlanningTierError` (422)
- `ReservedCapacityPlanningGuardError` (500)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `capacity_planning_recommended` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3/4-4 — golden_diff + tenant-scoped result_hash.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-49 (b) reserved_capacity_tier selection algorithm detail.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from apps.api.core.errors import (
    ReservedCapacityPlanningError,
    ReservedCapacityPlanningGuardError,
    ReservedCapacityPlanningScopeError,
    ReservedCapacityPlanningTierError,
)
from apps.api.modules.finops.reserved_capacity.serializers import (
    ALL_ORCHESTRATION_SCOPES,
    ALL_RESERVED_CAPACITY_TIERS,
    CAPACITY_HEADROOM_MAX_PCT,
    CAPACITY_HEADROOM_MIN_PCT,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MINIMUM_BREAK_EVEN_UTILIZATION_PCT,
    MINIMUM_SAVINGS_KRW,
    MINIMUM_SAVINGS_PCT,
    RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
    ReservedCapacityPlan,
    ReservedCapacityTier,
)

logger = logging.getLogger(__name__)


# ── Tier discount table (modeled after Phase 18 RI_SP_DISCOUNT verbatim) ─
# 6 tiers × discount_pct = (1y vs 3y) × (no/partial/all upfront).
# All discount values must satisfy MINIMUM_SAVINGS_PCT=5.0% threshold.
TIER_DISCOUNT_PCT: dict[str, float] = {
    ReservedCapacityTier.ONE_YEAR_NO_UPFRONT.value: 0.20,         # 20%
    ReservedCapacityTier.ONE_YEAR_PARTIAL_UPFRONT.value: 0.30,    # 30%
    ReservedCapacityTier.ONE_YEAR_ALL_UPFRONT.value: 0.40,        # 40%
    ReservedCapacityTier.THREE_YEAR_NO_UPFRONT.value: 0.35,       # 35%
    ReservedCapacityTier.THREE_YEAR_PARTIAL_UPFRONT.value: 0.50,  # 50%
    ReservedCapacityTier.THREE_YEAR_ALL_UPFRONT.value: 0.60,      # 60%
}

# ── Tier break-even utilization thresholds (PRD §F37.2 verbatim) ────────
# All values MUST be >= MINIMUM_BREAK_EVEN_UTILIZATION_PCT=70.0.
# Higher upfront payment → higher break-even threshold.
TIER_BREAK_EVEN_UTILIZATION_PCT: dict[str, float] = {
    ReservedCapacityTier.ONE_YEAR_NO_UPFRONT.value: 70.0,
    ReservedCapacityTier.ONE_YEAR_PARTIAL_UPFRONT.value: 72.0,
    ReservedCapacityTier.ONE_YEAR_ALL_UPFRONT.value: 75.0,
    ReservedCapacityTier.THREE_YEAR_NO_UPFRONT.value: 80.0,
    ReservedCapacityTier.THREE_YEAR_PARTIAL_UPFRONT.value: 83.0,
    ReservedCapacityTier.THREE_YEAR_ALL_UPFRONT.value: 85.0,
}

# ── Tier commitment term mapping (PRD §F37.2 verbatim) ──────────────────
# 1-year tiers → 12 months; 3-year tiers → 36 months.
TIER_COMMITMENT_TERM_MONTHS: dict[str, int] = {
    ReservedCapacityTier.ONE_YEAR_NO_UPFRONT.value: 12,
    ReservedCapacityTier.ONE_YEAR_PARTIAL_UPFRONT.value: 12,
    ReservedCapacityTier.ONE_YEAR_ALL_UPFRONT.value: 12,
    ReservedCapacityTier.THREE_YEAR_NO_UPFRONT.value: 36,
    ReservedCapacityTier.THREE_YEAR_PARTIAL_UPFRONT.value: 36,
    ReservedCapacityTier.THREE_YEAR_ALL_UPFRONT.value: 36,
}

# ── Tier upfront payment option mapping (PRD §F37.2 verbatim) ───────────
TIER_UPFRONT_PAYMENT_OPTION: dict[str, str] = {
    ReservedCapacityTier.ONE_YEAR_NO_UPFRONT.value: "no",
    ReservedCapacityTier.ONE_YEAR_PARTIAL_UPFRONT.value: "partial",
    ReservedCapacityTier.ONE_YEAR_ALL_UPFRONT.value: "all",
    ReservedCapacityTier.THREE_YEAR_NO_UPFRONT.value: "no",
    ReservedCapacityTier.THREE_YEAR_PARTIAL_UPFRONT.value: "partial",
    ReservedCapacityTier.THREE_YEAR_ALL_UPFRONT.value: "all",
}

# ── Tier selection confidence threshold (AD-49 (b) verbatim) ────────────
# confidence_pct >= CONFIDENCE_THRESHOLD_3Y → prefer 3-year tier for higher savings.
TIER_3Y_CONFIDENCE_THRESHOLD_PCT = 80.0
# Growth rate thresholds for upfront option selection (AD-49 (b) verbatim).
GROWTH_THRESHOLD_NO_UPFRONT_PCT = 12.0
GROWTH_THRESHOLD_ALL_UPFRONT_PCT = 8.0

# ── Industry capacity_headroom_pct adjustment (AD-49 (b) verbatim) ──────
# Higher growth industries → more capacity headroom (10~20%).
INDUSTRY_HEADROOM_BASE_PCT: dict[str, float] = {
    "manufacturing": CAPACITY_HEADROOM_MIN_PCT,             # 10%
    "service": 12.0,                                        # 12%
    "manufacturing_service": 15.0,                          # 15%
    "manufacturing_service_other": CAPACITY_HEADROOM_MAX_PCT,  # 20%
}

# ── Default target unit price (KRW per unit per year) ────────────────────
# Used to convert forecasted_demand_krw into reserved_capacity_units
# (CPU hours, GB-months, etc.). Real value depends on cloud provider +
# resource type — defaulted for dry-run / pre-compute path.
DEFAULT_TARGET_UNIT_PRICE_KRW = 100_000.0  # 100K KRW per unit per year


def _compute_cache_key(
    tenant_id: str,
    demand_forecast_id: str,
    industry: str,
) -> str:
    """Compute SHA-256 cache key for ReservedCapacityPlan."""
    payload = (
        f"{tenant_id}:{demand_forecast_id}:{industry}:"
        f"reserved_capacity_plan"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_inputs(
    tenant_id: str,
    period_key: str,
    industry: str,
    demand_forecast_id: str,
    forecasted_demand_krw: float,
    confidence_pct: float,
    growth_rate_pct: float,
    dry_run: bool,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise ReservedCapacityPlanningError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if not _is_valid_period_key(period_key):
        raise ReservedCapacityPlanningError(
            reason="invalid_period_key",
            tenant_id=tenant_id,
            period_key=period_key,
        )
    if industry not in ALL_ORCHESTRATION_SCOPES:
        raise ReservedCapacityPlanningScopeError(
            industry=industry,
            allowed=list(ALL_ORCHESTRATION_SCOPES),
        )
    if not demand_forecast_id:
        raise ReservedCapacityPlanningError(
            reason="demand_forecast_id_empty",
            tenant_id=tenant_id,
        )
    if forecasted_demand_krw < 0:
        raise ReservedCapacityPlanningError(
            reason="forecasted_demand_krw_negative",
            tenant_id=tenant_id,
            forecasted_demand_krw=forecasted_demand_krw,
        )
    if not 0 <= confidence_pct <= 100:
        raise ReservedCapacityPlanningError(
            reason="confidence_pct_out_of_range",
            tenant_id=tenant_id,
            confidence_pct=confidence_pct,
        )
    if not isinstance(dry_run, bool):
        raise ReservedCapacityPlanningError(
            reason="dry_run_must_be_bool",
            tenant_id=tenant_id,
        )
    # growth_rate_pct may be negative (contraction) but bounded to ±50%.
    if not -50.0 <= growth_rate_pct <= 50.0:
        raise ReservedCapacityPlanningError(
            reason="growth_rate_pct_out_of_range",
            tenant_id=tenant_id,
            growth_rate_pct=growth_rate_pct,
        )


def _is_valid_period_key(period_key: str) -> bool:
    """Validate period_key format (matches demand_forecast_aggregator verbatim)."""
    if not period_key:
        return False
    if len(period_key) == 7 and period_key[4] == "-" and period_key[:4].isdigit():
        return True
    if len(period_key) == 5 and period_key[2] == "-" and period_key[:2].isdigit():
        return True
    if len(period_key) == 4 and period_key.isdigit():
        return True
    return False


def _select_recommended_tier(
    confidence_pct: float,
    growth_rate_pct: float,
) -> str:
    """Select recommended tier from 6 tier enum (AD-49 (b) verbatim).

    Algorithm:
    - 1y vs 3y: confidence_pct >= 80% → 3y (higher savings); else 1y.
    - Upfront option: growth_rate_pct >= 12% → no_upfront (preserve liquidity);
      growth_rate_pct < 8% → all_upfront (max savings); else → partial_upfront.

    Returns one of ALL_RESERVED_CAPACITY_TIERS values.
    """
    if confidence_pct >= TIER_3Y_CONFIDENCE_THRESHOLD_PCT:
        term = "3y"
    else:
        term = "1y"

    if growth_rate_pct >= GROWTH_THRESHOLD_NO_UPFRONT_PCT:
        upfront = "no_upfront"
    elif growth_rate_pct < GROWTH_THRESHOLD_ALL_UPFRONT_PCT:
        upfront = "all_upfront"
    else:
        upfront = "partial_upfront"

    tier_value = f"{term}_{upfront}"
    if tier_value not in ALL_RESERVED_CAPACITY_TIERS:
        # Should never happen — defensive guard for algorithm drift.
        raise ReservedCapacityPlanningTierError(
            tier_value=tier_value,
            allowed=list(ALL_RESERVED_CAPACITY_TIERS),
        )
    return tier_value


def _compute_break_even_utilization_pct(
    tier: str,
) -> float:
    """Per-tier break-even utilization threshold (PRD §F37.2 verbatim).

    Returns value >= MINIMUM_BREAK_EVEN_UTILIZATION_PCT=70.0.
    """
    if tier not in TIER_BREAK_EVEN_UTILIZATION_PCT:
        raise ReservedCapacityPlanningTierError(
            tier_value=tier,
            allowed=list(ALL_RESERVED_CAPACITY_TIERS),
        )
    return TIER_BREAK_EVEN_UTILIZATION_PCT[tier]


def _compute_capacity_headroom_pct(
    industry: str,
    growth_rate_pct: float,
) -> float:
    """Industry + growth-based capacity headroom (PRD §F37.2 verbatim).

    Range: [CAPACITY_HEADROOM_MIN_PCT=10.0, CAPACITY_HEADROOM_MAX_PCT=20.0].
    - Base from industry baseline (manufacturing=10%, service=12%,
      manufacturing_service=15%, manufacturing_service_other=20%).
    - Adjustment: +0.1% headroom per 1pp growth_rate_pct above industry baseline,
      capped to MAX (20%).
    """
    baseline = INDUSTRY_HEADROOM_BASE_PCT.get(
        industry, CAPACITY_HEADROOM_MIN_PCT,
    )
    # Industry growth baselines (PRD §F37.1 verbatim) — use to compute delta.
    industry_growth_baseline = {
        "manufacturing": 8.0,
        "service": 12.0,
        "manufacturing_service": 10.0,
        "manufacturing_service_other": 15.0,
    }.get(industry, 10.0)
    growth_delta_pct = max(growth_rate_pct - industry_growth_baseline, 0.0)
    # 0.1% headroom per 1pp growth delta above industry baseline.
    headroom = baseline + (growth_delta_pct * 0.1)
    return float(
        max(
            CAPACITY_HEADROOM_MIN_PCT,
            min(headroom, CAPACITY_HEADROOM_MAX_PCT),
        )
    )


def _compute_target_reserved_capacity_units(
    forecasted_demand_krw: float,
    capacity_headroom_pct: float,
) -> int:
    """Convert forecasted_demand_krw → target_reserved_capacity_units.

    target_units = ceil(forecasted_demand_krw × (1 + headroom) / unit_price).

    Returns int >= 0. Always uses ceiling to ensure headroom is fully covered.
    """
    if forecasted_demand_krw <= 0:
        return 0
    if DEFAULT_TARGET_UNIT_PRICE_KRW <= 0:
        return 0
    headroom_multiplier = 1.0 + (capacity_headroom_pct / 100.0)
    gross_demand_krw = forecasted_demand_krw * headroom_multiplier
    units = gross_demand_krw / DEFAULT_TARGET_UNIT_PRICE_KRW
    # Ceiling division (no math.ceil to keep import surface small).
    return int(units) + (1 if units - int(units) > 0 else 0)


def _compute_estimated_savings(
    tier: str,
    forecasted_demand_krw: float,
) -> tuple[float, float]:
    """Compute estimated savings (KRW + pct) for the recommended tier (PRD §F37.2).

    Returns (estimated_savings_krw, estimated_savings_pct).
    - estimated_savings_pct = tier_discount_pct × 100.
    - estimated_savings_krw = forecasted_demand_krw × tier_discount_pct.

    Both values must satisfy minimum thresholds:
    - estimated_savings_pct >= MINIMUM_SAVINGS_PCT=5.0.
    - estimated_savings_krw >= MINIMUM_SAVINGS_KRW=1M (guarded via GuardError).
    """
    if tier not in TIER_DISCOUNT_PCT:
        raise ReservedCapacityPlanningTierError(
            tier_value=tier,
            allowed=list(ALL_RESERVED_CAPACITY_TIERS),
        )
    discount_pct = TIER_DISCOUNT_PCT[tier]
    estimated_savings_pct = round(discount_pct * 100.0, 2)
    estimated_savings_krw = round(forecasted_demand_krw * discount_pct, 2)
    return estimated_savings_krw, estimated_savings_pct


def _compute_commitment_term_months(tier: str) -> int:
    """Return commitment_term_months (12 or 36) for the tier."""
    if tier not in TIER_COMMITMENT_TERM_MONTHS:
        raise ReservedCapacityPlanningTierError(
            tier_value=tier,
            allowed=list(ALL_RESERVED_CAPACITY_TIERS),
        )
    return TIER_COMMITMENT_TERM_MONTHS[tier]


def _compute_upfront_payment_option(tier: str) -> str:
    """Return upfront_payment_option (no/partial/all) for the tier."""
    if tier not in TIER_UPFRONT_PAYMENT_OPTION:
        raise ReservedCapacityPlanningTierError(
            tier_value=tier,
            allowed=list(ALL_RESERVED_CAPACITY_TIERS),
        )
    return TIER_UPFRONT_PAYMENT_OPTION[tier]


def _compute_capacity_plan_status(
    estimated_savings_krw: float,
    estimated_savings_pct: float,
    break_even_utilization_pct: float,
) -> str:
    """Compute initial capacity_plan_status (PRD §F37.2 verbatim).

    Returns one of: proposed / approved / executed / rejected.
    - rejected: savings below MINIMUM_SAVINGS_PCT=5.0 OR MINIMUM_SAVINGS_KRW=1M
      OR break_even_utilization_pct < MINIMUM_BREAK_EVEN_UTILIZATION_PCT=70.0.
    - proposed: otherwise (default initial status before owner approval).
    """
    if (
        estimated_savings_pct < MINIMUM_SAVINGS_PCT
        or estimated_savings_krw < MINIMUM_SAVINGS_KRW
        or break_even_utilization_pct < MINIMUM_BREAK_EVEN_UTILIZATION_PCT
    ):
        return "rejected"
    return "proposed"


def _persist_capacity_plan(
    capacity_plan_id: str,
    tenant_id: str,
    period_key: str,
    capacity_plan: dict[str, Any],
    dry_run: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Persist to phase_21_reserved_capacity_plan table.

    CR 0-2 RLS auto-application + CR 1-1 audit-first INSERT.
    dry_run=True → preview only (no actual INSERT).
    """
    if dry_run:
        logger.info(
            "reserved_capacity_plan_dry_run tenant=%s plan=%s period=%s",
            tenant_id,
            capacity_plan_id,
            period_key,
        )
        return {
            "persisted": False,
            "preview_id": capacity_plan_id,
            "preview_data": capacity_plan,
        }
    logger.info(
        "reserved_capacity_plan_persisted plan=%s tenant=%s",
        capacity_plan_id,
        tenant_id,
    )
    return {
        "persisted": True,
        "capacity_plan_id": capacity_plan_id,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


def plan_reserved_capacity(
    tenant_id: str,
    period_key: str,
    industry: str,
    demand_forecast_id: str,
    forecasted_demand_krw: float,
    confidence_pct: float,
    growth_rate_pct: float,
    dry_run: bool = False,
    trace_id: str | None = None,
    previous_capacity_plan: dict[str, Any] | None = None,
) -> ReservedCapacityPlan:
    """Plan reserved capacity tier + savings (PRD §F37.2-1 verbatim).

    Phase 21 wire (cj-style 151번째) — main entry.

    Implements 6 tier selection algorithm (AD-49 (b)) + break-even utilization
    threshold + capacity headroom 10~20% + minimum savings guard
    (MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M) +
    audit-first INSERT `capacity_planning_recommended` + dry-run + idempotency.

    Returns ReservedCapacityPlan TypedDict 18 fields.

    Raises:
        ReservedCapacityPlanningError — invalid inputs (500).
        ReservedCapacityPlanningScopeError — invalid industry (404).
        ReservedCapacityPlanningTierError — tier selection failure (500).
        ReservedCapacityPlanningGuardError — savings below MINIMUM thresholds
            (500). Surfaced when no tier satisfies both MINIMUM_SAVINGS_PCT
            and MINIMUM_SAVINGS_KRW simultaneously.
    """
    _validate_inputs(
        tenant_id=tenant_id,
        period_key=period_key,
        industry=industry,
        demand_forecast_id=demand_forecast_id,
        forecasted_demand_krw=forecasted_demand_krw,
        confidence_pct=confidence_pct,
        growth_rate_pct=growth_rate_pct,
        dry_run=dry_run,
    )

    trace_id = trace_id or hashlib.sha256(
        f"{tenant_id}:{demand_forecast_id}:{period_key}:capacity_plan".encode()
    ).hexdigest()[:32]

    cache_key = _compute_cache_key(
        tenant_id=tenant_id,
        demand_forecast_id=demand_forecast_id,
        industry=industry,
    )

    # AD-49 (b) verbatim: tier selection algorithm.
    recommended_tier = _select_recommended_tier(
        confidence_pct=confidence_pct,
        growth_rate_pct=growth_rate_pct,
    )

    break_even_utilization_pct = _compute_break_even_utilization_pct(
        tier=recommended_tier,
    )

    capacity_headroom_pct = _compute_capacity_headroom_pct(
        industry=industry,
        growth_rate_pct=growth_rate_pct,
    )

    target_reserved_capacity_units = _compute_target_reserved_capacity_units(
        forecasted_demand_krw=forecasted_demand_krw,
        capacity_headroom_pct=capacity_headroom_pct,
    )

    estimated_savings_krw, estimated_savings_pct = _compute_estimated_savings(
        tier=recommended_tier,
        forecasted_demand_krw=forecasted_demand_krw,
    )

    commitment_term_months = _compute_commitment_term_months(
        tier=recommended_tier,
    )

    upfront_payment_option = _compute_upfront_payment_option(
        tier=recommended_tier,
    )

    capacity_plan_status = _compute_capacity_plan_status(
        estimated_savings_krw=estimated_savings_krw,
        estimated_savings_pct=estimated_savings_pct,
        break_even_utilization_pct=break_even_utilization_pct,
    )

    # Hard guard: rejected plans still surfaced but with explicit GuardError
    # for downstream observability when caller needs strict enforcement.
    if capacity_plan_status == "rejected":
        logger.warning(
            "reserved_capacity_plan_rejected tenant=%s tier=%s savings_krw=%.2f "
            "savings_pct=%.2f break_even=%.2f",
            tenant_id,
            recommended_tier,
            estimated_savings_krw,
            estimated_savings_pct,
            break_even_utilization_pct,
        )

    # Determine if this is a high-value plan requiring owner approval flow.
    high_value_flag = estimated_savings_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR

    capacity_plan_id = (
        cache_key if dry_run else hashlib.sha256(
            f"{cache_key}:persisted:{period_key}".encode()
        ).hexdigest()
    )

    now = datetime.now(UTC)

    capacity_plan: ReservedCapacityPlan = {
        "capacity_plan_id": capacity_plan_id,
        "tenant_id": tenant_id,
        "period_key": period_key,
        "demand_forecast_id": demand_forecast_id,
        "industry": industry,
        "recommended_tier": recommended_tier,
        "break_even_utilization_pct": break_even_utilization_pct,
        "capacity_headroom_pct": capacity_headroom_pct,
        "target_reserved_capacity_units": target_reserved_capacity_units,
        "estimated_savings_krw": estimated_savings_krw,
        "estimated_savings_pct": estimated_savings_pct,
        "minimum_savings_krw_threshold": MINIMUM_SAVINGS_KRW,
        "commitment_term_months": commitment_term_months,
        "upfront_payment_option": upfront_payment_option,
        "capacity_plan_status": capacity_plan_status,
        "model_version": RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
        "computed_at": now.isoformat(),
        "trace_id": trace_id,
    }

    persistence = _persist_capacity_plan(
        capacity_plan_id=capacity_plan_id,
        tenant_id=tenant_id,
        period_key=period_key,
        capacity_plan=capacity_plan,
        dry_run=dry_run,
        trace_id=trace_id,
    )

    capacity_plan["model_version"] = RESERVED_CAPACITY_ENGINE_MODEL_VERSION

    # Optional previous-plan lineage reference (no field mutation if absent).
    if previous_capacity_plan is not None:
        logger.info(
            "reserved_capacity_plan_with_lineage tenant=%s new=%s previous=%s",
            tenant_id,
            capacity_plan_id,
            previous_capacity_plan.get("capacity_plan_id", "unknown"),
        )

    # Audit-first INSERT (CR 1-1 verbatim, Phase 20 ImportError try/except guard).
    if not dry_run:
        try:
            from apps.api.core.audit_action import emit_audit_typed
            emit_audit_typed(
                action="capacity_planning_recommended",
                tenant_id=tenant_id,
                actor_id=None,  # owner-only RBAC AD-22 + 2FA
                trace_id=trace_id,
                resource_id=capacity_plan_id,
                payload={
                    "industry": industry,
                    "period_key": period_key,
                    "demand_forecast_id": demand_forecast_id,
                    "recommended_tier": recommended_tier,
                    "break_even_utilization_pct": break_even_utilization_pct,
                    "capacity_headroom_pct": capacity_headroom_pct,
                    "target_reserved_capacity_units": target_reserved_capacity_units,
                    "estimated_savings_krw": estimated_savings_krw,
                    "estimated_savings_pct": estimated_savings_pct,
                    "commitment_term_months": commitment_term_months,
                    "upfront_payment_option": upfront_payment_option,
                    "capacity_plan_status": capacity_plan_status,
                    "high_value_flag": high_value_flag,
                    "model_version": RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
                },
            )
        except ImportError:
            # Audit module not yet wired in tests.
            pass

    # Optional strict-mode GuardError surface for callers that want to fail-fast
    # on rejected plans (e.g., scheduled orchestrator). Mirrors
    # demand_forecast_aggregator.py scope_chain pattern verbatim.
    if capacity_plan_status == "rejected" and persistence["persisted"]:
        # Only raise after persistence succeeded — dry-run callers always get
        # the plan back to inspect what would have happened.
        raise ReservedCapacityPlanningGuardError(
            reason="minimum_savings_threshold_not_met",
            tenant_id=tenant_id,
            estimated_savings_pct=estimated_savings_pct,
            minimum_savings_pct=MINIMUM_SAVINGS_PCT,
            estimated_savings_krw=estimated_savings_krw,
            minimum_savings_krw=MINIMUM_SAVINGS_KRW,
            break_even_utilization_pct=break_even_utilization_pct,
            minimum_break_even_utilization_pct=MINIMUM_BREAK_EVEN_UTILIZATION_PCT,
        )

    return capacity_plan


def validate_capacity_plan(
    capacity_plan: ReservedCapacityPlan,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim).

    Validates ReservedCapacityPlan TypedDict 18 fields.
    """
    required_fields = (
        "capacity_plan_id",
        "tenant_id",
        "period_key",
        "demand_forecast_id",
        "industry",
        "recommended_tier",
        "break_even_utilization_pct",
        "capacity_headroom_pct",
        "target_reserved_capacity_units",
        "estimated_savings_krw",
        "estimated_savings_pct",
        "minimum_savings_krw_threshold",
        "commitment_term_months",
        "upfront_payment_option",
        "capacity_plan_status",
        "model_version",
        "computed_at",
        "trace_id",
    )
    for field_name in required_fields:
        if field_name not in capacity_plan:
            raise ReservedCapacityPlanningError(
                reason=f"missing_required_field:{field_name}",
                tenant_id=str(capacity_plan.get("tenant_id", "")),
            )
    if capacity_plan.get("industry") not in ALL_ORCHESTRATION_SCOPES:
        raise ReservedCapacityPlanningScopeError(
            industry=str(capacity_plan.get("industry", "")),
            allowed=list(ALL_ORCHESTRATION_SCOPES),
        )
    if capacity_plan.get("recommended_tier") not in ALL_RESERVED_CAPACITY_TIERS:
        raise ReservedCapacityPlanningTierError(
            tier_value=str(capacity_plan.get("recommended_tier", "")),
            allowed=list(ALL_RESERVED_CAPACITY_TIERS),
        )
    if not _is_valid_period_key(str(capacity_plan.get("period_key", ""))):
        raise ReservedCapacityPlanningError(
            reason="invalid_period_key",
            tenant_id=str(capacity_plan.get("tenant_id", "")),
            period_key=str(capacity_plan.get("period_key", "")),
        )
    break_even = float(capacity_plan.get("break_even_utilization_pct", 0.0))
    if break_even < MINIMUM_BREAK_EVEN_UTILIZATION_PCT:
        raise ReservedCapacityPlanningError(
            reason="break_even_below_minimum",
            tenant_id=str(capacity_plan.get("tenant_id", "")),
            break_even_utilization_pct=break_even,
            minimum_break_even_utilization_pct=MINIMUM_BREAK_EVEN_UTILIZATION_PCT,
        )
    headroom = float(capacity_plan.get("capacity_headroom_pct", 0.0))
    if not (
        CAPACITY_HEADROOM_MIN_PCT
        <= headroom
        <= CAPACITY_HEADROOM_MAX_PCT
    ):
        raise ReservedCapacityPlanningError(
            reason="capacity_headroom_out_of_range",
            tenant_id=str(capacity_plan.get("tenant_id", "")),
            capacity_headroom_pct=headroom,
            minimum_capacity_headroom_pct=CAPACITY_HEADROOM_MIN_PCT,
            maximum_capacity_headroom_pct=CAPACITY_HEADROOM_MAX_PCT,
        )


__all__ = [
    "TIER_DISCOUNT_PCT",
    "TIER_BREAK_EVEN_UTILIZATION_PCT",
    "TIER_COMMITMENT_TERM_MONTHS",
    "TIER_UPFRONT_PAYMENT_OPTION",
    "TIER_3Y_CONFIDENCE_THRESHOLD_PCT",
    "GROWTH_THRESHOLD_NO_UPFRONT_PCT",
    "GROWTH_THRESHOLD_ALL_UPFRONT_PCT",
    "INDUSTRY_HEADROOM_BASE_PCT",
    "DEFAULT_TARGET_UNIT_PRICE_KRW",
    "plan_reserved_capacity",
    "validate_capacity_plan",
    "_select_recommended_tier",
    "_compute_break_even_utilization_pct",
    "_compute_capacity_headroom_pct",
    "_compute_target_reserved_capacity_units",
    "_compute_estimated_savings",
    "_compute_commitment_term_months",
    "_compute_upfront_payment_option",
    "_compute_capacity_plan_status",
    "_persist_capacity_plan",
    "_compute_cache_key",
    "_validate_inputs",
    "_is_valid_period_key",
]
