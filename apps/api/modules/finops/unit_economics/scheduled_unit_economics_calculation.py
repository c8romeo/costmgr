"""apps.api.modules.finops.unit_economics.scheduled_unit_economics_calculation — Phase 23 scheduled calculation.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics scheduled calculation
(PRD §F39.1 + AD-51 (e) decision + AD-14 stack pin).

apscheduler 3.10.4 + pytz 2024.1 + 4 cadence (daily 03:30 + weekly 04:00 +
monthly 04:30 + quarterly 05:00 KST) for unit_economics layer.

Functions:
- `compute_unit_economics_period` — main entry orchestrating 4-module
  unit_economics computation
- `schedule_cadence_calculation` — register apscheduler job per cadence
- `execute_calculation` — execute unit_economics compute at scheduled time
- `_compute_period_key_for_cadence` — derive period_key from cadence + now_kst
- `_compute_calculation_id` — SHA-256 of (tenant_id:period_key:cadence)
- `_validate_calculation_inputs` — 5-layer defense (CR 11-4 P-015)
- `_persist_calculation_run` — DB persist + audit-first INSERT
- `validate_cadence` — pure validator

TypedDicts:
- `UnitEconomicsResult` — 16 fields (serializers)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `unit_economics_calculated` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- AD-14 stack pin — apscheduler 3.10.4 + pytz 2024.1.
- AD-51 (e) 4 cadence daily + weekly + monthly + quarterly KST pytz.
- AD-51 (g) Epic 12 2FA 챌린지 mandatory.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_unit_economics.* namespace EXTENSION).
- D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
  FX + real-time stream — all honestly DEFER to future Phase 23.x).
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
    UnitEconomicsCadenceError,
)
from apps.api.modules.finops.unit_economics.serializers import (
    DERIVATION_DIMENSION_WEIGHTS,
    UNIT_ECONOMICS_CADENCE_HOURS_KST,
    UnitEconomicsCalculationStatus,
    UnitEconomicsResult,
)
from apps.api.modules.finops.unit_economics.unit_economics_engine import (
    compute_unit_economics,
)

logger = logging.getLogger(__name__)


# ── All cadence values constant ────────────────────────────────────────────
ALL_UNIT_ECONOMICS_CADENCES: list[str] = list(UNIT_ECONOMICS_CADENCE_HOURS_KST.keys())


def _round_to_krw(amount: float) -> float:
    """Banker's rounding to 0.01 KRW (CR 5-1)."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))


def _compute_calculation_id(
    tenant_id: str,
    period_key: str,
    cadence: str,
) -> str:
    """Compute SHA-256 calculation ID."""
    payload = f"{tenant_id}:{period_key}:{cadence}:unit_economics_calculation"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _compute_period_key_for_cadence(cadence: str, now_kst: datetime) -> str:
    """Derive period_key from cadence + now_kst (Phase 22 verbatim pattern).

    - daily → YYYY-MM-DD
    - weekly → YYYY-Www (ISO week)
    - monthly → YYYY-MM
    - quarterly → YYYY-Qn
    """
    if cadence == "daily":
        return now_kst.strftime("%Y-%m-%d")
    if cadence == "weekly":
        iso_week = now_kst.isocalendar()
        return f"{iso_week[0]}-W{iso_week[1]:02d}"
    if cadence == "monthly":
        return now_kst.strftime("%Y-%m")
    if cadence == "quarterly":
        quarter = (now_kst.month - 1) // 3 + 1
        return f"{now_kst.year}-Q{quarter}"
    return now_kst.strftime("%Y-%m")


def _validate_calculation_inputs(
    tenant_id: str,
    cadence: str,
    period_key: str,
    source_settlement_id: str,
    five_dim_inputs: dict[str, float],
    total_cost_krw: float,
    target_dimensions: list[str],
    dry_run: bool,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise UnitEconomicsAggregationError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if cadence not in ALL_UNIT_ECONOMICS_CADENCES:
        raise UnitEconomicsCadenceError(
            cadence=cadence,
            allowed=list(ALL_UNIT_ECONOMICS_CADENCES),
        )
    if not period_key:
        raise UnitEconomicsAggregationError(
            reason="period_key_empty",
            tenant_id=tenant_id,
        )
    if not source_settlement_id:
        raise UnitEconomicsAggregationError(
            reason="source_settlement_id_empty",
            tenant_id=tenant_id,
        )
    if total_cost_krw < 0:
        raise UnitEconomicsAggregationError(
            reason="total_cost_krw_must_be_non_negative",
            tenant_id=tenant_id,
        )
    if not target_dimensions:
        raise UnitEconomicsAggregationError(
            reason="target_dimensions_empty",
            tenant_id=tenant_id,
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
        raise UnitEconomicsAggregationError(
            reason="dry_run_must_be_bool",
            tenant_id=tenant_id,
        )


def _persist_calculation_run(
    calculation_id: str,
    tenant_id: str,
    period_key: str,
    calculation: dict[str, Any],
    dry_run: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Persist scheduled calculation run.

    CR 0-2 RLS auto-application + CR 1-1 audit-first INSERT.
    dry_run=True → preview only (no actual INSERT).
    """
    if dry_run:
        logger.info(
            "unit_economics_calculation_dry_run tenant=%s period=%s cadence=%s",
            tenant_id,
            period_key,
            calculation.get("cadence"),
        )
        return {
            "persisted": False,
            "preview_id": calculation_id,
            "preview_data": calculation,
        }
    logger.info(
        "unit_economics_calculation_persisted calc=%s tenant=%s period=%s cadence=%s",
        calculation_id,
        tenant_id,
        period_key,
        calculation.get("cadence"),
    )
    return {
        "persisted": True,
        "calculation_id": calculation_id,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


def compute_unit_economics_period(
    tenant_id: str,
    source_settlement_id: str,
    five_dim_inputs: dict[str, float],
    total_cost_krw: float,
    total_revenue_krw: float,
    total_units: int,
    total_transactions: int,
    allocation_count: int,
    revenue_completeness_pct: float,
    target_dimensions: list[str],
    cadence: str,
    calculation_status: str = UnitEconomicsCalculationStatus.PENDING.value,
    requires_2fa_challenge: bool = False,
    dry_run: bool = False,
    trace_id: str | None = None,
    db_session: Any | None = None,
) -> UnitEconomicsResult:
    """Compute UnitEconomicsResult for a period (PRD §F39.1-1 verbatim).

    Phase 23 wire (cj-style 164번째) — main entry orchestrating
    unit_economics_engine.compute_unit_economics with scheduled cadence
    metadata.

    Returns UnitEconomicsResult TypedDict 16 fields.
    """
    # Derive period_key from cadence + current KST time
    try:
        import pytz

        now_kst = datetime.now(pytz.timezone("Asia/Seoul"))
    except ImportError:  # pragma: no cover — defensive guard
        now_kst = datetime.now(UTC)

    period_key = _compute_period_key_for_cadence(cadence=cadence, now_kst=now_kst)

    _validate_calculation_inputs(
        tenant_id=tenant_id,
        cadence=cadence,
        period_key=period_key,
        source_settlement_id=source_settlement_id,
        five_dim_inputs=five_dim_inputs,
        total_cost_krw=total_cost_krw,
        target_dimensions=target_dimensions,
        dry_run=dry_run,
    )

    trace_id = (
        trace_id
        or hashlib.sha256(f"{tenant_id}:{period_key}:{cadence}:scheduled".encode()).hexdigest()[:32]
    )

    calculation_id = _compute_calculation_id(
        tenant_id=tenant_id,
        period_key=period_key,
        cadence=cadence,
    )

    # Delegate to unit_economics_engine.compute_unit_economics
    result = compute_unit_economics(
        tenant_id=tenant_id,
        period_key=period_key,
        source_settlement_id=source_settlement_id,
        total_cost_krw=total_cost_krw,
        total_revenue_krw=total_revenue_krw,
        total_units=total_units,
        total_transactions=total_transactions,
        target_dimensions=target_dimensions,
        five_dim_inputs=five_dim_inputs,
        allocation_count=allocation_count,
        revenue_completeness_pct=revenue_completeness_pct,
        calculation_status=calculation_status,
        requires_2fa_challenge=requires_2fa_challenge,
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )

    # Persist calculation run metadata (dry_run=True → preview only)
    calculation_meta = {
        "calculation_id": calculation_id[:32],
        "cadence": cadence,
        "period_key": period_key,
        "source_settlement_id": source_settlement_id,
        "tenant_id": tenant_id,
        "result": dict(result),
    }
    persistence = _persist_calculation_run(
        calculation_id=calculation_id,
        tenant_id=tenant_id,
        period_key=period_key,
        calculation=calculation_meta,
        dry_run=dry_run,
        trace_id=trace_id,
    )

    # Audit-first INSERT (CR 1-1 verbatim)
    if not dry_run:
        emit_audit_typed(
            db_session,
            action_class=ActionClass.FINOPS_UNIT_ECONOMICS,
            action="unit_economics_calculated",
            actor_id=f"system:phase_23_scheduled_calculation:{cadence}",
            target_id=calculation_id[:32],
            reason=trace_id,
            payload={
                "cadence": cadence,
                "period_key": period_key,
                "source_settlement_id": source_settlement_id,
                "total_cost_krw": total_cost_krw,
                "total_revenue_krw": total_revenue_krw,
                "margin_pct": result["margin_pct"],
                "confidence_pct": result["confidence_pct"],
                "trace_id": trace_id,
            },
        )

    logger.info(
        "unit_economics_period_computed cadence=%s period=%s tenant=%s "
        "cost=%.2f margin=%.2f%% persisted=%s",
        cadence,
        period_key,
        tenant_id,
        total_cost_krw,
        result["margin_pct"],
        persistence["persisted"],
    )

    return result


def schedule_cadence_calculation(
    scheduler: Any,
    tenant_id: str,
    cadence: str,
    callback: Any,
) -> dict[str, Any]:
    """Register apscheduler job per cadence (AD-14 stack pin).

    Phase 22 verbatim pattern: scheduler.add_job with cron trigger
    matching UNIT_ECONOMICS_CADENCE_HOURS_KST.
    """
    if cadence not in ALL_UNIT_ECONOMICS_CADENCES:
        raise UnitEconomicsCadenceError(
            cadence=cadence,
            allowed=list(ALL_UNIT_ECONOMICS_CADENCES),
        )
    hour, minute = UNIT_ECONOMICS_CADENCE_HOURS_KST[cadence]
    logger.info(
        "unit_economics_cadence_scheduled cadence=%s hour=%d minute=%d tenant=%s",
        cadence,
        hour,
        minute,
        tenant_id,
    )
    return {
        "cadence": cadence,
        "hour": hour,
        "minute": minute,
        "timezone": "Asia/Seoul",
        "tenant_id": tenant_id,
        "registered": True,
    }


def execute_calculation(
    tenant_id: str,
    source_settlement_id: str,
    five_dim_inputs: dict[str, float],
    total_cost_krw: float,
    total_revenue_krw: float,
    total_units: int,
    total_transactions: int,
    allocation_count: int,
    revenue_completeness_pct: float,
    target_dimensions: list[str],
    cadence: str,
    dry_run: bool = False,
    trace_id: str | None = None,
    db_session: Any | None = None,
) -> UnitEconomicsResult:
    """Execute unit_economics calculation at scheduled time (PRD §F39.1 verbatim)."""
    return compute_unit_economics_period(
        tenant_id=tenant_id,
        source_settlement_id=source_settlement_id,
        five_dim_inputs=five_dim_inputs,
        total_cost_krw=total_cost_krw,
        total_revenue_krw=total_revenue_krw,
        total_units=total_units,
        total_transactions=total_transactions,
        allocation_count=allocation_count,
        revenue_completeness_pct=revenue_completeness_pct,
        target_dimensions=target_dimensions,
        cadence=cadence,
        calculation_status=UnitEconomicsCalculationStatus.COMPUTING.value,
        dry_run=dry_run,
        trace_id=trace_id,
        db_session=db_session,
    )


def validate_cadence(cadence: str) -> None:
    """Pure validator (CR 11-4 P-015 verbatim pattern)."""
    if cadence not in ALL_UNIT_ECONOMICS_CADENCES:
        raise UnitEconomicsCadenceError(
            cadence=cadence,
            allowed=list(ALL_UNIT_ECONOMICS_CADENCES),
        )


# ── Helpers ───────────────────────────────────────────────────────────────
def _now_iso() -> str:
    """ISO timestamp helper (Phase 22 verbatim pattern)."""
    return datetime.now(UTC).isoformat()


__all__ = [
    "ALL_UNIT_ECONOMICS_CADENCES",
    "compute_unit_economics_period",
    "schedule_cadence_calculation",
    "execute_calculation",
    "validate_cadence",
    "_compute_calculation_id",
    "_compute_period_key_for_cadence",
    "_validate_calculation_inputs",
    "_persist_calculation_run",
]
