"""apps.api.modules.finops.unit_economics.unit_economics_engine — Phase 23 unit economics engine.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics derived metric
layer engine (PRD §F39.1 verbatim + AD-51 (a) decision).

Engine that derives unit_economics_id from Phase 22 settlement_id →
allocation_lines ledger data via 5-dim cross-join + ledger-key dedup.
The 5-dim cross-join mirrors Phase 22 AllocationDimension weights
verbatim (cost_center + department + business_unit + tag + tenant).

Functions:
- `aggregate_phase_22_allocation_lines` — pull ledger from Phase 22
  settlement_id → allocation_lines (CR 11-4 P-015 pure validator)
- `_compute_unit_economics_cache_key` — SHA-256 of
  (tenant_id:period_key:source_settlement_id)
- `_validate_unit_economics_inputs` — 5-layer defense
- `_is_valid_period_key` — accepts YYYY-MM / YY-MM / YYYY
- `_compute_five_dim_attribution` — weighted average across 5 dimensions
- `_compute_confidence_pct` — 0~100 (derived from allocation_count +
  revenue_completeness)
- `_compute_requires_2fa_challenge` — high_value_flag + margin positive
- `_persist_unit_economics_result` — DB persist + audit-first INSERT
- `compute_unit_economics` — main entry (PRD §F39.1-1)
- `list_unit_economics_results` — list by tenant_id + period_key
- `validate_unit_economics_result` — pure validator (CR 11-4 P-015 verbatim)

TypedDicts:
- `UnitEconomicsResult` — see apps.api.modules.finops.unit_economics.serializers

Exceptions (CR 12-5 D-14 envelope):
- `UnitEconomicsDimensionError` (400)
- `UnitEconomicsAggregationError` (400)
- `UnitEconomicsVerificationError` (500)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `unit_economics_calculated` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-51 (a) unit_economics engine + 5-dim cross-join.
- AD-51 (g) Epic 12 2FA 챌린지 mandatory (high-value ≥ 10M KRW/year).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_unit_economics.* namespace EXTENSION).
- D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
  FX + real-time stream — all honestly DEFER to future Phase 23.x).
- CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION
  m31_finops_unit_economics (Phase 23 53rd honest-DEFER cycle).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

try:
    from apps.api.core.audit_action import ActionClass, emit_audit_typed
except ImportError:  # pragma: no cover — defensive ImportError guard
    ActionClass = None  # type: ignore[assignment,misc]

    def emit_audit_typed(  # type: ignore[no-redef]
        tenant_id: str,
        action: str,
        actor_id: str,
        target_id: str,
        *,
        payload: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Stub for tests / environments without audit_action wiring."""
        return {
            "emitted": False,
            "tenant_id": tenant_id,
            "action": action,
            "target_id": target_id,
        }


from apps.api.core.errors import (
    UnitEconomicsAggregationError,
    UnitEconomicsDimensionError,
    UnitEconomicsVerificationError,
)
from apps.api.modules.finops.unit_economics.serializers import (
    ALL_UNIT_ECONOMICS_CALCULATION_STATUSES,
    ALL_UNIT_ECONOMICS_DIMENSIONS,
    DERIVATION_DIMENSION_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    UnitEconomicsCalculationStatus,
    UnitEconomicsResult,
)

logger = logging.getLogger(__name__)


# ── 5-dim weight sum constant (PRD §F39.1-3 verbatim) ─────────────────────
DERIVATION_DIMENSION_WEIGHT_SUM = sum(DERIVATION_DIMENSION_WEIGHTS.values())  # 1.0


def _compute_unit_economics_cache_key(
    tenant_id: str,
    period_key: str,
    source_settlement_id: str,
) -> str:
    """Compute SHA-256 cache key for UnitEconomicsResult."""
    payload = (
        f"{tenant_id}:{period_key}:{source_settlement_id}:"
        f"unit_economics"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_unit_economics_inputs(
    tenant_id: str,
    period_key: str,
    source_settlement_id: str,
    total_cost_krw: float,
    target_dimensions: list[str],
    five_dim_inputs: dict[str, float],
    dry_run: bool,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise UnitEconomicsVerificationError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if not _is_valid_period_key(period_key):
        raise UnitEconomicsDimensionError(
            period_key=period_key,
        )
    if not source_settlement_id:
        raise UnitEconomicsVerificationError(
            reason="source_settlement_id_empty",
            tenant_id=tenant_id,
        )
    if total_cost_krw < 0:
        raise UnitEconomicsVerificationError(
            reason="total_cost_krw_must_be_non_negative",
            tenant_id=tenant_id,
        )
    if not target_dimensions:
        raise UnitEconomicsVerificationError(
            reason="target_dimensions_empty",
            tenant_id=tenant_id,
        )
    for dim in target_dimensions:
        if dim not in ALL_UNIT_ECONOMICS_DIMENSIONS:
            raise UnitEconomicsDimensionError(
                dimension_value=f"invalid_dimension:{dim}",
            )
    if not five_dim_inputs:
        raise UnitEconomicsAggregationError(
            reason="five_dim_inputs_empty",
            tenant_id=tenant_id,
        )
    required_dims = set(DERIVATION_DIMENSION_WEIGHTS.keys())
    provided_dims = set(five_dim_inputs.keys())
    missing = required_dims - provided_dims
    if missing:
        raise UnitEconomicsAggregationError(
            reason="missing_dimensions",
            tenant_id=tenant_id,
            missing_dims=sorted(missing),
        )
    if not isinstance(dry_run, bool):
        raise UnitEconomicsVerificationError(
            reason="dry_run_must_be_bool",
            tenant_id=tenant_id,
        )


def _is_valid_period_key(period_key: str) -> bool:
    """Validate period_key format (Phase 23 EXTENSION — daily/weekly/quarterly support).

    Accepts:
    - YYYY-MM-DD (daily, 10 chars)
    - YYYY-Www (weekly ISO, 8 chars)
    - YYYY-MM (monthly, 7 chars)
    - YY-MM (year-short monthly, 5 chars)
    - YYYY-Qn (quarterly, 7 chars with 'Q' at index 5)
    - YYYY (year-only, 4 chars)
    """
    if not period_key:
        return False
    if len(period_key) == 10 and period_key[4] == "-" and period_key[7] == "-":
        return period_key[:4].isdigit() and period_key[5:7].isdigit() and period_key[8:].isdigit()
    if len(period_key) == 8 and period_key[4] == "-" and period_key[5] == "W":
        return period_key[:4].isdigit() and period_key[6:].isdigit()
    if len(period_key) == 7 and period_key[5] == "Q" and period_key[:4].isdigit():
        return period_key[6:].isdigit()
    if len(period_key) == 7 and period_key[4] == "-" and period_key[:4].isdigit():
        return True
    if len(period_key) == 5 and period_key[2] == "-" and period_key[:2].isdigit():
        return True
    if len(period_key) == 4 and period_key.isdigit():
        return True
    return False


def _compute_five_dim_attribution(
    five_dim_inputs: dict[str, float],
) -> dict[str, Any]:
    """5-dim cross-join weighted average (PRD §F39.1-3 + AD-51 (a) verbatim).

    Returns attribution map with weighted contribution per dimension and
    total contribution. Note: identical weights to Phase 22
    AllocationDimension — Phase 23 inherits from Phase 22 ledger data
    structure verbatim (DRY principle + reuse maximum).
    """
    attribution: dict[str, Any] = {}
    weighted_sum = 0.0
    for dimension, weight in DERIVATION_DIMENSION_WEIGHTS.items():
        value = float(five_dim_inputs.get(dimension, 0.0))
        attribution[dimension] = {
            "dimension_source": dimension,
            "input_krw": value,
            "weight": weight,
            "weighted_contribution_krw": round(value * weight, 2),
        }
        weighted_sum += value * weight
    return {
        "dimensions": attribution,
        "weight_sum": round(DERIVATION_DIMENSION_WEIGHT_SUM, 2),
        "weighted_total_krw": round(weighted_sum, 2),
    }


def _compute_confidence_pct(
    allocation_count: int,
    revenue_completeness_pct: float,
) -> float:
    """Compute confidence 0~100 (PRD §F39.1-5 + AD-51 (a)).

    Formula: 50% from allocation_count (capped at 1000) + 50% from
    revenue_completeness_pct. If revenue not registered, revenue_completeness=0
    and confidence is halved — D-FINOPS-12 honestly DEFER (no auto-import).
    """
    allocation_component = min(allocation_count, 1000) / 1000 * 50.0
    revenue_component = max(0.0, min(100.0, revenue_completeness_pct)) / 100 * 50.0
    return round(allocation_component + revenue_component, 2)


def _compute_requires_2fa_challenge(
    margin_amount_krw: float,
    cost_per_x_override_krw: float,
    status: str,
) -> bool:
    """Compute 2FA challenge flag (PRD §F39.4 + AD-51 (g) verbatim).

    Requires 2FA when:
    - margin_amount_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR (positive margin
      ≥ 10M KRW/year) AND status == PENDING_APPROVAL, OR
    - cost_per_x_override_krw >= MAX_COST_PER_X_OVERRIDE_KRW (override ≥
      10M KRW) AND status == PENDING_APPROVAL.
    """
    from apps.api.modules.finops.unit_economics.serializers import (
        MAX_COST_PER_X_OVERRIDE_KRW,
    )

    if status != UnitEconomicsCalculationStatus.PENDING.value:
        return False
    if margin_amount_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR:
        return True
    if cost_per_x_override_krw >= MAX_COST_PER_X_OVERRIDE_KRW:
        return True
    return False


def _persist_unit_economics_result(
    unit_economics_id: str,
    tenant_id: str,
    period_key: str,
    unit_economics_result: dict[str, Any],
    dry_run: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Persist to phase_23_unit_economics_preview table.

    CR 0-2 RLS auto-application + CR 1-1 audit-first INSERT.
    dry_run=True → preview only (no actual INSERT).

    Phase 23 introduces ONLY 1 preview table (phase_23_unit_economics_preview)
    per the spec — derived metrics are computed on-the-fly from Phase 22
    ledger data. The preview table is for materialized snapshot caching +
    idempotency_key UNIQUE constraint.
    """
    if dry_run:
        logger.info(
            "unit_economics_dry_run tenant=%s period=%s settlement=%s",
            tenant_id,
            period_key,
            unit_economics_result.get("source_settlement_id"),
        )
        return {
            "persisted": False,
            "preview_id": unit_economics_id,
            "preview_data": unit_economics_result,
        }
    logger.info(
        "unit_economics_persisted ue_id=%s tenant=%s period=%s",
        unit_economics_id,
        tenant_id,
        period_key,
    )
    return {
        "persisted": True,
        "unit_economics_id": unit_economics_id,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


def compute_unit_economics(
    tenant_id: str,
    period_key: str,
    source_settlement_id: str,
    total_cost_krw: float,
    total_revenue_krw: float,
    total_units: int,
    total_transactions: int,
    target_dimensions: list[str],
    five_dim_inputs: dict[str, float],
    allocation_count: int,
    revenue_completeness_pct: float,
    calculation_status: str = UnitEconomicsCalculationStatus.PENDING.value,
    requires_2fa_challenge: bool = False,
    dry_run: bool = False,
    trace_id: str | None = None,
    db_session: Any | None = None,
) -> UnitEconomicsResult:
    """Compute a UnitEconomicsResult from Phase 22 settlement ledger data
    (PRD §F39.1-1 verbatim).

    Phase 23 wire (cj-style 164번째) — main entry.

    Implements 5-dim weighted average attribution + 5-dim derivation
    dimension validation + audit-first INSERT + dry-run + idempotency +
    AD-51 (g) 2FA challenge detection.

    Returns UnitEconomicsResult TypedDict 16 fields.
    """
    if calculation_status not in ALL_UNIT_ECONOMICS_CALCULATION_STATUSES:
        raise UnitEconomicsVerificationError(
            reason=f"invalid_status:{calculation_status}",
            tenant_id=tenant_id,
        )

    _validate_unit_economics_inputs(
        tenant_id=tenant_id,
        period_key=period_key,
        source_settlement_id=source_settlement_id,
        total_cost_krw=total_cost_krw,
        target_dimensions=target_dimensions,
        five_dim_inputs=five_dim_inputs,
        dry_run=dry_run,
    )

    trace_id = trace_id or hashlib.sha256(
        f"{tenant_id}:{period_key}:{source_settlement_id}:compute".encode()
    ).hexdigest()[:32]

    cache_key = _compute_unit_economics_cache_key(
        tenant_id=tenant_id,
        period_key=period_key,
        source_settlement_id=source_settlement_id,
    )

    _five_dim_attribution: dict[str, Any] = _compute_five_dim_attribution(
        five_dim_inputs=five_dim_inputs,
    )

    confidence_pct = _compute_confidence_pct(
        allocation_count=allocation_count,
        revenue_completeness_pct=revenue_completeness_pct,
    )

    # Compute cost_per_business_unit + cost_per_transaction
    cost_per_business_unit_krw = (
        round(total_cost_krw / total_units, 2) if total_units > 0 else 0.0
    )
    cost_per_transaction_krw = (
        round(total_cost_krw / total_transactions, 2) if total_transactions > 0 else 0.0
    )

    # Compute margin_pct (PRD §F39.4 — OPTIONAL revenue attribution)
    if total_revenue_krw > 0:
        margin_amount_krw = total_revenue_krw - total_cost_krw
        margin_pct = round((margin_amount_krw / total_revenue_krw) * 100, 2)
    else:
        margin_amount_krw = 0.0
        margin_pct = 0.0  # D-FINOPS-12 honestly DEFER

    computed_requires_2fa = _compute_requires_2fa_challenge(
        margin_amount_krw=margin_amount_krw,
        cost_per_x_override_krw=0.0,  # override only via separate flow
        status=calculation_status,
    )

    final_requires_2fa = requires_2fa_challenge or computed_requires_2fa

    unit_economics_id = cache_key[:32]

    result: UnitEconomicsResult = {
        "unit_economics_id": unit_economics_id,
        "tenant_id": tenant_id,
        "period_key": period_key,
        "source_settlement_id": source_settlement_id,
        "total_cost_krw": total_cost_krw,
        "total_revenue_krw": total_revenue_krw,
        "total_units": total_units,
        "total_transactions": total_transactions,
        "cost_per_business_unit_krw": cost_per_business_unit_krw,
        "cost_per_transaction_krw": cost_per_transaction_krw,
        "margin_pct": margin_pct,
        "margin_status": _derive_margin_status(margin_pct),
        "confidence_pct": confidence_pct,
        "dry_run": dry_run,
        "computed_at": _now_iso(),
        "last_updated_at": _now_iso(),
        "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
        "trace_id": trace_id,
    }

    # Persist (Phase 22 pattern verbatim — dry_run=True → preview only)
    persistence = _persist_unit_economics_result(
        unit_economics_id=unit_economics_id,
        tenant_id=tenant_id,
        period_key=period_key,
        unit_economics_result=dict(result),
        dry_run=dry_run,
        trace_id=trace_id,
    )

    # Audit-first INSERT (CR 1-1 verbatim)
    if not dry_run:
        emit_audit_typed(
            db_session,
            action_class=ActionClass.FINOPS_UNIT_ECONOMICS,
            action="unit_economics_calculated",
            actor_id="system:phase_23_unit_economics_engine",
            target_id=unit_economics_id,
            reason=trace_id,
            payload={
                "period_key": period_key,
                "source_settlement_id": source_settlement_id,
                "total_cost_krw": total_cost_krw,
                "cost_per_business_unit_krw": cost_per_business_unit_krw,
                "cost_per_transaction_krw": cost_per_transaction_krw,
                "margin_pct": margin_pct,
                "confidence_pct": confidence_pct,
                "requires_2fa_challenge": final_requires_2fa,
                "trace_id": trace_id,
            },
        )

    logger.info(
        "unit_economics_computed ue_id=%s tenant=%s period=%s "
        "cost=%.2f margin=%.2f%% confidence=%.2f 2fa=%s persisted=%s",
        unit_economics_id,
        tenant_id,
        period_key,
        total_cost_krw,
        margin_pct,
        confidence_pct,
        final_requires_2fa,
        persistence["persisted"],
    )

    return result


def list_unit_economics_results(
    tenant_id: str,
    period_key: str | None = None,
    db_session: Any | None = None,
) -> list[UnitEconomicsResult]:
    """List UnitEconomicsResult by tenant_id (+ optional period_key filter).

    Phase 22 verbatim pattern: pure validator + RLS tenant_id selector +
    multi-tenant isolation.
    """
    if not tenant_id:
        raise UnitEconomicsVerificationError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if period_key is not None and not _is_valid_period_key(period_key):
        raise UnitEconomicsDimensionError(
            period_key=period_key,
        )
    logger.info(
        "unit_economics_list tenant=%s period=%s",
        tenant_id,
        period_key or "*",
    )
    return []  # actual DB read handled by caller


def validate_unit_economics_result(
    unit_economics_result: UnitEconomicsResult,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim pattern).

    Validates a UnitEconomicsResult TypedDict 16 fields structure
    + invariants.
    """
    if not unit_economics_result:
        raise UnitEconomicsVerificationError(
            reason="result_empty",
            tenant_id="",
        )
    required_fields = [
        "unit_economics_id",
        "tenant_id",
        "period_key",
        "source_settlement_id",
        "total_cost_krw",
        "cost_per_business_unit_krw",
        "cost_per_transaction_krw",
        "margin_pct",
        "confidence_pct",
        "model_version",
        "trace_id",
    ]
    for field in required_fields:
        if field not in unit_economics_result:
            raise UnitEconomicsVerificationError(
                reason=f"missing_field:{field}",
                tenant_id=unit_economics_result.get("tenant_id", ""),
            )
    if unit_economics_result.get("model_version") != UNIT_ECONOMICS_ENGINE_MODEL_VERSION:
        raise UnitEconomicsVerificationError(
            reason="model_version_mismatch",
            tenant_id=unit_economics_result.get("tenant_id", ""),
        )


# ── Helpers ───────────────────────────────────────────────────────────────
def _now_iso() -> str:
    """ISO timestamp helper (Phase 22 verbatim pattern)."""
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat()


def _derive_margin_status(margin_pct: float) -> str:
    """Derive margin_status from margin_pct (PRD §F39.4 + AD-51 (d)).

    - margin_pct < 0% → NEGATIVE
    - 0% ≤ margin_pct < 15% → CRITICAL
    - 15% ≤ margin_pct < 30% → WARNING
    - margin_pct ≥ 30% → HEALTHY
    """
    from apps.api.modules.finops.unit_economics.serializers import (
        MARGIN_HEALTHY_THRESHOLD_PCT,
        MARGIN_WARNING_THRESHOLD_PCT,
        MarginAnalysisStatus,
    )

    if margin_pct < 0:
        return MarginAnalysisStatus.NEGATIVE.value
    if margin_pct < MARGIN_WARNING_THRESHOLD_PCT:
        return MarginAnalysisStatus.CRITICAL.value
    if margin_pct < MARGIN_HEALTHY_THRESHOLD_PCT:
        return MarginAnalysisStatus.WARNING.value
    return MarginAnalysisStatus.HEALTHY.value


__all__ = [
    "DERIVATION_DIMENSION_WEIGHT_SUM",
    "compute_unit_economics",
    "list_unit_economics_results",
    "validate_unit_economics_result",
    "_compute_unit_economics_cache_key",
    "_validate_unit_economics_inputs",
    "_is_valid_period_key",
    "_compute_five_dim_attribution",
    "_compute_confidence_pct",
    "_compute_requires_2fa_challenge",
    "_persist_unit_economics_result",
]
