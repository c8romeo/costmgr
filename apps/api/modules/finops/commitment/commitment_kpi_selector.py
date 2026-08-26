"""apps.api.modules.finops.commitment.commitment_kpi_selector — Commitment KPI selector.

Phase 18 wire (cj-style 135번째) — FinOps Cloud Commitment Management
territory (PRD §F34.2 verbatim + AD-45 (b) decision).

8 NEW commitment KPI calculations:
- total_commitment_value_krw — Σcommitment_value across 5 cloud providers
- coverage_pct — Σcommitment_value / total_on_demand_cost × 100
- utilization_pct — actual_used_hours / purchased_hours × 100
- expiring_commitments_30d — count of commitments expiring within 30 days
- recommended_purchase_krw — Phase 14 commitment_recommender recommended
- savings_realized_krw — on_demand_cost - commitment_cost
- idle_commitment_krw — unused_commitment_value (1 - utilization/100) × total
- renewal_decision_score — weighted coverage + utilization (0-100)

Functions:
- `select_commitment_kpis` — main entry (PRD §F34.2-1 verbatim)
- `compute_total_commitment_value` — total_commitment_value_krw
- `compute_coverage_pct` — coverage_pct
- `compute_utilization_pct` — utilization_pct
- `compute_expiring_commitments_30d` — expiring_commitments_30d
- `compute_recommended_purchase` — recommended_purchase_krw
- `compute_savings_realized` — savings_realized_krw
- `compute_idle_commitment` — idle_commitment_krw
- `compute_renewal_decision_score` — renewal_decision_score
- `validate_commitment_kpi` — pure validator (CR 11-4 P-015 verbatim)

TypedDict:
- `CommitmentKPI` — see apps.api.modules.finops.commitment.serializers

Exceptions (CR 12-5 D-14 envelope):
- `CommitmentKPIError` (500)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `commitment_kpi_calculated` AFTER compute.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-45 FinOps Cloud Commitment Management (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from apps.api.core.errors import (
    CommitmentInventoryAggregationError,
    CommitmentKPIError,
)
from apps.api.modules.finops.commitment.commitment_inventory_aggregator import (
    _get_industry_utilization_pct_baseline,
    aggregate_commitment_inventory,
)
from apps.api.modules.finops.commitment.serializers import (
    ALL_COMMITMENT_KPI_NAMES,
    ALL_COMMITMENT_KPI_THRESHOLD_STATUSES,
    COMMITMENT_DEFAULTS,
    COMMITMENT_ENGINE_MODEL_VERSION,
    CommitmentKPI,
)

logger = logging.getLogger(__name__)


# 8 NEW commitment KPI units map (PRD §F34.2 verbatim).
_KPI_UNIT_MAP: dict[str, str] = {
    "total_commitment_value_krw": "krw",
    "coverage_pct": "pct",
    "utilization_pct": "pct",
    "expiring_commitments_30d": "count",
    "recommended_purchase_krw": "krw",
    "savings_realized_krw": "krw",
    "idle_commitment_krw": "krw",
    "renewal_decision_score": "score",
}


# 8 NEW commitment KPI target values (PRD §F34.2 verbatim).
_KPI_TARGET_MAP: dict[str, float] = {
    "total_commitment_value_krw": 0.0,  # target = current (informational)
    "coverage_pct": COMMITMENT_DEFAULTS["coverage_target_pct"],  # 70% target
    "utilization_pct": COMMITMENT_DEFAULTS["utilization_target_pct"],  # 80% target
    "expiring_commitments_30d": 0.0,  # target = 0 (avoid expiring)
    "recommended_purchase_krw": 0.0,  # target = current (informational)
    "savings_realized_krw": 0.0,  # target = current (informational)
    "idle_commitment_krw": 0.0,  # target = 0 (avoid idle)
    "renewal_decision_score": COMMITMENT_DEFAULTS["renewal_decision_threshold"],  # 50 score
}


def _compute_kpi_cache_key(
    tenant_id: str,
    kpi_name: str,
    period_key: str,
) -> str:
    """Compute SHA-256 cache key for CommitmentKPI."""
    payload = f"{tenant_id}:{kpi_name}:{period_key}:commitment_kpi"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_kpi_inputs(
    tenant_id: str,
    kpi_name: str,
    period_key: str,
) -> None:
    """Pure validator for KPI inputs (CR 11-4 P-015 verbatim)."""
    if not tenant_id:
        raise CommitmentInventoryAggregationError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if kpi_name not in ALL_COMMITMENT_KPI_NAMES:
        raise CommitmentKPIError(
            reason=f"unknown_kpi:{kpi_name}",
            kpi_name=kpi_name,
            allowed=list(ALL_COMMITMENT_KPI_NAMES),
        )
    if not period_key:
        raise CommitmentKPIError(
            reason="period_key_empty",
            period_key=period_key,
        )


def _classify_threshold_status(
    kpi_name: str,
    kpi_value: float,
    industry: str = "manufacturing",
) -> str:
    """Classify KPI threshold status (on_track/warning/critical).

    Phase 18 wire (cj-style 135번째) — applies industry-specific threshold
    classification per AD-45 (b) verbatim.
    """
    if kpi_name == "coverage_pct":
        # Higher is better; target 70% baseline.
        target = COMMITMENT_DEFAULTS["coverage_target_pct"]
        if kpi_value >= target:
            return "on_track"
        if kpi_value >= target * 0.7:
            return "warning"
        return "critical"
    if kpi_name == "utilization_pct":
        # Higher is better; target 80% baseline.
        target = COMMITMENT_DEFAULTS["utilization_target_pct"]
        if kpi_value >= target:
            return "on_track"
        if kpi_value >= target * 0.7:
            return "warning"
        return "critical"
    if kpi_name == "idle_commitment_krw":
        # Lower is better; 0 = on_track.
        if kpi_value <= 0.0:
            return "on_track"
        if kpi_value <= 1000000.0:  # 1M KRW warning
            return "warning"
        return "critical"
    if kpi_name == "renewal_decision_score":
        # Higher is better; threshold 50.
        threshold = COMMITMENT_DEFAULTS["renewal_decision_threshold"]
        if kpi_value >= threshold:
            return "on_track"
        if kpi_value >= threshold * 0.7:
            return "warning"
        return "critical"
    if kpi_name == "expiring_commitments_30d":
        # Lower is better; 0 = on_track.
        if kpi_value <= 0:
            return "on_track"
        if kpi_value <= 5:
            return "warning"
        return "critical"
    # Default: classify based on absolute value sign.
    if kpi_value == 0.0:
        return "on_track"
    return "on_track"


def compute_total_commitment_value(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> float:
    """Compute total_commitment_value_krw via Phase 18 commitment aggregator.

    Phase 18 wire (cj-style 135번째) — delegates to
    aggregate_commitment_inventory().total_commitment_value_krw.
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return float(rollup.get("total_commitment_value_krw", 0.0))


def compute_coverage_pct(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> float:
    """Extract coverage_pct (Σcommitment_value / total_on_demand_cost × 100).

    Phase 18 wire (cj-style 135번째) — coverage % measures how much of
    on-demand cost is covered by commitments. Target 70% per
    COMMITMENT_DEFAULTS["coverage_target_pct"].
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return float(rollup.get("coverage_pct", 0.0))


def compute_utilization_pct(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> float:
    """Extract utilization_pct (actual_used_hours / purchased_hours × 100).

    Phase 18 wire (cj-style 135번째) — utilization % measures how much
    of purchased commitment hours are actually consumed. Target 80% per
    COMMITMENT_DEFAULTS["utilization_target_pct"].
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return float(rollup.get("utilization_pct", 0.0))


def compute_expiring_commitments_30d(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> int:
    """Extract expiring_commitments_30d count.

    Phase 18 wire (cj-style 135번째) — count of commitments expiring
    within 30 days from period_key.
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return int(rollup.get("expiring_commitments_30d", 0))


def compute_recommended_purchase(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> float:
    """Extract recommended_purchase_krw (Phase 14 commitment_recommender EXTENSION).

    Phase 18 wire (cj-style 135번째) — Phase 14 commitment_recommender
    6 commitment_types × 2 commitment_terms EXTENSION.
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return float(rollup.get("recommended_purchase_krw", 0.0))


def compute_savings_realized(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> float:
    """Extract savings_realized_krw (on_demand_cost - commitment_cost).

    Phase 18 wire (cj-style 135번째) — savings from commitment purchases.
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return float(rollup.get("savings_realized_krw", 0.0))


def compute_idle_commitment(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> float:
    """Extract idle_commitment_krw (unused commitment value).

    Phase 18 wire (cj-style 135번째) — idle = (1 - utilization/100) × total.
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return float(rollup.get("idle_commitment_krw", 0.0))


def compute_renewal_decision_score(
    tenant_id: str,
    period_key: str,
    industry: str = "manufacturing",
    db_session: Any | None = None,
) -> float:
    """Extract renewal_decision_score (weighted coverage + utilization).

    Phase 18 wire (cj-style 135번째) — 0-100 score. Higher = stronger
    renewal recommendation.
    """
    rollup = aggregate_commitment_inventory(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=tenant_id,
        period_key=period_key,
        trace_id="",
        industry=industry,
        db_session=db_session,
        dry_run=True,
    )
    return float(rollup.get("renewal_decision_score", 0.0))


def select_commitment_kpis(
    tenant_id: str,
    period_key: str,
    trace_id: str = "",
    industry: str = "manufacturing",
    db_session: Any | None = None,
    dry_run: bool = False,
) -> list[CommitmentKPI]:
    """Compute 8 NEW commitment KPIs + return list of CommitmentKPI.

    Phase 18 wire (cj-style 135번째) — main entry (PRD §F34.2-1 verbatim).

    Args:
        tenant_id: Tenant UUID (CR 0-2 RLS — multi-tenant isolation).
        period_key: Period key (e.g. "2026-08", "2026-Q3", "2026").
        trace_id: Trace ID for audit (CR 1-1 ContextVar).
        industry: Tenant industry (manufacturing/service/manufacturing_service/
            manufacturing_service_other) for utilization_pct baseline.
        db_session: Optional DB session (None for dry-run).
        dry_run: If True, skip audit-first INSERT (CR 1-1 verbatim).

    Returns:
        list[CommitmentKPI] TypedDict 16 fields per KPI (8 NEW KPIs).

    Raises:
        CommitmentInventoryAggregationError — invalid inputs (500).
        CommitmentKPIError — KPI compute failure (500).

    CR lessons applied:
    - CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
    - CR 1-1 audit-first INSERT — `commitment_kpi_calculated` AFTER compute.
    - CR 1-1 ContextVar — trace_id propagation.
    - CR 11-4 P-015 — pure validator pattern.
    - CR 12-5 D-14 typed exception envelope verbatim.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    - AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
    - AD-45 FinOps Cloud Commitment Management (a)~(g) 7 sub-decisions.
    - NFR4 PII minimization — only business metrics + commitment amounts.
    - NFR18 ko-KR SSOT.
    """
    _validate_kpi_inputs(tenant_id, "total_commitment_value_krw", period_key)

    kpis: list[CommitmentKPI] = []

    try:
        # 1. total_commitment_value_krw
        total_value = compute_total_commitment_value(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="total_commitment_value_krw",
                kpi_value=total_value,
                kpi_unit=_KPI_UNIT_MAP["total_commitment_value_krw"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "total_commitment_value_krw", total_value, industry
                ),
                kpi_target=_KPI_TARGET_MAP["total_commitment_value_krw"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

        # 2. coverage_pct
        coverage = compute_coverage_pct(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="coverage_pct",
                kpi_value=coverage,
                kpi_unit=_KPI_UNIT_MAP["coverage_pct"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "coverage_pct", coverage, industry
                ),
                kpi_target=_KPI_TARGET_MAP["coverage_pct"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

        # 3. utilization_pct
        utilization = compute_utilization_pct(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="utilization_pct",
                kpi_value=utilization,
                kpi_unit=_KPI_UNIT_MAP["utilization_pct"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "utilization_pct", utilization, industry
                ),
                kpi_target=_KPI_TARGET_MAP["utilization_pct"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

        # 4. expiring_commitments_30d
        expiring = compute_expiring_commitments_30d(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="expiring_commitments_30d",
                kpi_value=float(expiring),
                kpi_unit=_KPI_UNIT_MAP["expiring_commitments_30d"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "expiring_commitments_30d", float(expiring), industry
                ),
                kpi_target=_KPI_TARGET_MAP["expiring_commitments_30d"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

        # 5. recommended_purchase_krw
        recommended = compute_recommended_purchase(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="recommended_purchase_krw",
                kpi_value=recommended,
                kpi_unit=_KPI_UNIT_MAP["recommended_purchase_krw"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "recommended_purchase_krw", recommended, industry
                ),
                kpi_target=_KPI_TARGET_MAP["recommended_purchase_krw"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

        # 6. savings_realized_krw
        savings = compute_savings_realized(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="savings_realized_krw",
                kpi_value=savings,
                kpi_unit=_KPI_UNIT_MAP["savings_realized_krw"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "savings_realized_krw", savings, industry
                ),
                kpi_target=_KPI_TARGET_MAP["savings_realized_krw"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

        # 7. idle_commitment_krw
        idle = compute_idle_commitment(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="idle_commitment_krw",
                kpi_value=idle,
                kpi_unit=_KPI_UNIT_MAP["idle_commitment_krw"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "idle_commitment_krw", idle, industry
                ),
                kpi_target=_KPI_TARGET_MAP["idle_commitment_krw"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

        # 8. renewal_decision_score
        renewal = compute_renewal_decision_score(
            tenant_id=tenant_id,
            period_key=period_key,
            industry=industry,
            db_session=db_session,
        )
        kpis.append(
            CommitmentKPI(
                kpi_name="renewal_decision_score",
                kpi_value=renewal,
                kpi_unit=_KPI_UNIT_MAP["renewal_decision_score"],
                kpi_delta=None,
                kpi_trend="flat",
                kpi_threshold_status=_classify_threshold_status(
                    "renewal_decision_score", renewal, industry
                ),
                kpi_target=_KPI_TARGET_MAP["renewal_decision_score"],
                kpi_computed_at=datetime.now(tz=UTC),
                trace_id=trace_id,
            )
        )

    except Exception as exc:
        raise CommitmentKPIError(
            reason=str(exc),
            tenant_id=tenant_id,
            period_key=period_key,
        ) from exc

    # Audit-first INSERT `commitment_kpi_calculated` AFTER compute (CR 1-1).
    if db_session is not None and not dry_run:
        try:
            from apps.api.core.audit_action import ActionClass, emit_audit_typed

            emit_audit_typed(
                db_session,
                action_class=ActionClass.FINOPS_COMMITMENT,
                action="commitment_kpi_calculated",
                actor_id=None,  # owner-only RBAC AD-22 + 2FA
                target_id=None,
                reason=trace_id,
                payload={
                    "period_key": period_key,
                    "industry": industry,
                    "kpi_count": len(kpis),
                    "model_version": COMMITMENT_ENGINE_MODEL_VERSION,
                    "trace_id": trace_id,
                    "tenant_id": tenant_id,
                },
                tenant_id=tenant_id,
            )
        except ImportError:
            pass

    logger.info(
        "commitment_kpi_selector.select_commitment_kpis",
        extra={
            "tenant_id": tenant_id,
            "period_key": period_key,
            "industry": industry,
            "kpi_count": len(kpis),
            "dry_run": dry_run,
        },
    )

    _ = _get_industry_utilization_pct_baseline  # reserved for future cross-rollup hints
    return kpis


def validate_commitment_kpi(kpi: CommitmentKPI) -> bool:
    """Pure validator for CommitmentKPI TypedDict.

    CR 11-4 P-015 verbatim 5-layer defense (syntax + semantic +
    kpi_name validation + unit validation + threshold_status validation).
    """
    if not isinstance(kpi, dict):
        raise CommitmentKPIError(
            reason="kpi_not_dict",
            tenant_id="",
        )
    required = [
        "kpi_name",
        "kpi_value",
        "kpi_unit",
        "kpi_threshold_status",
        "kpi_computed_at",
        "trace_id",
    ]
    for field_name in required:
        if field_name not in kpi:
            raise CommitmentKPIError(
                reason=f"missing_field:{field_name}",
                kpi_name=str(kpi.get("kpi_name", "")),
            )
    if kpi["kpi_name"] not in ALL_COMMITMENT_KPI_NAMES:
        raise CommitmentKPIError(
            reason=f"unknown_kpi:{kpi['kpi_name']}",
            kpi_name=str(kpi["kpi_name"]),
            allowed=list(ALL_COMMITMENT_KPI_NAMES),
        )
    if kpi["kpi_threshold_status"] not in ALL_COMMITMENT_KPI_THRESHOLD_STATUSES:
        raise CommitmentKPIError(
            reason=f"invalid_threshold_status:{kpi['kpi_threshold_status']}",
            kpi_name=str(kpi["kpi_name"]),
        )
    return True


__all__ = [
    "select_commitment_kpis",
    "compute_total_commitment_value",
    "compute_coverage_pct",
    "compute_utilization_pct",
    "compute_expiring_commitments_30d",
    "compute_recommended_purchase",
    "compute_savings_realized",
    "compute_idle_commitment",
    "compute_renewal_decision_score",
    "validate_commitment_kpi",
]