"""packages.cost_engine.budget_variance — Story 8.2 Budget Variance pure kernel.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m8_budget/services/budget_variance_service.py`
  (T3 service layer — fetch_variance_table / compute_variance_total)

AD-1 / AD-5 / AD-8 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes actual data
fetched from DB; this kernel owns the variance math + threshold severity
+ V8 determinism + ABCD gray badge placeholder.

PRD §F8.2 (예산-실적 대조 시 모든 차이 행 + A×B×C×D 미구현 회색 배지):
- Severity thresholds: `abs(variance_pct) < 5%` normal / `5% <= < 10%` warning
  / `>= 10%` critical
- 부호(sign) 보존: 음수 variance = 절감(`actual < budget`), 양수 = 초과(`actual > budget`)
- A×B×C×D 회색 배지 placeholder (PRD §15 NON-GOAL #1)

V8 determinism: `compute_variance_hash` 는 hashlib.sha256 결정론 digest
— 동일 입력 → byte-identical hash (Epic 4 baseline + 7-1/7-2/8-1 패턴).

A19 cohesion pattern 4번째 검증: `budget_variance.py` 는
`packages/cost_engine/cvp.py` (7-1) + `packages/cost_engine/projection.py`
(7-2) + `packages/cost_engine/budget_period_key.py` (8-1) 와 surface 분리
— concern 별도 (variance compute + threshold severity 는 budget concern).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, Literal

# ── Constants ────────────────────────────────────────────────
# PRD §F8.2 verbatim severity thresholds (3-tier).
SEVERITY_THRESHOLD_WARNING_PCT: Final[Decimal] = Decimal("5")
SEVERITY_THRESHOLD_CRITICAL_PCT: Final[Decimal] = Decimal("10")

# Decimal precision for variance_pct (PRD §F8.2 + AD-8 monetary).
# 4 decimal places + ROUND_HALF_EVEN (banker's rounding) parity with TS decimal.js.
VARIANCE_PCT_QUANTUM: Final[Decimal] = Decimal("0.0001")

# Severity values (PRD §F8.2 + epics.md Story 8.2 AC).
Severity = Literal["normal", "warning", "critical"]

# Color values (frontend mapping — PRD §F8.2 + AC #4 verbatim).
Color = Literal["gray", "yellow", "red"]

# Hash prefix for compute_variance_hash (V8 determinism trace).
VARIANCE_HASH_PREFIX: Final[str] = "sha256:"

# A×B×C×D gray badge placeholder (PRD §15 NON-GOAL #1 + §10 M8 (b) verbatim).
ABCD_DISABLED_LABEL: Final[str] = "A×B×C×D 원가 차이 분석"
ABCD_DISABLED_TOOLTIP: Final[str] = (
    "2차 예정 — A×B×C×D 편성 엔진 미구현 (PRD §15 NON-GOAL #1)"
)
ABCD_DISABLED_NOTE: Final[str] = "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]"

# ABCD badge variant (variance / trend / sensitivity — 8-3 retrofit foundation).
ABCDVariant = Literal["variance", "trend", "sensitivity"]


# ── Frozen dataclasses ───────────────────────────────────────
@dataclass(frozen=True, slots=True)
class Variance:
    """Frozen budget variance entity (PRD §F8.2 + AD-8 monetary).

    `budget_value` = Decimal (>= 0)
    `actual_value` = Decimal (>= 0)
    `difference` = actual_value - budget_value
        (sign-preserved: 음수=절감, 양수=초과)
    `variance_pct` = (difference / budget_value) * 100,
        ROUND_HALF_EVEN 4 decimal places (banker's rounding, AD-8).
    `severity` = "normal" | "warning" | "critical" per ±5%/±10% thresholds.
    """

    budget_value: Decimal
    actual_value: Decimal
    difference: Decimal
    variance_pct: Decimal
    severity: Severity


@dataclass(frozen=True, slots=True)
class VarianceRow:
    """Frozen variance row entity (frontend row mapping).

    `label` = 항목명 (예: "직접재료", "직접노무", "제조경비", "합계")
    `variance` = Variance (4 fields)
    `color` = "gray" | "yellow" | "red" (severity → color mapping)
    """

    label: str
    variance: Variance
    color: Color


@dataclass(frozen=True, slots=True)
class ABCDDisabledBadge:
    """A×B×C×D 회색 배지 placeholder (PRD §15 NON-GOAL #1 + §10 M8 (b) verbatim).

    Story 8.2에서 disabled placeholder 명시, 8-3 follow-up에서 retrofit 가능.
    """

    variant: ABCDVariant
    label: str
    tooltip: str
    disabled: bool


# ── Pure functions ───────────────────────────────────────────
def compute_variance(*, budget_value: Decimal, actual_value: Decimal) -> Variance:
    """PRD §F8.2 verbatim variance compute.

    공식: `difference = actual_value - budget_value` (sign-preserved)
          `variance_pct = (difference / budget_value) * 100`
          (ROUND_HALF_EVEN 4 decimal places, AD-8)

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-8 + AD-11).

    Edge cases (ValueError raise):
      - `budget_value < 0` → "budget_value must be non-negative"
      - `actual_value < 0` → "actual_value must be non-negative"

    Edge cases (severity):
      - `budget_value == 0 AND actual_value == 0` → `variance_pct = 0`
        + `severity = "normal"`
      - `budget_value == 0 AND actual_value > 0` → `variance_pct = +Infinity`
        + `severity = "critical"` (infinite variance)
      - `budget_value > 0 AND actual_value == 0` → `variance_pct = -100`
        (100% 절감) + `severity = "critical"` (abs 100 >= 10)

    V8 determinism: 100회 동일 입력 → 100회 byte-identical 결과.
    """
    if not isinstance(budget_value, Decimal):
        raise ValueError(
            f"budget_value must be Decimal, got {type(budget_value).__name__}"
        )
    if not isinstance(actual_value, Decimal):
        raise ValueError(
            f"actual_value must be Decimal, got {type(actual_value).__name__}"
        )
    if budget_value < 0:
        raise ValueError("budget_value must be non-negative")
    if actual_value < 0:
        raise ValueError("actual_value must be non-negative")

    # Difference = actual - budget (sign-preserved: 음수=절감, 양수=초과)
    difference = actual_value - budget_value

    # Variance percentage
    if budget_value == 0:
        # 0/0 → no variance, budget=0 AND actual>0 → +Infinity (excess)
        # actual<0 is already rejected above, so this is +Infinity only.
        variance_pct = (
            Decimal("0") if actual_value == 0 else Decimal("Infinity")
        )
    else:
        # ROUND_HALF_EVEN 4 decimal places (PRD §F8.2 verbatim).
        variance_pct = (difference / budget_value * 100).quantize(
            VARIANCE_PCT_QUANTUM, rounding=ROUND_HALF_EVEN
        )

    # Severity per ±5%/±10% thresholds (infinite variance = critical)
    if variance_pct.is_infinite() or variance_pct.is_nan():
        severity: Severity = "critical"
    elif abs(variance_pct) < SEVERITY_THRESHOLD_WARNING_PCT:
        severity = "normal"
    elif abs(variance_pct) < SEVERITY_THRESHOLD_CRITICAL_PCT:
        severity = "warning"
    else:
        severity = "critical"

    return Variance(
        budget_value=budget_value,
        actual_value=actual_value,
        difference=difference,
        variance_pct=variance_pct,
        severity=severity,
    )


def compute_variance_color(*, variance_pct: Decimal) -> Color:
    """PRD §F8.2 verbatim severity → color mapping.

    `abs(variance_pct) < 5` → "gray" (normal)
    `5 <= abs(variance_pct) < 10` → "yellow" (warning)
    `abs(variance_pct) >= 10` → "red" (critical)
    `variance_pct.is_nan() or variance_pct.is_infinite()` → "gray"
        (default fallback per AC #1)

    Pure-Python, stdlib-only (AD-5 + AD-11).
    """
    if not isinstance(variance_pct, Decimal):
        raise ValueError(
            f"variance_pct must be Decimal, got {type(variance_pct).__name__}"
        )
    # Infinity/NaN → "gray" fallback (cannot compute color for infinite variance)
    if variance_pct.is_nan() or variance_pct.is_infinite():
        return "gray"
    if abs(variance_pct) < SEVERITY_THRESHOLD_WARNING_PCT:
        return "gray"
    if abs(variance_pct) < SEVERITY_THRESHOLD_CRITICAL_PCT:
        return "yellow"
    return "red"


def compute_variance_hash(*, variance: Variance) -> str:
    """V8 determinism hash for variance (Epic 4 baseline + 7-1/7-2/8-1 pattern).

    `hashlib.sha256(repr(variance).encode()).hexdigest()` — 16바이트 hexdigest
    (32 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: `Variance` is `frozen=True, slots=True` — repr은 결정론
    (dataclass auto-generated repr + Decimal repr with full precision).

    Returns:
      `f"sha256:{64-char-hexdigest}"`.
    """
    if not isinstance(variance, Variance):
        raise ValueError(
            f"variance must be Variance, got {type(variance).__name__}"
        )
    digest = hashlib.sha256(repr(variance).encode()).hexdigest()
    return f"{VARIANCE_HASH_PREFIX}{digest}"


def compute_abcd_disabled_badge(
    *, variant: ABCDVariant = "variance"
) -> ABCDDisabledBadge:
    """PRD §15 NON-GOAL #1 + §10 M8 (b) verbatim A×B×C×D 회색 배지 placeholder.

    1차 MVP = placeholder 명시 (회색 배경 + "2차 예정" + disabled).
    2차 retrofit 시 engine_type placeholder = "abcd_disabled" foundation.

    Pure-Python, stdlib-only (AD-5 + AD-11).

    Args:
      variant: "variance" | "trend" | "sensitivity" (Story 8.3 retrofit
        foundation).

    Returns:
      ABCDDisabledBadge (frozen dataclass with label + tooltip + disabled=True).
    """
    if variant not in ("variance", "trend", "sensitivity"):
        raise ValueError(
            f"variant must be one of 'variance'/'trend'/'sensitivity', "
            f"got {variant!r}"
        )
    return ABCDDisabledBadge(
        variant=variant,
        label=ABCD_DISABLED_LABEL,
        tooltip=ABCD_DISABLED_TOOLTIP,
        disabled=True,
    )
