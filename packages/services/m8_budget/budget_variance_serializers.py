"""packages.services.m8_budget.budget_variance_serializers — Story 8.2 thin JSON serializers.

Pure-Python JSON-safe serializers for `Variance` + `VarianceRow` +
`ABCDDisabledBadge` frozen dataclasses. Decimal-as-string (AD-8 monetary
precision parity) + UTF-8 Korean SSOT labels (NFR18 ko-KR MVP lock).

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m8_budget.budget_variance_serializers`
registered in `tests/architecture/test_api_calls_only_ports.py` (T7 wire).
"""

from __future__ import annotations

from packages.cost_engine.budget_variance import (
    ABCDDisabledBadge,
    VarianceRow,
)


def serialize_variance_row(row: VarianceRow) -> dict[str, object]:
    """Serialize `VarianceRow` → JSON-safe dict (PRD §F8.2 + AD-15).

    AD-15 §1 cross-language parity with TS mirror
    `apps/web/lib/m8-budget-variance.ts:serializeVarianceRowTS`.

    JSON-safe format:
      - Decimal → str (AD-8 monetary precision)
      - Color → str (Literal "gray" | "yellow" | "red")
      - Severity → str (Literal "normal" | "warning" | "critical")
    """
    return {
        "label": str(row.label),
        "budget_value": str(row.variance.budget_value),
        "actual_value": str(row.variance.actual_value),
        "difference": str(row.variance.difference),
        "variance_pct": str(row.variance.variance_pct),
        "severity": str(row.variance.severity),
        "color": str(row.color),
    }


def serialize_variance_total(row: VarianceRow) -> dict[str, object]:
    """Serialize 합계 row → JSON-safe dict (PRD §F8.2 + AD-15).

    `label="합계"` 합계 행 (테이블 하단, totalRow) 직렬화.
    is_total=true 명시적으로 frontend에 통지.
    """
    payload = serialize_variance_row(row)
    payload["is_total"] = True
    return payload


def serialize_abcd_disabled_badge(badge: ABCDDisabledBadge) -> dict[str, object]:
    """Serialize A×B×C×D 회색 배지 placeholder → JSON-safe dict.

    PRD §15 NON-GOAL #1 + §10 M8 (b) verbatim.
    1차 MVP = disabled placeholder 명시 (회색 배경 + "2차 예정" + disabled).
    """
    return {
        "variant": str(badge.variant),
        "label": str(badge.label),
        "tooltip": str(badge.tooltip),
        "disabled": bool(badge.disabled),
    }


__all__ = [
    "serialize_variance_row",
    "serialize_variance_total",
    "serialize_abcd_disabled_badge",
]
