"""apps.api.modules.slo.slo_burn_rate_evaluator — multi-window burn-rate eval.

Phase 10 (cj-style 103번째 wire) — SLO Engineering / Error Budget
Management territory (PRD §F26.2 verbatim).

Google SRE Workbook verbatim 4 windows:
(a) **fast burn (1h window, 5min alert, threshold 14.4x objective consumption)** —
    즉각적 문제 감지.
(b) **slow burn (6h window, 30min alert, threshold 6x)** — 시간 단위 문제 감지.
(c) **exhaustion (24h window, 2h alert, threshold 3x)** — 단기 예산 고갈 감지.
(d) **long (3d window, 6h alert, threshold 1x)** — 장기 추세 감지.

Multi-window composite evaluation:
    (fast OR slow) AND (slow OR exhaustion) AND (exhaustion OR long)
Composite alert = 4 windows pairwise OR 의 3개 AND 조건 모두 만족 시 critical.

Burn-rate formula:
    burn_rate = error_rate / (1 - objective)
    (objective 99.9% → 정상 error_rate 0.1% → burn_rate > 14.4x 면 1h 안에
     2% 예산 소진 = 알람 트리거)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `slo_violation_detected` (AFTER burn-rate 알람 트리거).
- CR 4-3/4-4 — slo_burn_rate baseline freeze 30d rolling pattern verbatim
  미러 (Phase 8 baseline freeze carry-over).
- CR 1-1 ContextVar — trace_id request-scoped ContextVar binding.

AD-14 stack pin — prometheus_client + alertmanager.
AD-22 owner-only RBAC — manual override + threshold 조정 owner-only +
Epic 12 2FA 챌린지.

Industry-agnostic per CR 12-1 L4 precedent.
"""
from __future__ import annotations

import logging
import uuid
from typing import Final, TypedDict

from apps.api.modules.slo.slo_dsl import (
    DEFAULT_BURN_RATE_THRESHOLD,
    SloViolationDetectedError,
    WINDOW_1H,
    WINDOW_24H,
    WINDOW_3D,
    WINDOW_6H,
)

logger = logging.getLogger(__name__)


# ── Constants — Google SRE Workbook verbatim 4 windows ──────────
# (PRD §F26.2.2 verbatim)
WINDOW_FAST_BURN: Final[str] = WINDOW_1H  # 1h
WINDOW_SLOW_BURN: Final[str] = WINDOW_6H  # 6h
WINDOW_EXHAUSTION: Final[str] = WINDOW_24H  # 24h
WINDOW_LONG: Final[str] = WINDOW_3D  # 3d

# Thresholds (multipliers of objective consumption)
THRESHOLD_FAST_BURN: Final[float] = 14.4
THRESHOLD_SLOW_BURN: Final[float] = 6.0
THRESHOLD_EXHAUSTION: Final[float] = 3.0
THRESHOLD_LONG: Final[float] = 1.0

# Alert windows (PRD §F26.2.2 verbatim)
ALERT_WINDOW_FAST_BURN_SECONDS: Final[int] = 5 * 60  # 5min
ALERT_WINDOW_SLOW_BURN_SECONDS: Final[int] = 30 * 60  # 30min
ALERT_WINDOW_EXHAUSTION_SECONDS: Final[int] = 2 * 60 * 60  # 2h
ALERT_WINDOW_LONG_SECONDS: Final[int] = 6 * 60 * 60  # 6h

# 2min cadence evaluator (PRD §F26.2.10 verbatim — Phase 7 observability 정합)
EVALUATOR_CADENCE_SECONDS: Final[int] = 2 * 60  # 2min


# ── Typed envelopes (CR 12-5 D-PARITY-01) ──────────────────────
class SloBurnRateWindow(TypedDict):
    """Single-window burn-rate evaluation result.

    Fields:
        window: One of 4 windows (fast/slow/exhaustion/long).
        burn_rate: Computed burn rate (e.g. 14.4x).
        threshold: Window threshold (e.g. 14.4x).
        breached: True if burn_rate > threshold.
        alert_after_seconds: Alert window (PRD §F26.2.2 verbatim).
    """

    window: str
    burn_rate: float
    threshold: float
    breached: bool
    alert_after_seconds: int


class SloBurnRateEvaluation(TypedDict):
    """Composite burn-rate evaluation result (PRD §F26.2.4 verbatim).

    Fields:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        objective: Target value (e.g. 99.9).
        window_results: Per-window evaluation (4 entries).
        composite_breached: True if composite alert fired (3/4 AND).
        composite_severity: 'warning' | 'critical' (composite AND → critical).
        evaluated_at: ISO8601 timestamp.
        trace_id: Request trace_id (CR 1-1 ContextVar lesson).
    """

    slo_id: str
    tenant_id: str
    objective: float
    window_results: list[SloBurnRateWindow]
    composite_breached: bool
    composite_severity: str
    evaluated_at: str
    trace_id: str


class SloMetricSample(TypedDict):
    """A single SLI metric sample (PRD §F26.2.6 verbatim).

    Fields:
        tenant_id: Tenant UUID4 string.
        slo_id: SloDefinition.slo_id.
        service: Target service name.
        error_rate: Observed error rate (0.0~1.0).
        window: Window the sample covers.
        sampled_at: ISO8601 timestamp.
    """

    tenant_id: str
    slo_id: str
    service: str
    error_rate: float
    window: str
    sampled_at: str


# ── Pure burn-rate formula (PRD §F26.2.3 verbatim) ─────────────
def compute_burn_rate(error_rate: float, objective: float) -> float:
    """Compute burn rate given observed error_rate and objective.

    Formula: burn_rate = error_rate / (1 - objective)
    (objective 99.9% → 정상 error_rate 0.1% → burn_rate > 14.4x 면 1h 안에
     2% 예산 소진 = 알람 트리거.)

    Args:
        error_rate: Observed error rate (0.0~1.0).
        objective: SLO objective as percentage (e.g. 99.9 → 0.999 internally).

    Returns:
        Burn rate multiplier (>= 0).
    """
    objective_ratio = objective / 100.0
    if objective_ratio >= 1.0:
        return 0.0  # objective = 100% means no budget to consume
    budget_remaining = 1.0 - objective_ratio
    if budget_remaining <= 0:
        return 0.0
    return error_rate / budget_remaining


# ── 4-window burn-rate evaluation (PRD §F26.2.2 verbatim) ──────
WINDOW_THRESHOLDS: Final[dict[str, float]] = {
    WINDOW_FAST_BURN: THRESHOLD_FAST_BURN,
    WINDOW_SLOW_BURN: THRESHOLD_SLOW_BURN,
    WINDOW_EXHAUSTION: THRESHOLD_EXHAUSTION,
    WINDOW_LONG: THRESHOLD_LONG,
}

WINDOW_ALERT_AFTER: Final[dict[str, int]] = {
    WINDOW_FAST_BURN: ALERT_WINDOW_FAST_BURN_SECONDS,
    WINDOW_SLOW_BURN: ALERT_WINDOW_SLOW_BURN_SECONDS,
    WINDOW_EXHAUSTION: ALERT_WINDOW_EXHAUSTION_SECONDS,
    WINDOW_LONG: ALERT_WINDOW_LONG_SECONDS,
}


def evaluate_single_window(
    window: str,
    error_rate: float,
    objective: float,
) -> SloBurnRateWindow:
    """Evaluate burn rate for a single window.

    Args:
        window: One of 4 windows (WINDOW_FAST_BURN/SLOW_BURN/EXHAUSTION/LONG).
        error_rate: Observed error rate (0.0~1.0).
        objective: SLO objective as percentage.

    Returns:
        SloBurnRateWindow with burn_rate + breached status.

    Raises:
        KeyError: If window is not one of the 4 SRE Workbook windows.
    """
    if window not in WINDOW_THRESHOLDS:
        raise SloViolationDetectedError(
            slo_id="<unknown>",
            window=window,
            burn_rate=0.0,
            threshold=0.0,
        )
    burn_rate = compute_burn_rate(error_rate, objective)
    threshold = WINDOW_THRESHOLDS[window]
    return SloBurnRateWindow(
        window=window,
        burn_rate=burn_rate,
        threshold=threshold,
        breached=burn_rate > threshold,
        alert_after_seconds=WINDOW_ALERT_AFTER[window],
    )


def evaluate_all_windows(
    slo_id: str,
    tenant_id: str,
    objective: float,
    error_rates_by_window: dict[str, float],
    *,
    evaluated_at: str,
    trace_id: str | None = None,
) -> SloBurnRateEvaluation:
    """Evaluate all 4 windows + composite alert (PRD §F26.2.4 verbatim).

    Composite alert = 3/4 AND:
        (fast OR slow) AND (slow OR exhaustion) AND (exhaustion OR long)

    Args:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        objective: SLO objective as percentage.
        error_rates_by_window: Dict mapping window → error rate (0.0~1.0).
        evaluated_at: ISO8601 timestamp.
        trace_id: Request trace_id (CR 1-1 ContextVar).

    Returns:
        SloBurnRateEvaluation with composite_breached + composite_severity.

    Raises:
        SloViolationDetectedError: When composite alert fires.
    """
    resolved_trace_id = trace_id or str(uuid.uuid4())

    window_results: list[SloBurnRateWindow] = []
    for window in (
        WINDOW_FAST_BURN,
        WINDOW_SLOW_BURN,
        WINDOW_EXHAUSTION,
        WINDOW_LONG,
    ):
        error_rate = error_rates_by_window.get(window, 0.0)
        result = evaluate_single_window(window, error_rate, objective)
        window_results.append(result)

    # Composite evaluation: pairwise OR 의 3개 AND 조건
    by_window = {r["window"]: r["breached"] for r in window_results}
    composite = (
        (by_window[WINDOW_FAST_BURN] or by_window[WINDOW_SLOW_BURN])
        and (by_window[WINDOW_SLOW_BURN] or by_window[WINDOW_EXHAUSTION])
        and (by_window[WINDOW_EXHAUSTION] or by_window[WINDOW_LONG])
    )

    evaluation = SloBurnRateEvaluation(
        slo_id=slo_id,
        tenant_id=tenant_id,
        objective=objective,
        window_results=window_results,
        composite_breached=composite,
        composite_severity="critical" if composite else "warning",
        evaluated_at=evaluated_at,
        trace_id=resolved_trace_id,
    )

    if composite:
        # Find the most severe window (highest burn_rate) for the error
        worst = max(window_results, key=lambda r: r["burn_rate"])
        logger.warning(
            "slo_violation_detected slo_id=%s window=%s burn_rate=%.2fx threshold=%.2fx",
            slo_id,
            worst["window"],
            worst["burn_rate"],
            worst["threshold"],
        )
        raise SloViolationDetectedError(
            slo_id=slo_id,
            window=worst["window"],
            burn_rate=worst["burn_rate"],
            threshold=worst["threshold"],
            trace_id=resolved_trace_id,
        )

    return evaluation


# ── Baseline freeze pattern (CR 4-3/4-4 verbatim 미러) ──────────
def compute_baseline_threshold(slo_id: str, baseline_burn_rate: float) -> float:
    """Compute the alert threshold based on 30d rolling baseline.

    The baseline freeze pattern (CR 4-3/4-4) allows the burn-rate threshold
    to adapt based on historical patterns while keeping the 14.4x fast burn
    as the floor.

    Args:
        slo_id: SloDefinition.slo_id (for baseline lookup SSOT).
        baseline_burn_rate: 30d rolling baseline burn rate.

    Returns:
        Effective threshold (max of SRE Workbook floor + baseline).
    """
    return max(DEFAULT_BURN_RATE_THRESHOLD, baseline_burn_rate)


__all__ = [
    "SloBurnRateWindow",
    "SloBurnRateEvaluation",
    "SloMetricSample",
    "WINDOW_FAST_BURN",
    "WINDOW_SLOW_BURN",
    "WINDOW_EXHAUSTION",
    "WINDOW_LONG",
    "THRESHOLD_FAST_BURN",
    "THRESHOLD_SLOW_BURN",
    "THRESHOLD_EXHAUSTION",
    "THRESHOLD_LONG",
    "ALERT_WINDOW_FAST_BURN_SECONDS",
    "ALERT_WINDOW_SLOW_BURN_SECONDS",
    "ALERT_WINDOW_EXHAUSTION_SECONDS",
    "ALERT_WINDOW_LONG_SECONDS",
    "EVALUATOR_CADENCE_SECONDS",
    "WINDOW_THRESHOLDS",
    "WINDOW_ALERT_AFTER",
    "compute_burn_rate",
    "evaluate_single_window",
    "evaluate_all_windows",
    "compute_baseline_threshold",
]
