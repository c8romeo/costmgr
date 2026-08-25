"""apps.api.modules.finops.pricing.rate_card_aggregator — Pricing rate card aggregator.

Phase 19 wire (cj-style 139번째) — FinOps Pricing, Rate Card & TCO
Modeling territory (PRD §F35.1 verbatim + AD-46 (a) decision).

8-module cross-rollup aggregator + 5-cloud-provider cross-rollup:
Phase 11 showback + Phase 12 anomaly + Phase 13 forecast + Phase 14
optimization + Phase 15 tag_governance + Phase 16 executive + Phase 17
sustainability + Phase 18 commitment → single RateCardInventory TypedDict
18 fields.

Functions:
- `aggregate_rate_card_inventory` — main entry (PRD §F35.1-1 verbatim)
- `compute_showback_blended_rate` — Phase 11 showback_total_krw / hours
- `compute_anomaly_rate_impact` — Phase 12 anomaly_count_30d × avg_rate
- `compute_forecast_rate_trajectory` — Phase 13 forecast_rate_30d_pct
- `compute_optimization_effective_discount` — Phase 14 optimization_savings_krw
- `compute_tag_governance_allocation_pct` — Phase 15 tag_compliance_pct
- `compute_executive_unit_economics` — Phase 16 executive cost_per_user baseline
- `compute_sustainability_carbon_adjusted_rate` — Phase 17 carbon_intensity × rate
- `compute_commitment_discount_baseline` — Phase 18 commitment savings_realized_krw
- `compute_cloud_provider_breakdown` — 5-cloud-provider breakdown (AWS + Azure + GCP + Naver + KT)
- `compute_pricing_model_breakdown` — 6-pricing-model breakdown (on_demand + 1y_ri + 3y_ri + 1y_sp + 3y_sp + savings_plan)
- `compute_unit_metric_breakdown` — 4-unit-metric breakdown (cost_per_user + cost_per_transaction + cost_per_request + cost_per_hour)
- `validate_rate_card_inventory` — pure validator (CR 11-4 P-015 verbatim)

TypedDict:
- `RateCardInventory` — see apps.api.modules.finops.pricing.serializers

Exceptions (CR 12-5 D-14 envelope):
- `PricingAggregationError` (500)
- `PricingScopeError` (404)
- `PricingPeriodError` (422)
- `PricingCrossModuleJoinError` (500)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `pricing_dashboard_viewed` BEFORE view.
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3/4-4 — RateCardInventory golden_diff + tenant-scoped result_hash.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-46 FinOps Pricing, Rate Card & TCO Modeling (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from apps.api.core.errors import (
    PricingAggregationError,
    PricingCrossModuleJoinError,
    PricingPeriodError,
    PricingScopeError,
)
from apps.api.modules.finops.pricing.serializers import (
    ALL_PRICING_CLOUD_PROVIDERS,
    ALL_PRICING_MODELS,
    ALL_PRICING_SCOPE_TYPES,
    ALL_PRICING_UNIT_METRICS,
    PRICING_DEFAULTS,
    PRICING_ENGINE_MODEL_VERSION,
    RateCardInventory,
)

logger = logging.getLogger(__name__)


def _compute_cache_key(
    tenant_id: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
) -> str:
    """Compute SHA-256 cache key for RateCardInventory."""
    payload = f"{tenant_id}:{scope_type}:{scope_id}:{period_key}:pricing"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_inputs(
    tenant_id: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise PricingAggregationError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if scope_type not in ALL_PRICING_SCOPE_TYPES:
        raise PricingScopeError(
            scope_type=scope_type,
            allowed=list(ALL_PRICING_SCOPE_TYPES),
        )
    if not scope_id:
        raise PricingScopeError(
            scope_type=scope_type,
            allowed=list(ALL_PRICING_SCOPE_TYPES),
        )
    # Period key: "YYYY-MM", "YYYY-QN", or "YYYY".
    if not _is_valid_period_key(period_key):
        raise PricingPeriodError(
            period_key=period_key,
        )


def _is_valid_period_key(period_key: str) -> bool:
    """Validate period_key format."""
    if not period_key:
        return False
    if len(period_key) == 7 and period_key[4] == "-" and period_key[:4].isdigit():
        try:
            month = int(period_key[5:])
            return 1 <= month <= 12
        except ValueError:
            return False
    if len(period_key) == 7 and period_key[5] == "Q" and period_key[:4].isdigit():
        try:
            quarter = int(period_key[6:])
            return 1 <= quarter <= 4
        except ValueError:
            return False
    if len(period_key) == 4 and period_key.isdigit():
        return True
    return False


def _get_industry_unit_economics_baseline(industry: str = "manufacturing") -> float:
    """Return unit_economics_score baseline for tenant industry.

    Phase 19 wire (cj-style 139번째) — 4-industry baseline per AD-46 (e)
    verbatim:
    - manufacturing ≤ 1.2 unit_economics_score baseline
    - service ≤ 0.8 unit_economics_score baseline
    - manufacturing_service ≤ 1.0 unit_economics_score baseline
    - manufacturing_service_other ≤ 1.1 unit_economics_score baseline

    Defaults to manufacturing when industry is unspecified or unknown.
    """
    baselines = PRICING_DEFAULTS.get(
        "unit_economics_score_industry_baselines",
        {
            "manufacturing": 1.2,
            "service": 0.8,
            "manufacturing_service": 1.0,
            "manufacturing_service_other": 1.1,
        },
    )
    return float(baselines.get(industry, baselines["manufacturing"]))


def _compute_pricing_model_multiplier(pricing_model: str) -> float:
    """Return on_demand multiplier for the given pricing_model.

    Phase 19 wire (cj-style 139번째) — 6-pricing-model multiplier matrix
    per AD-46 (a) verbatim (PRICING_DEFAULTS dict).
    """
    multiplier_map = {
        "on_demand": 1.0,
        "1y_ri": PRICING_DEFAULTS["on_demand_multiplier_1y_ri"],
        "3y_ri": PRICING_DEFAULTS["on_demand_multiplier_3y_ri"],
        "1y_sp": PRICING_DEFAULTS["on_demand_multiplier_1y_sp"],
        "3y_sp": PRICING_DEFAULTS["on_demand_multiplier_3y_sp"],
        "savings_plan": PRICING_DEFAULTS["on_demand_multiplier_savings_plan"],
    }
    return float(multiplier_map.get(pricing_model, 1.0))


def compute_showback_blended_rate(
    showback_total_krw: float,
    total_compute_hours: float,
) -> float:
    """Phase 11 showback blended rate extraction (KRW/hour).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if total_compute_hours <= 0:
        return 0.0
    return float(showback_total_krw) / float(total_compute_hours)


def compute_anomaly_rate_impact(
    anomaly_count_30d: int,
    avg_anomaly_cost_krw: float,
) -> float:
    """Phase 12 anomaly rate impact (KRW).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    return float(anomaly_count_30d) * float(avg_anomaly_cost_krw)


def compute_forecast_rate_trajectory(
    forecast_30d_krw: float,
    current_30d_krw: float,
) -> float:
    """Phase 13 forecast rate trajectory (% delta over 30 days).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if current_30d_krw == 0:
        return 0.0
    return ((float(forecast_30d_krw) - float(current_30d_krw)) / float(current_30d_krw)) * 100.0


def compute_optimization_effective_discount(
    optimization_savings_krw: float,
    on_demand_baseline_krw: float,
) -> float:
    """Phase 14 optimization effective discount (% saved vs on_demand).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if on_demand_baseline_krw == 0:
        return 0.0
    return (float(optimization_savings_krw) / float(on_demand_baseline_krw)) * 100.0


def compute_tag_governance_allocation_pct(
    tagged_cost_krw: float,
    total_cost_krw: float,
) -> float:
    """Phase 15 tag_governance allocation_pct (% of cost with proper tags).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if total_cost_krw == 0:
        return 0.0
    return (float(tagged_cost_krw) / float(total_cost_krw)) * 100.0


def compute_executive_unit_economics(
    total_cost_krw: float,
    active_user_count: int,
) -> float:
    """Phase 16 executive unit_economics — cost per active user (KRW).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if active_user_count <= 0:
        return 0.0
    return float(total_cost_krw) / float(active_user_count)


def compute_sustainability_carbon_adjusted_rate(
    carbon_intensity_kgco2e_per_krw: float,
    blended_rate_krw_per_hour: float,
) -> float:
    """Phase 17 carbon-adjusted rate (kgCO2e per hour).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    return float(carbon_intensity_kgco2e_per_krw) * float(blended_rate_krw_per_hour)


def compute_commitment_discount_baseline(
    commitment_savings_krw: float,
    on_demand_baseline_krw: float,
) -> float:
    """Phase 18 commitment discount baseline (% saved).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if on_demand_baseline_krw == 0:
        return 0.0
    return (float(commitment_savings_krw) / float(on_demand_baseline_krw)) * 100.0


def compute_cloud_provider_breakdown(
    aws_krw: float,
    azure_krw: float,
    gcp_krw: float,
    naver_krw: float,
    kt_krw: float,
) -> dict[str, float]:
    """5-cloud-provider cost breakdown (Phase 19 AD-46 (a) verbatim).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    return {
        "aws": float(aws_krw),
        "azure": float(azure_krw),
        "gcp": float(gcp_krw),
        "naver": float(naver_krw),
        "kt": float(kt_krw),
    }


def compute_pricing_model_breakdown(
    on_demand_krw: float,
    one_year_ri_krw: float,
    three_year_ri_krw: float,
    one_year_sp_krw: float,
    three_year_sp_krw: float,
    savings_plan_krw: float,
) -> dict[str, float]:
    """6-pricing-model cost breakdown (Phase 19 AD-46 (a) verbatim).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    return {
        "on_demand": float(on_demand_krw),
        "1y_ri": float(one_year_ri_krw),
        "3y_ri": float(three_year_ri_krw),
        "1y_sp": float(one_year_sp_krw),
        "3y_sp": float(three_year_sp_krw),
        "savings_plan": float(savings_plan_krw),
    }


def compute_unit_metric_breakdown(
    cost_per_user_krw: float,
    cost_per_transaction_krw: float,
    cost_per_request_krw: float,
    cost_per_hour_krw: float,
) -> dict[str, float]:
    """4-unit-metric cost breakdown (Phase 19 AD-46 (a) verbatim).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    return {
        "cost_per_user": float(cost_per_user_krw),
        "cost_per_transaction": float(cost_per_transaction_krw),
        "cost_per_request": float(cost_per_request_krw),
        "cost_per_hour": float(cost_per_hour_krw),
    }


def validate_rate_card_inventory(rollup: RateCardInventory) -> bool:
    """Pure validator for RateCardInventory (CR 11-4 P-015 verbatim).

    Returns True if all required fields are present + non-empty.
    Raises PricingAggregationError if critical fields are missing.
    """
    required = [
        "rate_card_id",
        "tenant_id",
        "scope_type",
        "scope_id",
        "period_key",
        "total_blended_rate_krw_per_hour",
        "effective_discount_pct",
        "computed_at",
    ]
    missing = [field for field in required if field not in rollup or rollup[field] in (None, "")]
    if missing:
        raise PricingAggregationError(
            reason="rate_card_inventory_missing_required_fields",
            missing_fields=missing,
        )
    return True


def aggregate_rate_card_inventory(
    tenant_id: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
    *,
    industry: str = "manufacturing",
    # Phase 11 showback input
    showback_total_krw: float = 0.0,
    total_compute_hours: float = 0.0,
    # Phase 12 anomaly input
    anomaly_count_30d: int = 0,
    avg_anomaly_cost_krw: float = 0.0,
    # Phase 13 forecast input
    forecast_30d_krw: float = 0.0,
    current_30d_krw: float = 0.0,
    # Phase 14 optimization input
    optimization_savings_krw: float = 0.0,
    on_demand_baseline_krw: float = 0.0,
    # Phase 15 tag_governance input
    tagged_cost_krw: float = 0.0,
    # Phase 16 executive input
    total_cost_krw: float = 0.0,
    active_user_count: int = 0,
    transaction_count: int = 0,
    request_count: int = 0,
    # Phase 17 sustainability input
    carbon_intensity_kgco2e_per_krw: float = 0.0,
    # Phase 18 commitment input
    commitment_savings_krw: float = 0.0,
    # 5 cloud provider cost (Phase 19 AD-46 (a))
    aws_krw: float = 0.0,
    azure_krw: float = 0.0,
    gcp_krw: float = 0.0,
    naver_krw: float = 0.0,
    kt_krw: float = 0.0,
    # 6 pricing model cost (Phase 19 AD-46 (a))
    pricing_model_costs: dict[str, float] | None = None,
) -> RateCardInventory:
    """Aggregate 8-module cross-rollup + 5-cloud-provider + 6-pricing-model
    RateCardInventory.

    Returns a RateCardInventory TypedDict 18 fields (PRD §F35.1-2 verbatim).
    Pure aggregator — NO DB I/O (callers persist via repository layer).

    CR 1-1 audit-first INSERT: caller MUST emit `pricing_dashboard_viewed`
    BEFORE invoking this aggregator (this module does NOT emit audit).
    """
    _validate_inputs(tenant_id, scope_type, scope_id, period_key)

    # 1) blended rate (Phase 11)
    blended_rate = compute_showback_blended_rate(
        showback_total_krw, total_compute_hours
    )

    # 2) effective discount (Phase 14 + Phase 18 combined)
    effective_discount_pct = compute_optimization_effective_discount(
        optimization_savings_krw, on_demand_baseline_krw
    ) + compute_commitment_discount_baseline(
        commitment_savings_krw, on_demand_baseline_krw
    )

    # 3) cloud provider breakdown (5 providers)
    cloud_provider_breakdown = compute_cloud_provider_breakdown(
        aws_krw, azure_krw, gcp_krw, naver_krw, kt_krw
    )

    # 4) pricing model breakdown (6 models) — caller-provided or default zero
    if pricing_model_costs is None:
        pricing_model_breakdown = {model: 0.0 for model in ALL_PRICING_MODELS}
    else:
        pricing_model_breakdown = {
            model: float(pricing_model_costs.get(model, 0.0))
            for model in ALL_PRICING_MODELS
        }

    # 5) unit metric breakdown (4 metrics)
    cost_per_user_krw = compute_executive_unit_economics(
        total_cost_krw, active_user_count
    )
    cost_per_transaction_krw = (
        float(total_cost_krw) / float(transaction_count)
        if transaction_count > 0 else 0.0
    )
    cost_per_request_krw = (
        float(total_cost_krw) / float(request_count)
        if request_count > 0 else 0.0
    )
    cost_per_hour_krw = compute_showback_blended_rate(
        showback_total_krw, total_compute_hours
    )
    unit_metric_breakdown = compute_unit_metric_breakdown(
        cost_per_user_krw,
        cost_per_transaction_krw,
        cost_per_request_krw,
        cost_per_hour_krw,
    )

    # 6) scope_chain — 8-module source attribution + industry baseline
    scope_chain: dict[str, Any] = {
        "phase_11_showback_total_krw": float(showback_total_krw),
        "phase_12_anomaly_count_30d": int(anomaly_count_30d),
        "phase_13_forecast_30d_krw": float(forecast_30d_krw),
        "phase_14_optimization_savings_krw": float(optimization_savings_krw),
        "phase_15_tagged_cost_krw": float(tagged_cost_krw),
        "phase_16_total_cost_krw": float(total_cost_krw),
        "phase_17_carbon_intensity": float(carbon_intensity_kgco2e_per_krw),
        "phase_18_commitment_savings_krw": float(commitment_savings_krw),
        "industry": industry,
        "industry_unit_economics_baseline": _get_industry_unit_economics_baseline(industry),
        "engine_model_version": PRICING_ENGINE_MODEL_VERSION,
    }

    # 7) compute rate_card_hash (CR 4-3/4-4 tenant-scoped result_hash)
    rate_card_hash = _compute_cache_key(tenant_id, scope_type, scope_id, period_key)

    rollup: RateCardInventory = {
        "rate_card_id": "",  # caller-set after INSERT
        "tenant_id": tenant_id,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "period_key": period_key,
        "scope_chain": scope_chain,
        "total_blended_rate_krw_per_hour": blended_rate,
        "effective_discount_pct": effective_discount_pct,
        "pricing_model_breakdown": pricing_model_breakdown,
        "unit_metric_breakdown": unit_metric_breakdown,
        "cloud_provider_breakdown": cloud_provider_breakdown,
        "cost_per_user_krw": cost_per_user_krw,
        "cost_per_transaction_krw": cost_per_transaction_krw,
        "cost_per_request_krw": cost_per_request_krw,
        "cost_per_hour_krw": cost_per_hour_krw,
        "on_demand_cost_krw": float(on_demand_baseline_krw),
        "discounted_cost_krw": float(showback_total_krw),
        "rate_card_hash": rate_card_hash,
        "computed_at": datetime.now(UTC),
        "trace_id": "",  # caller-set via ContextVar
    }
    return rollup


def load_rate_card_inventory(
    rollup_id: str,
    tenant_id: str,
) -> RateCardInventory:
    """Placeholder loader — repository layer MUST replace this stub.

    Raises PricingCrossModuleJoinError if no row found for tenant_id.
    """
    raise PricingCrossModuleJoinError(
        rollup_id=rollup_id,
        tenant_id=tenant_id,
    )
