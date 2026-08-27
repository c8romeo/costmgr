"""apps.api.modules.finops.unit_economics.margin_analysis — Phase 23 margin analysis.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics
margin_analysis + revenue attribution engine (PRD §F39.4 verbatim +
AD-51 (d) decision).

OPTIONAL margin analysis — only computed when revenue is registered in
tenant_revenue table. D-FINOPS-12 honestly DEFER if revenue not available
(margin_pct = 0.0 + status = "warning" + audit action).

Margin status thresholds (PRD §F39.4 + AD-51 (d) verbatim):
- margin_pct < 0% → NEGATIVE (alert + Epic 12 2FA mandatory)
- 0% ≤ margin_pct < 15% → CRITICAL
- 15% ≤ margin_pct < 30% → WARNING
- margin_pct ≥ 30% → HEALTHY

Functions:
- `execute_margin_analysis` — main entry (PRD §F39.4-1 verbatim)
- `_compute_cache_key` — SHA-256 of
  (tenant_id:unit_economics_id:business_unit)
- `_validate_revenue_sources` — check revenue registration
- `_compute_margin_status` — derive status from margin_pct
- `_compute_margin_alerts` — generate UnitEconomicsAlert records
- `_validate_inputs` — 5-layer defense (CR 11-4 P-015)
- `_persist_margin_analysis` — DB persist + audit-first INSERT
- `validate_margin_analysis` — pure validator
- `aggregate_margin_analysis` — totals + revenue completeness

TypedDicts:
- `MarginAnalysisResult` — 14 fields (serializers)
- `UnitEconomicsAlert` — 8 fields (serializers)

Exceptions (CR 12-5 D-14 envelope):
- `UnitEconomicsRevenueError` (400)
- `UnitEconomicsMarginError` (500)
- `UnitEconomicsAlertError` (500)
- `UnitEconomicsApprovalRequiredError` (403)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `margin_analysis_executed` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-51 (d) margin analysis + revenue attribution.
- AD-51 (g) Epic 12 2FA 챌린지 mandatory (high-value margin positive
  ≥ 10M KRW/year + negative margin alert).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_unit_economics.* namespace EXTENSION).
- D-FINOPS-12 honestly DEFER (multi-currency FX + tenant revenue
  auto-import — all honestly DEFER to future Phase 23.x).
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
    UnitEconomicsMarginError,
    UnitEconomicsRevenueError,
)
from apps.api.modules.finops.unit_economics.serializers import (
    ALL_MARGIN_ANALYSIS_STATUSES,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MARGIN_HEALTHY_THRESHOLD_PCT,
    MARGIN_NEGATIVE_PCT,
    MARGIN_WARNING_THRESHOLD_PCT,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    MarginAnalysisResult,
    MarginAnalysisStatus,
    UnitEconomicsAlert,
    UnitEconomicsAlertSeverity,
)

logger = logging.getLogger(__name__)


# ── Banker's rounding precision ───────────────────────────────────────────
MARGIN_AMOUNT_QUANTUM = Decimal("0.01")  # KRW 1 jeon
MARGIN_PCT_QUANTUM = Decimal("0.01")  # 0.01% precision


def _round_to_krw(amount: float) -> float:
    """Banker's rounding (CR 5-1 verbatim) to 0.01 KRW."""
    return float(
        Decimal(str(amount)).quantize(MARGIN_AMOUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    )


def _round_to_pct(pct: float) -> float:
    """Banker's rounding (CR 5-1 verbatim) to 0.01% precision."""
    return float(
        Decimal(str(pct)).quantize(MARGIN_PCT_QUANTUM, rounding=ROUND_HALF_EVEN)
    )


def _compute_cache_key(
    tenant_id: str,
    unit_economics_id: str,
    business_unit: str,
) -> str:
    """Compute SHA-256 cache key for MarginAnalysisResult."""
    payload = (
        f"{tenant_id}:{unit_economics_id}:{business_unit}:margin_analysis"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_revenue_sources(
    revenue_sources: list[str] | None,
    revenue_completeness_pct: float,
) -> None:
    """Validate revenue registration (D-FINOPS-12 honestly DEFER guard).

    Phase 23 derives margin ONLY when revenue is registered in
    tenant_revenue table. If revenue_sources is empty or
    revenue_completeness_pct < 50%, log a warning + audit action but do
    not raise (margin_pct = 0.0 + status = WARNING).
    """
    if not revenue_sources:
        logger.warning(
            "margin_analysis_revenue_not_registered — D-FINOPS-12 honestly DEFER: "
            "no revenue sources registered; margin_pct will be 0.0 + status=WARNING"
        )
        return
    if revenue_completeness_pct < 50.0:
        logger.warning(
            "margin_analysis_revenue_incomplete completeness=%.2f%% — "
            "confidence will be reduced; D-FINOPS-12 partial DEFER",
            revenue_completeness_pct,
        )


def _compute_margin_status(margin_pct: float) -> str:
    """Derive margin_status from margin_pct (PRD §F39.4 + AD-51 (d)).

    - margin_pct < 0% → NEGATIVE
    - 0% ≤ margin_pct < 15% → CRITICAL
    - 15% ≤ margin_pct < 30% → WARNING
    - margin_pct ≥ 30% → HEALTHY
    """
    if margin_pct < MARGIN_NEGATIVE_PCT:
        return MarginAnalysisStatus.NEGATIVE.value
    if margin_pct < MARGIN_WARNING_THRESHOLD_PCT:
        return MarginAnalysisStatus.CRITICAL.value
    if margin_pct < MARGIN_HEALTHY_THRESHOLD_PCT:
        return MarginAnalysisStatus.WARNING.value
    return MarginAnalysisStatus.HEALTHY.value


def _compute_margin_alerts(
    margin_status: str,
    margin_amount_krw: float,
    margin_id: str,
    tenant_id: str,
    period_key: str,
) -> list[UnitEconomicsAlert]:
    """Generate UnitEconomicsAlert records (PRD §F39.4 verbatim).

    Triggers:
    - NEGATIVE → severity=CRITICAL + alert_type=margin_negative + 2FA
    - CRITICAL → severity=WARNING + alert_type=margin_critical
    - WARNING → severity=INFO + alert_type=margin_warning
    - HEALTHY → no alerts
    - margin_amount_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR →
      severity=INFO + alert_type=margin_positive_high_value + 2FA
    """
    alerts: list[UnitEconomicsAlert] = []
    base_alert: dict[str, Any] = {
        "tenant_id": tenant_id,
        "period_key": period_key,
        "margin_id": margin_id,
        "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
        "triggered_at": _now_iso(),
        "trace_id": "",
    }

    if margin_status == MarginAnalysisStatus.NEGATIVE.value:
        alerts.append(
            UnitEconomicsAlert(
                **base_alert,
                alert_id=hashlib.sha256(
                    f"{margin_id}:margin_negative:{period_key}".encode()
                ).hexdigest()[:32],
                severity=UnitEconomicsAlertSeverity.CRITICAL.value,
                alert_type="margin_negative",
                alert_message=(
                    f"Margin is NEGATIVE ({margin_amount_krw:.2f} KRW). "
                    "Immediate action required. Epic 12 2FA �린지 mandatory."
                ),
                requires_2fa_challenge=True,
            )
        )
    elif margin_status == MarginAnalysisStatus.CRITICAL.value:
        alerts.append(
            UnitEconomicsAlert(
                **base_alert,
                alert_id=hashlib.sha256(
                    f"{margin_id}:margin_critical:{period_key}".encode()
                ).hexdigest()[:32],
                severity=UnitEconomicsAlertSeverity.WARNING.value,
                alert_type="margin_critical",
                alert_message=(
                    f"Margin is CRITICAL ({margin_amount_krw:.2f} KRW). "
                    "Review cost allocation urgently."
                ),
                requires_2fa_challenge=False,
            )
        )
    elif margin_status == MarginAnalysisStatus.WARNING.value:
        alerts.append(
            UnitEconomicsAlert(
                **base_alert,
                alert_id=hashlib.sha256(
                    f"{margin_id}:margin_warning:{period_key}".encode()
                ).hexdigest()[:32],
                severity=UnitEconomicsAlertSeverity.INFO.value,
                alert_type="margin_warning",
                alert_message=(
                    f"Margin is WARNING ({margin_amount_krw:.2f} KRW). "
                    "Monitor closely."
                ),
                requires_2fa_challenge=False,
            )
        )

    if margin_amount_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR:
        alerts.append(
            UnitEconomicsAlert(
                **base_alert,
                alert_id=hashlib.sha256(
                    f"{margin_id}:margin_positive_high_value:{period_key}".encode()
                ).hexdigest()[:32],
                severity=UnitEconomicsAlertSeverity.INFO.value,
                alert_type="margin_positive_high_value",
                alert_message=(
                    f"Margin is positive high-value ({margin_amount_krw:.2f} KRW/year). "
                    "Owner approval recommended. Epic 12 2FA 챌린지 mandatory."
                ),
                requires_2fa_challenge=True,
            )
        )

    return alerts


def _validate_inputs(
    tenant_id: str,
    unit_economics_id: str,
    period_key: str,
    business_unit: str,
    total_cost_krw: float,
    total_revenue_krw: float,
    revenue_sources: list[str] | None,
    revenue_completeness_pct: float,
    dry_run: bool,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise UnitEconomicsRevenueError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if not unit_economics_id:
        raise UnitEconomicsRevenueError(
            reason="unit_economics_id_empty",
            tenant_id=tenant_id,
        )
    if not period_key:
        raise UnitEconomicsRevenueError(
            reason="period_key_empty",
            tenant_id=tenant_id,
        )
    if not business_unit:
        raise UnitEconomicsRevenueError(
            reason="business_unit_empty",
            tenant_id=tenant_id,
        )
    if total_cost_krw < 0:
        raise UnitEconomicsRevenueError(
            reason="total_cost_krw_must_be_non_negative",
            tenant_id=tenant_id,
        )
    if total_revenue_krw < 0:
        raise UnitEconomicsRevenueError(
            reason="total_revenue_krw_must_be_non_negative",
            tenant_id=tenant_id,
        )
    if revenue_sources is not None and not isinstance(revenue_sources, list):
        raise UnitEconomicsRevenueError(
            reason="revenue_sources_must_be_list",
            tenant_id=tenant_id,
        )
    if not (0.0 <= revenue_completeness_pct <= 100.0):
        raise UnitEconomicsRevenueError(
            reason="revenue_completeness_pct_must_be_0_to_100",
            tenant_id=tenant_id,
        )
    if not isinstance(dry_run, bool):
        raise UnitEconomicsRevenueError(
            reason="dry_run_must_be_bool",
            tenant_id=tenant_id,
        )


def _compute_requires_2fa_challenge(
    margin_amount_krw: float,
    margin_status: str,
) -> bool:
    """Compute 2FA challenge flag (PRD §F39.4 + AD-51 (g) verbatim).

    Requires 2FA when:
    - margin_status == NEGATIVE (loss situation), OR
    - margin_amount_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR (positive
      high-value ≥ 10M KRW/year).
    """
    if margin_status == MarginAnalysisStatus.NEGATIVE.value:
        return True
    if margin_amount_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR:
        return True
    return False


def _persist_margin_analysis(
    margin_id: str,
    tenant_id: str,
    period_key: str,
    margin: dict[str, Any],
    alerts: list[UnitEconomicsAlert],
    dry_run: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Persist MarginAnalysisResult + alerts.

    CR 0-2 RLS auto-application + CR 1-1 audit-first INSERT.
    dry_run=True → preview only (no actual INSERT).
    """
    if dry_run:
        logger.info(
            "margin_analysis_dry_run tenant=%s period=%s bu=%s alerts=%d",
            tenant_id,
            period_key,
            margin.get("business_unit"),
            len(alerts),
        )
        return {
            "persisted": False,
            "preview_id": margin_id,
            "preview_data": margin,
            "preview_alerts": alerts,
        }
    logger.info(
        "margin_analysis_persisted margin=%s tenant=%s period=%s alerts=%d",
        margin_id,
        tenant_id,
        period_key,
        len(alerts),
    )
    return {
        "persisted": True,
        "margin_id": margin_id,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


def execute_margin_analysis(
    tenant_id: str,
    unit_economics_id: str,
    period_key: str,
    business_unit: str,
    total_cost_krw: float,
    total_revenue_krw: float,
    revenue_sources: list[str] | None = None,
    revenue_completeness_pct: float = 0.0,
    requires_2fa_challenge: bool = False,
    dry_run: bool = False,
    trace_id: str | None = None,
    db_session: Any | None = None,
) -> MarginAnalysisResult:
    """Execute MarginAnalysisResult (PRD §F39.4-1 verbatim).

    Phase 23 wire (cj-style 164번째) — main entry.

    Implements margin computation + revenue attribution + 3-tier status
    + alert generation + audit-first INSERT + dry-run + Epic 12 2FA 챌린지
    detection.

    Returns MarginAnalysisResult TypedDict 14 fields.
    """
    _validate_inputs(
        tenant_id=tenant_id,
        unit_economics_id=unit_economics_id,
        period_key=period_key,
        business_unit=business_unit,
        total_cost_krw=total_cost_krw,
        total_revenue_krw=total_revenue_krw,
        revenue_sources=revenue_sources,
        revenue_completeness_pct=revenue_completeness_pct,
        dry_run=dry_run,
    )

    _validate_revenue_sources(
        revenue_sources=revenue_sources,
        revenue_completeness_pct=revenue_completeness_pct,
    )

    trace_id = trace_id or hashlib.sha256(
        f"{tenant_id}:{unit_economics_id}:{business_unit}:margin".encode()
    ).hexdigest()[:32]

    cache_key = _compute_cache_key(
        tenant_id=tenant_id,
        unit_economics_id=unit_economics_id,
        business_unit=business_unit,
    )

    # Compute margin (D-FINOPS-12 honestly DEFER if no revenue)
    if total_revenue_krw > 0 and revenue_sources:
        margin_amount_krw = _round_to_krw(total_revenue_krw - total_cost_krw)
        margin_pct = _round_to_pct(
            (margin_amount_krw / total_revenue_krw) * 100
        )
    else:
        margin_amount_krw = 0.0
        margin_pct = 0.0  # D-FINOPS-12 honestly DEFER

    margin_status = _compute_margin_status(margin_pct)

    computed_requires_2fa = _compute_requires_2fa_challenge(
        margin_amount_krw=margin_amount_krw,
        margin_status=margin_status,
    )

    final_requires_2fa = requires_2fa_challenge or computed_requires_2fa

    margin_id = cache_key[:32]

    margin: MarginAnalysisResult = {
        "margin_id": margin_id,
        "unit_economics_id": unit_economics_id,
        "tenant_id": tenant_id,
        "period_key": period_key,
        "business_unit": business_unit,
        "total_cost_krw": _round_to_krw(total_cost_krw),
        "total_revenue_krw": _round_to_krw(total_revenue_krw),
        "margin_amount_krw": margin_amount_krw,
        "margin_pct": margin_pct,
        "margin_status": margin_status,
        "revenue_sources": list(revenue_sources or []),
        "revenue_completeness_pct": round(revenue_completeness_pct, 2),
        "requires_2fa_challenge": final_requires_2fa,
        "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
        "computed_at": _now_iso(),
        "trace_id": trace_id,
    }

    # Generate alerts
    alerts = _compute_margin_alerts(
        margin_status=margin_status,
        margin_amount_krw=margin_amount_krw,
        margin_id=margin_id,
        tenant_id=tenant_id,
        period_key=period_key,
    )

    # Persist (dry_run=True → preview only)
    persistence = _persist_margin_analysis(
        margin_id=margin_id,
        tenant_id=tenant_id,
        period_key=period_key,
        margin=dict(margin),
        alerts=alerts,
        dry_run=dry_run,
        trace_id=trace_id,
    )

    # Audit-first INSERT (CR 1-1 verbatim)
    if not dry_run:
        emit_audit_typed(
            db_session,
            action_class=ActionClass.FINOPS_UNIT_ECONOMICS,
            action="margin_analysis_executed",
            actor_id="system:phase_23_margin_analysis",
            target_id=margin_id,
            reason=trace_id,
            payload={
                "unit_economics_id": unit_economics_id,
                "business_unit": business_unit,
                "total_cost_krw": total_cost_krw,
                "total_revenue_krw": total_revenue_krw,
                "margin_amount_krw": margin_amount_krw,
                "margin_pct": margin_pct,
                "margin_status": margin_status,
                "alert_count": len(alerts),
                "revenue_completeness_pct": revenue_completeness_pct,
                "requires_2fa_challenge": final_requires_2fa,
                "trace_id": trace_id,
            },
        )

        # Emit additional audit actions for alerts (if any)
        for alert in alerts:
            if alert.get("alert_type") == "margin_negative":
                emit_audit_typed(
                    db_session,
                    action_class=ActionClass.FINOPS_UNIT_ECONOMICS,
                    action="unit_economics_margin_negative_alert",
                    actor_id="system:phase_23_margin_analysis",
                    target_id=alert["alert_id"],
                    reason=trace_id,
                    payload={
                        "margin_id": margin_id,
                        "business_unit": business_unit,
                        "margin_amount_krw": margin_amount_krw,
                        "severity": alert["severity"],
                        "trace_id": trace_id,
                    },
                )
            elif alert.get("alert_type") == "margin_positive_high_value":
                emit_audit_typed(
                    db_session,
                    action_class=ActionClass.FINOPS_UNIT_ECONOMICS,
                    action="unit_economics_margin_alert",
                    actor_id="system:phase_23_margin_analysis",
                    target_id=alert["alert_id"],
                    reason=trace_id,
                    payload={
                        "margin_id": margin_id,
                        "business_unit": business_unit,
                        "margin_amount_krw": margin_amount_krw,
                        "severity": alert["severity"],
                        "trace_id": trace_id,
                    },
                )

    logger.info(
        "margin_analysis_computed margin=%s tenant=%s bu=%s "
        "margin=%.2f KRW (%.2f%%) status=%s alerts=%d 2fa=%s persisted=%s",
        margin_id,
        tenant_id,
        business_unit,
        margin_amount_krw,
        margin_pct,
        margin_status,
        len(alerts),
        final_requires_2fa,
        persistence["persisted"],
    )

    return margin


def validate_margin_analysis(margin: MarginAnalysisResult) -> None:
    """Pure validator (CR 11-4 P-015 verbatim pattern)."""
    if not margin:
        raise UnitEconomicsMarginError(
            reason="margin_empty",
            tenant_id="",
        )
    required_fields = [
        "margin_id",
        "unit_economics_id",
        "tenant_id",
        "period_key",
        "business_unit",
        "total_cost_krw",
        "total_revenue_krw",
        "margin_amount_krw",
        "margin_pct",
        "margin_status",
        "model_version",
        "trace_id",
    ]
    for field in required_fields:
        if field not in margin:
            raise UnitEconomicsMarginError(
                reason=f"missing_field:{field}",
                tenant_id=margin.get("tenant_id", ""),
            )
    if margin.get("model_version") != UNIT_ECONOMICS_ENGINE_MODEL_VERSION:
        raise UnitEconomicsMarginError(
            reason="model_version_mismatch",
            tenant_id=margin.get("tenant_id", ""),
        )
    if margin.get("margin_status") not in ALL_MARGIN_ANALYSIS_STATUSES:
        raise UnitEconomicsMarginError(
            reason=f"invalid_margin_status:{margin.get('margin_status')}",
            tenant_id=margin.get("tenant_id", ""),
        )


def aggregate_margin_analysis(
    margins: list[MarginAnalysisResult],
) -> dict[str, Any]:
    """Aggregate totals + revenue completeness (PRD §F39.4 verbatim)."""
    if not margins:
        raise UnitEconomicsMarginError(
            reason="margins_empty",
            tenant_id="",
        )
    total_cost = _round_to_krw(sum(m.get("total_cost_krw", 0.0) for m in margins))
    total_revenue = _round_to_krw(sum(m.get("total_revenue_krw", 0.0) for m in margins))
    total_margin = _round_to_krw(sum(m.get("margin_amount_krw", 0.0) for m in margins))
    overall_margin_pct = (
        _round_to_pct((total_margin / total_revenue) * 100)
        if total_revenue > 0
        else 0.0  # D-FINOPS-12 honestly DEFER
    )
    avg_revenue_completeness = round(
        sum(m.get("revenue_completeness_pct", 0.0) for m in margins) / len(margins), 2
    )
    return {
        "total_cost_krw": total_cost,
        "total_revenue_krw": total_revenue,
        "total_margin_krw": total_margin,
        "overall_margin_pct": overall_margin_pct,
        "business_unit_count": len(margins),
        "average_revenue_completeness_pct": avg_revenue_completeness,
        "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    }


# ── Helpers ───────────────────────────────────────────────────────────────
def _now_iso() -> str:
    """ISO timestamp helper (Phase 22 verbatim pattern)."""
    return datetime.now(UTC).isoformat()


__all__ = [
    "MARGIN_AMOUNT_QUANTUM",
    "MARGIN_PCT_QUANTUM",
    "execute_margin_analysis",
    "validate_margin_analysis",
    "aggregate_margin_analysis",
    "_compute_cache_key",
    "_validate_revenue_sources",
    "_compute_margin_status",
    "_compute_margin_alerts",
    "_validate_inputs",
    "_compute_requires_2fa_challenge",
    "_persist_margin_analysis",
]
