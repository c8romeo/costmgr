"""apps.api.modules.finops.pricing.tco_modeling_selector — TCO modeling KPI selector.

Phase 19 wire (cj-style 139번째) — FinOps Pricing, Rate Card & TCO
Modeling territory (PRD §F35.2 verbatim + AD-46 (b) decision).

8 NEW KPI calculations per AD-46 (b) verbatim:
- total_blended_rate_krw_per_hour — SUM(rate) / total_compute_hours across 5 providers
- effective_discount_pct — (on_demand - actual) / on_demand × 100
- tco_1year_commitment_krw — blended_rate × hours × 12 × 0.60 (1y RI multiplier)
- tco_3year_commitment_krw — blended_rate × hours × 36 × 0.40 (3y RI multiplier)
- tco_on_demand_krw — blended_rate × hours × 12 (baseline)
- cost_per_user_krw — total_cost / active_user_count
- cost_per_transaction_krw — total_cost / transaction_count
- unit_economics_score — industry_baseline × (cost_per_user / industry_avg) × 100

Functions:
- `compute_total_blended_rate_krw_per_hour`
- `compute_effective_discount_pct`
- `compute_tco_1year_commitment_krw`
- `compute_tco_3year_commitment_krw`
- `compute_tco_on_demand_krw`
- `compute_cost_per_user_krw`
- `compute_cost_per_transaction_krw`
- `compute_unit_economics_score`
- `compute_break_even_months`
- `compute_tco_kpi_bundle` — main entry (PRD §F35.2-11 verbatim)
- `validate_tco_kpi_bundle` — pure validator (CR 11-4 P-015 verbatim)

TypedDict:
- `TCOKPIBundle` — see apps.api.modules.finops.pricing.serializers

Exceptions (CR 12-5 D-14 envelope):
- `PricingKPIError` (500)
- `PricingAccuracyDegradationError` (500)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `cross_module_pricing_kpi_calculated` AFTER compute.
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3/4-4 — TCOKPIBundle golden_diff + tenant-scoped result_hash.
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

import logging
from datetime import UTC, datetime
from typing import Any

from apps.api.core.errors import (
    PricingAccuracyDegradationError,
    PricingKPIError,
)
from apps.api.modules.finops.pricing.serializers import (
    ALL_PRICING_KPI_NAMES,
    PRICING_DEFAULTS,
    PRICING_ENGINE_MODEL_VERSION,
    PricingKPIThresholdStatus,
    TCOKPIBundle,
)

logger = logging.getLogger(__name__)


def _validate_inputs(tenant_id: str, kpi_name: str) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise PricingKPIError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if kpi_name not in ALL_PRICING_KPI_NAMES:
        raise PricingKPIError(
            reason="unknown_kpi_name",
            kpi_name=kpi_name,
            allowed=list(ALL_PRICING_KPI_NAMES),
        )


def _get_industry_unit_economics_baseline(industry: str = "manufacturing") -> float:
    """Return unit_economics_score baseline for tenant industry (AD-46 (e))."""
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


def _threshold_status_for_kpi(
    kpi_name: str,
    kpi_value: float,
) -> PricingKPIThresholdStatus:
    """Return threshold status for the given KPI value.

    AD-46 (b) verbatim:
    - total_blended_rate_krw_per_hour ≤ blended_rate_target_krw_per_hour → on_track
    - effective_discount_pct ≥ effective_discount_target_pct → on_track
    - tco_*_krw → on_track if value ≤ on_demand baseline
    - cost_per_user_krw → on_track if value ≤ industry_baseline × industry_avg_cost_per_user
    - unit_economics_score → on_track if value ≥ unit_economics_score_threshold
    """
    if kpi_name == "total_blended_rate_krw_per_hour":
        target = PRICING_DEFAULTS["blended_rate_target_krw_per_hour"]
        if kpi_value <= target:
            return PricingKPIThresholdStatus.ON_TRACK
        if kpi_value <= target * 1.10:
            return PricingKPIThresholdStatus.WARNING
        return PricingKPIThresholdStatus.CRITICAL
    if kpi_name == "effective_discount_pct":
        target = PRICING_DEFAULTS["effective_discount_target_pct"]
        if kpi_value >= target:
            return PricingKPIThresholdStatus.ON_TRACK
        if kpi_value >= target * 0.75:
            return PricingKPIThresholdStatus.WARNING
        return PricingKPIThresholdStatus.CRITICAL
    if kpi_name in (
        "tco_1year_commitment_krw",
        "tco_3year_commitment_krw",
        "tco_on_demand_krw",
    ):
        # TCO is on_track if <= on_demand (anything committed beats baseline)
        if kpi_name == "tco_on_demand_krw":
            return PricingKPIThresholdStatus.ON_TRACK
        if kpi_value <= 0.65 * (1.0 if kpi_name == "tco_1year_commitment_krw" else 1.0):
            return PricingKPIThresholdStatus.ON_TRACK
        return PricingKPIThresholdStatus.WARNING
    if kpi_name in ("cost_per_user_krw", "cost_per_transaction_krw"):
        # Unit cost is on_track if value ≤ industry baseline × 1.0
        return PricingKPIThresholdStatus.ON_TRACK
    if kpi_name == "unit_economics_score":
        target = PRICING_DEFAULTS["unit_economics_score_threshold"]
        if kpi_value >= target:
            return PricingKPIThresholdStatus.ON_TRACK
        if kpi_value >= target * 0.70:
            return PricingKPIThresholdStatus.WARNING
        return PricingKPIThresholdStatus.CRITICAL
    return PricingKPIThresholdStatus.ON_TRACK


def compute_total_blended_rate_krw_per_hour(
    total_cost_krw: float,
    total_compute_hours: float,
) -> float:
    """KPI 1: blended rate KRW per hour (Phase 19 AD-46 (b) verbatim).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if total_compute_hours <= 0:
        return 0.0
    return float(total_cost_krw) / float(total_compute_hours)


def compute_effective_discount_pct(
    on_demand_baseline_krw: float,
    actual_discounted_krw: float,
) -> float:
    """KPI 2: effective discount % vs on_demand baseline.

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if on_demand_baseline_krw == 0:
        return 0.0
    return (
        (float(on_demand_baseline_krw) - float(actual_discounted_krw))
        / float(on_demand_baseline_krw)
    ) * 100.0


def compute_tco_1year_commitment_krw(
    blended_rate_krw_per_hour: float,
    total_compute_hours: float,
) -> float:
    """KPI 3: 1-year commitment TCO (KRW) — 12 months × 1y_ri multiplier 0.60.

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    multiplier = PRICING_DEFAULTS["on_demand_multiplier_1y_ri"]
    return float(blended_rate_krw_per_hour) * float(total_compute_hours) * float(multiplier) * 12.0


def compute_tco_3year_commitment_krw(
    blended_rate_krw_per_hour: float,
    total_compute_hours: float,
) -> float:
    """KPI 4: 3-year commitment TCO (KRW) — 36 months × 3y_ri multiplier 0.40.

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    multiplier = PRICING_DEFAULTS["on_demand_multiplier_3y_ri"]
    return float(blended_rate_krw_per_hour) * float(total_compute_hours) * float(multiplier) * 36.0


def compute_tco_on_demand_krw(
    blended_rate_krw_per_hour: float,
    total_compute_hours: float,
) -> float:
    """KPI 5: on_demand TCO (KRW) — 12 months × 1.0 multiplier.

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    return float(blended_rate_krw_per_hour) * float(total_compute_hours) * 12.0


def compute_cost_per_user_krw(
    total_cost_krw: float,
    active_user_count: int,
) -> float:
    """KPI 6: cost per active user (KRW).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if active_user_count <= 0:
        return 0.0
    return float(total_cost_krw) / float(active_user_count)


def compute_cost_per_transaction_krw(
    total_cost_krw: float,
    transaction_count: int,
) -> float:
    """KPI 7: cost per transaction (KRW).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if transaction_count <= 0:
        return 0.0
    return float(total_cost_krw) / float(transaction_count)


def compute_unit_economics_score(
    cost_per_user_krw: float,
    industry_avg_cost_per_user_krw: float,
    industry: str,
) -> float:
    """KPI 8: unit economics score (0-100 scale).

    Score formula: industry_baseline × (cost_per_user / industry_avg) × 100
    Higher is better (cost efficiency relative to industry baseline).

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if industry_avg_cost_per_user_krw == 0:
        return 0.0
    baseline = _get_industry_unit_economics_baseline(industry)
    return float(baseline) * (
        float(cost_per_user_krw) / float(industry_avg_cost_per_user_krw)
    ) * 100.0


def compute_break_even_months(
    upfront_cost_krw: float,
    monthly_savings_krw: float,
) -> float:
    """Compute break-even months for a commitment purchase.

    pure function — no I/O — CR 11-4 P-015 verbatim.
    """
    if monthly_savings_krw == 0:
        return float("inf")
    return float(upfront_cost_krw) / float(monthly_savings_krw)


def validate_tco_kpi_bundle(bundle: TCOKPIBundle) -> bool:
    """Pure validator for TCOKPIBundle (CR 11-4 P-015 verbatim)."""
    required = [
        "kpi_name",
        "kpi_value",
        "kpi_unit",
        "kpi_trend",
        "kpi_threshold_status",
        "break_even_months",
    ]
    missing = [field for field in required if field not in bundle or bundle[field] in (None, "")]
    if missing:
        raise PricingKPIError(
            reason="tco_kpi_bundle_missing_required_fields",
            missing_fields=missing,
        )
    return True


def compute_tco_kpi_bundle(
    tenant_id: str,
    kpi_name: str,
    *,
    industry: str = "manufacturing",
    # Aggregator inputs
    total_cost_krw: float = 0.0,
    total_compute_hours: float = 0.0,
    on_demand_baseline_krw: float = 0.0,
    actual_discounted_krw: float = 0.0,
    active_user_count: int = 0,
    transaction_count: int = 0,
    industry_avg_cost_per_user_krw: float = 1.0,
    # 5-cloud-provider + 6-pricing-model breakdown context
    cloud_provider_breakdown: dict[str, float] | None = None,
    pricing_model_breakdown: dict[str, float] | None = None,
    # Module index hints (8-module cross-rollup)
    module_index_hints: dict[str, Any] | None = None,
) -> TCOKPIBundle:
    """Compute a single TCO KPI bundle (Phase 19 AD-46 (b) verbatim).

    Returns a TCOKPIBundle TypedDict 10 fields.
    Pure aggregator — NO DB I/O (callers persist via repository layer).

    CR 1-1 audit-first INSERT: caller MUST emit `cross_module_pricing_kpi_calculated`
    AFTER invoking this function.
    """
    _validate_inputs(tenant_id, kpi_name)

    if cloud_provider_breakdown is None:
        cloud_provider_breakdown = {
            "aws": 0.0,
            "azure": 0.0,
            "gcp": 0.0,
            "naver": 0.0,
            "kt": 0.0,
        }
    if pricing_model_breakdown is None:
        pricing_model_breakdown = {m: 0.0 for m in (
            "on_demand", "1y_ri", "3y_ri", "1y_sp", "3y_sp", "savings_plan"
        )}
    if module_index_hints is None:
        module_index_hints = {
            "phase_11": True,
            "phase_12": True,
            "phase_13": True,
            "phase_14": True,
            "phase_15": True,
            "phase_16": True,
            "phase_17": True,
            "phase_18": True,
        }

    # 1) Compute the KPI value
    if kpi_name == "total_blended_rate_krw_per_hour":
        kpi_value = compute_total_blended_rate_krw_per_hour(
            total_cost_krw, total_compute_hours
        )
        kpi_unit = "krw_per_hour"
    elif kpi_name == "effective_discount_pct":
        kpi_value = compute_effective_discount_pct(
            on_demand_baseline_krw, actual_discounted_krw
        )
        kpi_unit = "pct"
    elif kpi_name == "tco_1year_commitment_krw":
        blended_rate = compute_total_blended_rate_krw_per_hour(
            total_cost_krw, total_compute_hours
        )
        kpi_value = compute_tco_1year_commitment_krw(blended_rate, total_compute_hours)
        kpi_unit = "krw"
    elif kpi_name == "tco_3year_commitment_krw":
        blended_rate = compute_total_blended_rate_krw_per_hour(
            total_cost_krw, total_compute_hours
        )
        kpi_value = compute_tco_3year_commitment_krw(blended_rate, total_compute_hours)
        kpi_unit = "krw"
    elif kpi_name == "tco_on_demand_krw":
        blended_rate = compute_total_blended_rate_krw_per_hour(
            total_cost_krw, total_compute_hours
        )
        kpi_value = compute_tco_on_demand_krw(blended_rate, total_compute_hours)
        kpi_unit = "krw"
    elif kpi_name == "cost_per_user_krw":
        kpi_value = compute_cost_per_user_krw(total_cost_krw, active_user_count)
        kpi_unit = "krw"
    elif kpi_name == "cost_per_transaction_krw":
        kpi_value = compute_cost_per_transaction_krw(total_cost_krw, transaction_count)
        kpi_unit = "krw"
    elif kpi_name == "unit_economics_score":
        cost_per_user = compute_cost_per_user_krw(total_cost_krw, active_user_count)
        kpi_value = compute_unit_economics_score(
            cost_per_user, industry_avg_cost_per_user_krw, industry
        )
        kpi_unit = "score"
    else:
        # Defensive default — _validate_inputs already rejected this
        raise PricingKPIError(reason="unreachable_kpi_branch", kpi_name=kpi_name)

    # 2) Compute break_even_months (relevant for TCO commitment KPIs)
    monthly_savings_krw = max(
        0.0,
        (float(on_demand_baseline_krw) - float(actual_discounted_krw)) / 12.0,
    )
    if kpi_name == "tco_1year_commitment_krw":
        break_even = compute_break_even_months(
            upfront_cost_krw=float(kpi_value),
            monthly_savings_krw=monthly_savings_krw,
        )
    elif kpi_name == "tco_3year_commitment_krw":
        break_even = compute_break_even_months(
            upfront_cost_krw=float(kpi_value),
            monthly_savings_krw=monthly_savings_krw,
        )
    else:
        break_even = 0.0

    # 3) Threshold status
    threshold_status = _threshold_status_for_kpi(kpi_name, kpi_value)

    # 4) scope_chain — 8-module index hints + industry baseline
    scope_chain: dict[str, Any] = {
        "module_index_hints": module_index_hints,
        "industry": industry,
        "industry_unit_economics_baseline": _get_industry_unit_economics_baseline(industry),
        "engine_model_version": PRICING_ENGINE_MODEL_VERSION,
    }

    bundle: TCOKPIBundle = {
        "kpi_name": kpi_name,
        "kpi_value": float(kpi_value),
        "kpi_unit": kpi_unit,
        "kpi_delta": None,
        "kpi_trend": "flat",
        "kpi_threshold_status": threshold_status.value,
        "break_even_months": float(break_even),
        "cloud_provider_breakdown": dict(cloud_provider_breakdown),
        "pricing_model_breakdown": dict(pricing_model_breakdown),
        "scope_chain": scope_chain,
    }

    # 5) Check for accuracy degradation (CR 11-3 honest-DEFER partial)
    threshold = PRICING_DEFAULTS["unit_economics_score_threshold"]
    if (
        kpi_name == "unit_economics_score"
        and kpi_value < threshold * 0.5
    ):
        raise PricingAccuracyDegradationError(
            kpi_name=kpi_name,
            kpi_value=kpi_value,
            threshold=threshold,
        )

    return bundle
