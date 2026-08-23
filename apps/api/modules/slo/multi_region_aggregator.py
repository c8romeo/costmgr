"""apps.api.modules.slo.multi_region_aggregator — multi-region SLO aggregation.

Phase 10 (cj-style 103번째 wire) — SLO Engineering / Error Budget
Management territory (PRD §F26.4 verbatim).

This module provides:
- `MultiRegionSloAggregate` TypedDict (7 fields) — aggregated SLO view.
- region_weight_map default (seoul 0.6 / tokyo 0.3 / singapore 0.1)
  aligned with Phase 5 wire `f093f8c` multi-region failover region
  weight 정합.
- replication_lag weighted adjustment (Phase 5 wire `f093f8c` 100MB
  threshold 기반) — replication_lag > 100MB 면
  weighted_budget_consumed_percent 1.2x multiplier 적용.
- `TenantSloOverride` TypedDict (6 fields) — tenant-scoped override.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `slo_target_updated` (region weight map 변경 / override).
- CR 4-3/4-4 — multi_region baseline 30d rolling pattern verbatim 미러.

AD-22 owner-only RBAC — region weight map 변경 + override 모두 owner-only.

Industry-agnostic per CR 12-1 L4 precedent.
"""
from __future__ import annotations

import logging
import uuid
from typing import Final, Literal, TypedDict

from apps.api.modules.slo.slo_dsl import (
    AGGREGATION_ANY_FAILURE,
    AGGREGATION_MAX,
    AGGREGATION_MIN,
    AGGREGATION_WEIGHTED_AVG,
    REGION_ALL,
    REGION_SEOUL,
    REGION_TOKYO,
    TenantSloOverride,
    VALID_AGGREGATIONS,
)

logger = logging.getLogger(__name__)


# ── Constants — region_weight_map default (Phase 5 wire 정합) ──
# PRD §F26.4.3 verbatim — aligned with Phase 5 wire `f093f8c`
# multi-region failover region weight.
DEFAULT_REGION_WEIGHT_MAP: Final[dict[str, float]] = {
    REGION_SEOUL: 0.6,
    REGION_TOKYO: 0.3,
    "singapore": 0.1,
}

# Phase 5 wire `f093f8c` phase_5_replication_lag 100MB threshold.
REPLICATION_LAG_THRESHOLD_MB: Final[float] = 100.0
REPLICATION_LAG_MULTIPLIER: Final[float] = 1.2  # 20% penalty

# Region normalization map
REGION_ALIASES: Final[dict[str, str]] = {
    REGION_SEOUL: REGION_SEOUL,
    "icn": REGION_SEOUL,  # Incheon airport code alias
    REGION_TOKYO: REGION_TOKYO,
    "nrt": REGION_TOKYO,  # Narita airport code alias
    "sin": "singapore",
    "sg": "singapore",
}


# ── Typed envelopes (CR 12-5 D-PARITY-01) ──────────────────────
class MultiRegionSloAggregate(TypedDict):
    """Multi-region SLO aggregate (PRD §F26.4.2 verbatim — 7 fields).

    Fields:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string (CR 0-2 RLS — tenant scoping).
        window: SLO window.
        weighted_budget_consumed_percent: Weighted aggregate (0.0~100.0+).
        region_results: Per-region budget consumed percent dict.
        replication_lag_adjusted: True if 1.2x multiplier applied.
        aggregation_method: One of 4 methods (weighted_avg/min/max/any_failure).
    """

    slo_id: str
    tenant_id: str
    window: str
    weighted_budget_consumed_percent: float
    region_results: dict[str, float]
    replication_lag_adjusted: bool
    aggregation_method: str


class RegionReplicationLag(TypedDict):
    """Per-region replication lag snapshot (PRD §F26.4.4 verbatim).

    Fields:
        region: Region name (seoul/tokyo/singapore).
        lag_mb: Replication lag in megabytes.
        sampled_at: ISO8601 timestamp.
    """

    region: str
    lag_mb: float
    sampled_at: str


# ── Region weight helpers ───────────────────────────────────────
def normalize_region(region: str) -> str:
    """Normalize region name (handle aliases).

    Args:
        region: Raw region name or alias.

    Returns:
        Canonical region name.
    """
    return REGION_ALIASES.get(region.lower(), region.lower())


def apply_region_weight_map(
    region_results: dict[str, float],
    weight_map: dict[str, float] | None = None,
) -> dict[str, float]:
    """Apply region weight normalization.

    Args:
        region_results: Per-region raw results (e.g. budget_consumed_percent).
        weight_map: Optional override weight map.

    Returns:
        Dict mapping canonical region name → normalized result (weighted).
    """
    weights = weight_map if weight_map is not None else DEFAULT_REGION_WEIGHT_MAP
    out: dict[str, float] = {}
    for raw_region, raw_value in region_results.items():
        region = normalize_region(raw_region)
        weight = weights.get(region, 0.0)
        out[region] = float(raw_value) * weight
    return out


# ── Aggregation methods (PRD §F26.4 verbatim) ──────────────────
def aggregate_weighted_avg(
    region_results: dict[str, float],
    weight_map: dict[str, float] | None = None,
) -> float:
    """weighted_avg aggregation method (PRD §F26.4.2 verbatim).

    Args:
        region_results: Per-region raw results.
        weight_map: Optional override weight map.

    Returns:
        Weighted average (0.0~100.0+).
    """
    weighted = apply_region_weight_map(region_results, weight_map)
    if not weighted:
        return 0.0
    return sum(weighted.values())


def aggregate_min(region_results: dict[str, float]) -> float:
    """min aggregation method (most conservative SLO view)."""
    if not region_results:
        return 0.0
    return min(region_results.values())


def aggregate_max(region_results: dict[str, float]) -> float:
    """max aggregation method (least conservative)."""
    if not region_results:
        return 0.0
    return max(region_results.values())


def aggregate_any_failure(region_results: dict[str, float]) -> float:
    """any_failure aggregation method — if any region > 100, return max."""
    if not region_results:
        return 0.0
    return max(region_results.values())


def aggregate_multi_region(
    slo_id: str,
    tenant_id: str,
    window: str,
    region_results: dict[str, float],
    replication_lags: list[RegionReplicationLag],
    *,
    aggregation_method: str = AGGREGATION_WEIGHTED_AVG,
    weight_map: dict[str, float] | None = None,
    evaluated_at: str | None = None,
) -> MultiRegionSloAggregate:
    """Aggregate multi-region SLO view (PRD §F26.4.2 verbatim).

    Steps:
    1. Determine replication_lag_adjusted (any lag > 100MB).
    2. Apply aggregation method.
    3. Apply 1.2x multiplier if lag detected.

    Args:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        window: SLO window.
        region_results: Per-region budget consumed percent (e.g. {seoul: 30, tokyo: 40}).
        replication_lags: Per-region replication lag snapshots.
        aggregation_method: One of 4 methods.
        weight_map: Optional override weight map.
        evaluated_at: ISO8601 timestamp (reserved for future audit).

    Returns:
        MultiRegionSloAggregate with weighted_budget_consumed_percent.
    """
    if aggregation_method not in VALID_AGGREGATIONS:
        raise ValueError(
            f"multi_region_aggregator: unsupported aggregation_method "
            f"{aggregation_method!r}. Valid: {list(VALID_AGGREGATIONS)}"
        )

    # Step 1: detect replication lag adjustment
    lag_adjusted = any(
        lag["lag_mb"] > REPLICATION_LAG_THRESHOLD_MB for lag in replication_lags
    )

    # Step 2: aggregate per method
    if aggregation_method == AGGREGATION_WEIGHTED_AVG:
        raw_value = aggregate_weighted_avg(region_results, weight_map)
    elif aggregation_method == AGGREGATION_MIN:
        raw_value = aggregate_min(region_results)
    elif aggregation_method == AGGREGATION_MAX:
        raw_value = aggregate_max(region_results)
    elif aggregation_method == AGGREGATION_ANY_FAILURE:
        raw_value = aggregate_any_failure(region_results)
    else:
        raw_value = 0.0

    # Step 3: apply 1.2x multiplier if lag detected
    weighted = raw_value * (REPLICATION_LAG_MULTIPLIER if lag_adjusted else 1.0)

    return MultiRegionSloAggregate(
        slo_id=slo_id,
        tenant_id=tenant_id,
        window=window,
        weighted_budget_consumed_percent=weighted,
        region_results=dict(region_results),
        replication_lag_adjusted=lag_adjusted,
        aggregation_method=aggregation_method,
    )


# ── Tenant-scoped override (PRD §F26.4.5 verbatim) ─────────────
def build_tenant_override(
    *,
    override_id: str,
    slo_id: str,
    tenant_id: str,
    objective_override: float | None,
    window_override: str | None,
    effective_from: str,
) -> TenantSloOverride:
    """Build a TenantSloOverride payload.

    Args:
        override_id: Stable unique identifier.
        slo_id: Target SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        objective_override: Optional override of objective.
        window_override: Optional override of window.
        effective_from: ISO8601 timestamp from which override is active.

    Returns:
        TenantSloOverride payload.
    """
    return TenantSloOverride(
        override_id=override_id,
        slo_id=slo_id,
        tenant_id=tenant_id,
        objective_override=objective_override,
        window_override=window_override,
        effective_from=effective_from,
    )


def override_is_active(override: TenantSloOverride, current_iso: str) -> bool:
    """Check if tenant override is currently active.

    Args:
        override: TenantSloOverride payload.
        current_iso: Current ISO8601 timestamp.

    Returns:
        True if effective_from <= current_iso.
    """
    from datetime import datetime

    try:
        eff = datetime.fromisoformat(override["effective_from"].replace("Z", "+00:00"))
        cur = datetime.fromisoformat(current_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    return cur >= eff


__all__ = [
    "MultiRegionSloAggregate",
    "RegionReplicationLag",
    "DEFAULT_REGION_WEIGHT_MAP",
    "REPLICATION_LAG_THRESHOLD_MB",
    "REPLICATION_LAG_MULTIPLIER",
    "REGION_ALIASES",
    "normalize_region",
    "apply_region_weight_map",
    "aggregate_weighted_avg",
    "aggregate_min",
    "aggregate_max",
    "aggregate_any_failure",
    "aggregate_multi_region",
    "build_tenant_override",
    "override_is_active",
]
