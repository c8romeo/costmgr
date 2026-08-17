"""packages.services.m10_ai.monthly_extraction_kernel — Story 10.1 pure kernel.

Story 10.1 (cj-style Epic 10 2번째 진입점, cj-style 26번째 epic 연속) —
T1.2 pure kernel for monthly input AI extraction.

This module is the **stdlib-only, pure-Python** kernel that processes AI
extracted values for the 6 monthly input fields (master PRD §3.1 6-stream):
- direct_material_cost (직접재료비)
- direct_labor_cost (직접노무비)
- manufacturing_overhead (제조간접비)
- selling_admin_cost (판매관리비)
- revenue (매출)
- inventory_closing (기말재고)

Why a separate kernel (vs. extending onboarding extraction):
- AD-5 engine purity — no I/O, no clock, no random; pure functions only.
- AD-7 strict invariant — AI output → input_drafts only (target_table='monthly_inputs').
- AD-15 cross-language parity — TS mirror at `apps/web/lib/ai-extract.ts`
  mirrors this kernel (drift caught by `apps/web/__tests__/lib/ai-extract-parity.test.ts`).
- AD-1 / AD-11 layering — service layer (apps/api/modules/m10_ai/service.py)
  imports this kernel; UI / handlers never reach into raw values.

Confidence scoring:
- master PRD §8.1 M0-c 70% threshold: `extraction_confidence < 0.70` → RED badge
  + 사용자 확정 강제.
- 0.70 ≤ confidence < 0.90 → YELLOW badge + 사용자 확정 권장.
- confidence >= 0.90 → GREEN badge + 사용자 확정 선택적.

Anti-pattern guards:
- Do NOT call any I/O (no DB, no network, no clock, no random).
- Do NOT import AI SDK or Pydantic — these are kept at the service layer boundary.
- Do NOT bake provider-specific keys into this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Final, Literal

from packages.services.m10_ai.extraction_port import (
    ExtractionEvidence,
    MonthlyFieldName,
)

# ── Confidence thresholds (master PRD §8.1 M0-c verbatim) ────
CONFIDENCE_RED_THRESHOLD: Final[Decimal] = Decimal("0.70")
CONFIDENCE_YELLOW_THRESHOLD: Final[Decimal] = Decimal("0.90")

# Korean thousand-separator: e.g. "1,234,567" → "1234567"
_KO_THOUSAND_SEPARATOR: Final[str] = ","

# Pattern: optional minus + digits + optional comma groups + optional decimal
_KO_NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^-?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^-?\d+(?:\.\d+)?$"
)


# ── Typed exception (master PRD §A11 "시스템은 틀리지 않는다") ──
class InvalidMonthlyFieldValueError(ValueError):
    """Raised when raw_value cannot be parsed into a Decimal.

    Maps to HTTP 422 INVALID_MONTHLY_FIELD_VALUE envelope via
    `apps/api/main.py` envelope handler (CR 12-5 D-14 verbatim).
    """

    def __init__(
        self,
        *,
        field_name: MonthlyFieldName,
        raw_value: str,
        reason: str,
    ) -> None:
        self.field_name = field_name
        self.raw_value = raw_value
        self.reason = reason
        super().__init__(
            f"Invalid monthly field value for {field_name.value}: "
            f"raw_value='{raw_value}' reason={reason}"
        )


# ── Frozen dataclasses (AD-5 engine purity) ──────────────────
@dataclass(frozen=True)
class MonthlyInputDraftRow:
    """One AI-extracted monthly input draft row (AD-7 verbatim).

    Persisted to `input_drafts` table with `target_table='monthly_inputs'`
    and `state='draft'` (AC #1, master PRD §3.1 6-stream).

    `confidence` is the model's self-rated heuristic in [0, 1]. The
    service layer (apps/api/modules/m10_ai/service.py) maps:
    - confidence < 0.70 → RED badge + 사용자 확정 강제
    - 0.70 ≤ confidence < 0.90 → YELLOW badge + 권장
    - confidence >= 0.90 → GREEN badge + 선택적
    """

    field_name: MonthlyFieldName
    value: Decimal
    confidence: Decimal  # 0.000..1.000; master PRD §8.1 M0-c 70% threshold
    evidence: ExtractionEvidence | None
    target_table: Literal["monthly_inputs"] = "monthly_inputs"


# ── Pure function: normalize_monthly_field_value ─────────────
def normalize_monthly_field_value(
    *, field_name: MonthlyFieldName, raw_value: str
) -> Decimal:
    """Parse raw_value string into Decimal, stripping ko-KR comma separator.

    Accepts forms like "1,234,567" / "1234567" / "1234.56" / "-500".
    Raises InvalidMonthlyFieldValueError on parse failure.

    AD-5 engine purity: no I/O, no clock, no random. Pure function.

    Args:
        field_name: Canonical MonthlyFieldName for error context.
        raw_value: Raw extracted string (e.g. AI provider output).

    Returns:
        Decimal value parsed from raw_value (negative allowed for expense refunds).

    Raises:
        InvalidMonthlyFieldValueError: raw_value doesn't match ko-KR number format.
    """
    if not isinstance(raw_value, str):
        raise InvalidMonthlyFieldValueError(
            field_name=field_name,
            raw_value=str(raw_value),
            reason="raw_value must be str, got " + type(raw_value).__name__,
        )

    stripped = raw_value.strip()
    if not stripped:
        raise InvalidMonthlyFieldValueError(
            field_name=field_name,
            raw_value=raw_value,
            reason="raw_value is empty after strip",
        )

    if not _KO_NUMBER_PATTERN.match(stripped):
        raise InvalidMonthlyFieldValueError(
            field_name=field_name,
            raw_value=raw_value,
            reason="raw_value does not match ko-KR number pattern",
        )

    normalized = stripped.replace(_KO_THOUSAND_SEPARATOR, "")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise InvalidMonthlyFieldValueError(
            field_name=field_name,
            raw_value=raw_value,
            reason=f"Decimal conversion failed: {exc}",
        ) from exc


# ── Pure function: compute_extraction_confidence ────────────
def compute_extraction_confidence(
    *,
    field_name: MonthlyFieldName,
    raw_value: str,
    evidence: ExtractionEvidence | None,
) -> Decimal:
    """Compute extraction confidence in [0.000, 1.000].

    Heuristic scoring (master PRD §8.1 M0-c 70% threshold 정합):
    - Base 0.50 (neutral)
    - + 0.20 if raw_value matches ko-KR number pattern (well-formed)
    - + 0.15 if evidence is not None (extracted from document, not hallucinated)
    - + 0.10 if raw_value length <= 20 chars (typical monthly input range)
    - + 0.05 if raw_value has decimal part (more precise)

    Clamped to [0.000, 1.000].

    AD-5 engine purity: no I/O, no clock, no random.

    Args:
        field_name: Canonical MonthlyFieldName for evidence correlation.
        raw_value: Raw extracted string.
        evidence: ExtractionEvidence (None = model hallucinated without source).

    Returns:
        Decimal confidence in [0.000, 1.000].
    """
    score = Decimal("0.50")

    # +0.20 if well-formed ko-KR number
    try:
        normalize_monthly_field_value(field_name=field_name, raw_value=raw_value)
        score += Decimal("0.20")
    except InvalidMonthlyFieldValueError:
        pass  # unparseable; no bonus

    # +0.15 if evidence exists
    if evidence is not None and evidence.text:
        score += Decimal("0.15")

    # +0.10 if raw_value length <= 20
    if len(raw_value.strip()) <= 20:
        score += Decimal("0.10")

    # +0.05 if has decimal part (more precise)
    if "." in raw_value:
        score += Decimal("0.05")

    # Clamp to [0.000, 1.000]
    if score < Decimal("0.000"):
        score = Decimal("0.000")
    elif score > Decimal("1.000"):
        score = Decimal("1.000")

    return score


__all__: Final[tuple[str, ...]] = (
    "CONFIDENCE_RED_THRESHOLD",
    "CONFIDENCE_YELLOW_THRESHOLD",
    "InvalidMonthlyFieldValueError",
    "MonthlyInputDraftRow",
    "normalize_monthly_field_value",
    "compute_extraction_confidence",
)