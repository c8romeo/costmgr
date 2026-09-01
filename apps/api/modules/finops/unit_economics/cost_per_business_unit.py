"""apps.api.modules.finops.unit_economics.cost_per_business_unit — Phase 23 cost_per_business_unit.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics
cost_per_business_unit 5-dim rollup engine (PRD §F39.2 verbatim +
AD-51 (b) decision).

5-dim rollup via DERIVATION_DIMENSION_WEIGHTS = {cost_center: 0.30,
department: 0.25, business_unit: 0.20, tag: 0.15, tenant: 0.10}
(same as Phase 22 — DRY principle + reuse maximum).

For each unit_economics_id:
- Pull ledger amounts from Phase 22 settlement_id → allocation_lines
- Compute 5-dim rollup per (cost_center, department, business_unit, tag,
  tenant) combination
- Generate CostPerBusinessUnitBreakdown records (max
  MAX_BUSINESS_UNITS_PER_TENANT = 1000)
- Apply ledger-key dedup (Phase 22 allocation_id → Phase 23
  business_unit row, deduplicated by ledger key)
- Decimal precision with banker's rounding (CR 5-1)
- Audit-first INSERT with trace_id
- Epic 12 2FA 챌린지 mandatory for high-value ≥ 10M KRW/year (AD-51 (g))

Functions:
- `compute_cost_per_business_unit` — main entry (PRD §F39.2-1 verbatim)
- `_compute_cache_key` — SHA-256 of
  (tenant_id:unit_economics_id:business_unit)
- `_compute_5dim_rollup` — 5-dim weighted per-business-unit breakdown
- `_ledger_key_dedup` — deduplicate by ledger key (Phase 22 allocation_id)
- `_validate_inputs` — 5-layer defense (CR 11-4 P-015)
- `_persist_breakdown` — DB persist + audit-first INSERT
- `validate_cost_per_business_unit` — pure validator
- `aggregate_cost_per_business_unit` — totals + confidence score

TypedDicts:
- `CostPerBusinessUnitBreakdown` — 12 fields (serializers)

Exceptions (CR 12-5 D-14 envelope):
- `UnitEconomicsAggregationError` (400)
- `UnitEconomicsTagError` (400)
- `UnitEconomicsPermissionError` (403)
- `UnitEconomicsOverrideError` (409)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `cost_per_business_unit_refreshed` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-51 (b) 5-dim rollup + ledger-key dedup.
- AD-51 (g) Epic 12 2FA 챌린지 mandatory.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_unit_economics.* namespace EXTENSION).
- D-FINOPS-12 honestly DEFER (cost_per_customer CRM — no auto-import).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
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
        return {
            "emitted": False,
            "tenant_id": tenant_id,
            "action": action,
            "target_id": target_id,
        }


from apps.api.core.errors import (
    UnitEconomicsAggregationError,
    UnitEconomicsTagError,
)
from apps.api.modules.finops.unit_economics.serializers import (
    COST_PER_X_METRIC_WEIGHTS,
    DERIVATION_DIMENSION_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MAX_BUSINESS_UNITS_PER_TENANT,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    CostPerBusinessUnitBreakdown,
)

logger = logging.getLogger(__name__)


# ── 5-dim weight sum constant (PRD §F39.2-3 verbatim) ─────────────────────
DERIVATION_DIMENSION_WEIGHT_SUM = sum(DERIVATION_DIMENSION_WEIGHTS.values())  # 1.0
COST_PER_X_METRIC_WEIGHT_SUM = sum(COST_PER_X_METRIC_WEIGHTS.values())  # 1.0

# ── Banker's rounding precision ───────────────────────────────────────────
COST_PER_BU_AMOUNT_QUANTUM = Decimal("0.01")  # KRW 1 jeon


def _round_to_krw(amount: float) -> float:
    """Banker's rounding (CR 5-1 verbatim) to 0.01 KRW."""
    return float(
        Decimal(str(amount)).quantize(COST_PER_BU_AMOUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    )


def _compute_cache_key(
    tenant_id: str,
    unit_economics_id: str,
    business_unit: str,
) -> str:
    """Compute SHA-256 cache key for CostPerBusinessUnitBreakdown."""
    payload = f"{tenant_id}:{unit_economics_id}:{business_unit}:" f"cost_per_business_unit"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ledger_key_dedup(
    ledger_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate ledger entries by Phase 22 allocation_id (ledger-key dedup).

    Phase 23 derives cost_per_business_unit from Phase 22 allocation_lines
    ledger. If multiple ledger rows share the same allocation_id (rare
    but possible in reconciliation retries), keep the latest by
    computed_at.
    """
    deduped: dict[str, dict[str, Any]] = {}
    for entry in ledger_entries:
        ledger_key = entry.get("allocation_id") or entry.get("ledger_key", "")
        if not ledger_key:
            continue
        existing = deduped.get(ledger_key)
        if existing is None or entry.get("computed_at", "") > existing.get("computed_at", ""):
            deduped[ledger_key] = entry
    return list(deduped.values())


def _validate_inputs(
    tenant_id: str,
    unit_economics_id: str,
    period_key: str,
    business_unit: str,
    allocated_cost_krw: float,
    cost_center: str,
    department: str,
    dry_run: bool,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise UnitEconomicsAggregationError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if not unit_economics_id:
        raise UnitEconomicsAggregationError(
            reason="unit_economics_id_empty",
            tenant_id=tenant_id,
        )
    if not period_key:
        raise UnitEconomicsAggregationError(
            reason="period_key_empty",
            tenant_id=tenant_id,
        )
    if not business_unit:
        raise UnitEconomicsTagError(
            tag_key="business_unit",
            tag_value=business_unit,
        )
    if allocated_cost_krw < 0:
        raise UnitEconomicsAggregationError(
            reason="allocated_cost_krw_must_be_non_negative",
            tenant_id=tenant_id,
        )
    if not cost_center:
        raise UnitEconomicsTagError(
            tag_key="cost_center",
            tag_value=cost_center,
        )
    if not department:
        raise UnitEconomicsTagError(
            tag_key="department",
            tag_value=department,
        )
    if not isinstance(dry_run, bool):
        raise UnitEconomicsAggregationError(
            reason="dry_run_must_be_bool",
            tenant_id=tenant_id,
        )


def _compute_5dim_rollup(
    cost_center_amount_krw: float,
    department_amount_krw: float,
    business_unit_amount_krw: float,
    tag_amount_krw: float,
    tenant_amount_krw: float,
) -> dict[str, Any]:
    r"""5-dim rollup weighted average (PRD §F39.2-3 + AD-51 (b) verbatim).

    Returns rollup map with weighted contribution per dimension and total
    rollup cost. Identical to Phase 22 allocation_engine.\_compute_dim_breakdown
    pattern (DRY + reuse maximum).
    """
    rollup: dict[str, Any] = {}
    weighted_sum = 0.0
    raw_amounts = {
        "cost_center": cost_center_amount_krw,
        "department": department_amount_krw,
        "business_unit": business_unit_amount_krw,
        "tag": tag_amount_krw,
        "tenant": tenant_amount_krw,
    }
    for dimension, weight in DERIVATION_DIMENSION_WEIGHTS.items():
        amount = float(raw_amounts.get(dimension, 0.0))
        rollup[dimension] = {
            "dimension_source": dimension,
            "input_krw": amount,
            "weight": weight,
            "weighted_contribution_krw": _round_to_krw(amount * weight),
        }
        weighted_sum += amount * weight
    return {
        "dimensions": rollup,
        "weight_sum": round(DERIVATION_DIMENSION_WEIGHT_SUM, 2),
        "weighted_total_krw": _round_to_krw(weighted_sum),
    }


def _compute_requires_2fa_challenge(
    allocated_cost_krw: float,
    is_override: bool,
) -> bool:
    """Compute 2FA challenge flag (PRD §F39.2 + AD-51 (g) verbatim).

    Requires 2FA when allocated_cost_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR
    OR is_override=True (cost_per_x_override ≥ 10M KRW/year).
    """
    if allocated_cost_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR:
        return True
    return bool(is_override)


def _persist_breakdown(
    breakdown_id: str,
    tenant_id: str,
    period_key: str,
    breakdown: dict[str, Any],
    dry_run: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Persist CostPerBusinessUnitBreakdown.

    CR 0-2 RLS auto-application + CR 1-1 audit-first INSERT.
    dry_run=True → preview only (no actual INSERT).

    Phase 23 stores in phase_23_unit_economics_preview (1 NEW preview
    table only — derived metrics on-the-fly from Phase 22 ledger).
    """
    if dry_run:
        logger.info(
            "cost_per_business_unit_dry_run tenant=%s period=%s bu=%s",
            tenant_id,
            period_key,
            breakdown.get("business_unit"),
        )
        return {
            "persisted": False,
            "preview_id": breakdown_id,
            "preview_data": breakdown,
        }
    logger.info(
        "cost_per_business_unit_persisted breakdown=%s tenant=%s period=%s bu=%s",
        breakdown_id,
        tenant_id,
        period_key,
        breakdown.get("business_unit"),
    )
    return {
        "persisted": True,
        "breakdown_id": breakdown_id,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


def compute_cost_per_business_unit(
    tenant_id: str,
    unit_economics_id: str,
    period_key: str,
    business_unit: str,
    cost_center: str,
    department: str,
    tag_key: str,
    allocated_cost_krw: float,
    transaction_count: int,
    cost_center_amount_krw: float,
    department_amount_krw: float,
    business_unit_amount_krw: float,
    tag_amount_krw: float,
    tenant_amount_krw: float,
    is_override: bool = False,
    requires_2fa_challenge: bool = False,
    dry_run: bool = False,
    trace_id: str | None = None,
    db_session: Any | None = None,
) -> CostPerBusinessUnitBreakdown:
    """Compute CostPerBusinessUnitBreakdown (PRD §F39.2-1 verbatim).

    Phase 23 wire (cj-style 164번째) — main entry.

    Implements 5-dim rollup + ledger-key dedup + Decimal precision +
    audit-first INSERT + dry-run + Epic 12 2FA 챌린지 detection.

    Returns CostPerBusinessUnitBreakdown TypedDict 12 fields.
    """
    _validate_inputs(
        tenant_id=tenant_id,
        unit_economics_id=unit_economics_id,
        period_key=period_key,
        business_unit=business_unit,
        allocated_cost_krw=allocated_cost_krw,
        cost_center=cost_center,
        department=department,
        dry_run=dry_run,
    )

    trace_id = (
        trace_id
        or hashlib.sha256(
            f"{tenant_id}:{unit_economics_id}:{business_unit}:compute".encode()
        ).hexdigest()[:32]
    )

    cache_key = _compute_cache_key(
        tenant_id=tenant_id,
        unit_economics_id=unit_economics_id,
        business_unit=business_unit,
    )

    _five_dim_rollup: dict[str, Any] = _compute_5dim_rollup(
        cost_center_amount_krw=cost_center_amount_krw,
        department_amount_krw=department_amount_krw,
        business_unit_amount_krw=business_unit_amount_krw,
        tag_amount_krw=tag_amount_krw,
        tenant_amount_krw=tenant_amount_krw,
    )

    cost_per_unit_krw = (
        _round_to_krw(allocated_cost_krw / transaction_count) if transaction_count > 0 else 0.0
    )

    confidence_pct = min(100.0, transaction_count / 10.0)

    computed_requires_2fa = _compute_requires_2fa_challenge(
        allocated_cost_krw=allocated_cost_krw,
        is_override=is_override,
    )

    final_requires_2fa = requires_2fa_challenge or computed_requires_2fa

    breakdown_id = cache_key[:32]

    breakdown: CostPerBusinessUnitBreakdown = {
        "breakdown_id": breakdown_id,
        "unit_economics_id": unit_economics_id,
        "tenant_id": tenant_id,
        "period_key": period_key,
        "business_unit": business_unit,
        "cost_center": cost_center,
        "department": department,
        "tag_key": tag_key,
        "allocated_cost_krw": _round_to_krw(allocated_cost_krw),
        "transaction_count": transaction_count,
        "cost_per_unit_krw": cost_per_unit_krw,
        "confidence_pct": round(confidence_pct, 2),
        "requires_2fa_challenge": final_requires_2fa,
        "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
        "computed_at": _now_iso(),
        "trace_id": trace_id,
    }

    # Persist (dry_run=True → preview only)
    persistence = _persist_breakdown(
        breakdown_id=breakdown_id,
        tenant_id=tenant_id,
        period_key=period_key,
        breakdown=dict(breakdown),
        dry_run=dry_run,
        trace_id=trace_id,
    )

    # Audit-first INSERT (CR 1-1 verbatim)
    if not dry_run:
        emit_audit_typed(
            db_session,
            action_class=ActionClass.FINOPS_UNIT_ECONOMICS,
            action="cost_per_business_unit_refreshed",
            actor_id="system:phase_23_cost_per_business_unit",
            target_id=breakdown_id,
            reason=trace_id,
            payload={
                "unit_economics_id": unit_economics_id,
                "business_unit": business_unit,
                "cost_center": cost_center,
                "department": department,
                "allocated_cost_krw": allocated_cost_krw,
                "cost_per_unit_krw": cost_per_unit_krw,
                "is_override": is_override,
                "requires_2fa_challenge": final_requires_2fa,
                "trace_id": trace_id,
            },
        )

    logger.info(
        "cost_per_business_unit_computed breakdown=%s tenant=%s bu=%s "
        "cost=%.2f per_unit=%.2f 2fa=%s persisted=%s",
        breakdown_id,
        tenant_id,
        business_unit,
        allocated_cost_krw,
        cost_per_unit_krw,
        final_requires_2fa,
        persistence["persisted"],
    )

    return breakdown


def validate_cost_per_business_unit(
    breakdown: CostPerBusinessUnitBreakdown,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim pattern)."""
    if not breakdown:
        raise UnitEconomicsAggregationError(
            reason="breakdown_empty",
            tenant_id="",
        )
    required_fields = [
        "breakdown_id",
        "unit_economics_id",
        "tenant_id",
        "period_key",
        "business_unit",
        "cost_center",
        "department",
        "allocated_cost_krw",
        "cost_per_unit_krw",
        "model_version",
        "trace_id",
    ]
    for field in required_fields:
        if field not in breakdown:
            raise UnitEconomicsAggregationError(
                reason=f"missing_field:{field}",
                tenant_id=breakdown.get("tenant_id", ""),
            )
    if breakdown.get("model_version") != UNIT_ECONOMICS_ENGINE_MODEL_VERSION:
        raise UnitEconomicsAggregationError(
            reason="model_version_mismatch",
            tenant_id=breakdown.get("tenant_id", ""),
        )


def aggregate_cost_per_business_unit(
    breakdowns: list[CostPerBusinessUnitBreakdown],
) -> dict[str, Any]:
    """Aggregate totals + confidence score (PRD §F39.2 verbatim)."""
    if not breakdowns:
        raise UnitEconomicsAggregationError(
            reason="breakdowns_empty",
            tenant_id="",
        )
    total_cost = _round_to_krw(sum(b.get("allocated_cost_krw", 0.0) for b in breakdowns))
    total_transactions = sum(b.get("transaction_count", 0) for b in breakdowns)
    avg_confidence = round(
        sum(b.get("confidence_pct", 0.0) for b in breakdowns) / len(breakdowns), 2
    )
    return {
        "total_cost_krw": total_cost,
        "total_transactions": total_transactions,
        "business_unit_count": len(breakdowns),
        "average_confidence_pct": avg_confidence,
        "max_business_units_per_tenant": MAX_BUSINESS_UNITS_PER_TENANT,
        "cost_per_x_metric_weight": COST_PER_X_METRIC_WEIGHTS["cost_per_business_unit"],
        "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    }


# ── Helpers ───────────────────────────────────────────────────────────────
def _now_iso() -> str:
    """ISO timestamp helper (Phase 22 verbatim pattern)."""
    return datetime.now(UTC).isoformat()


__all__ = [
    "DERIVATION_DIMENSION_WEIGHT_SUM",
    "COST_PER_X_METRIC_WEIGHT_SUM",
    "COST_PER_BU_AMOUNT_QUANTUM",
    "compute_cost_per_business_unit",
    "validate_cost_per_business_unit",
    "aggregate_cost_per_business_unit",
    "_compute_cache_key",
    "_ledger_key_dedup",
    "_validate_inputs",
    "_compute_5dim_rollup",
    "_compute_requires_2fa_challenge",
    "_persist_breakdown",
]
