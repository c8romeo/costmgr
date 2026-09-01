"""packages.services.m10_ai.insight_cache_kernel — Story 10.2 pure kernel.

Story 10.2 (cj-style Epic 10 3번째 진입점, cj-style 29번째 epic 연속) —
T1.1 pure kernel for the three-insight cache lookup surface (AD-25 verbatim).

This module is the **stdlib-only, pure-Python** kernel that defines:
- 3 default insight entries (master PRD §12 verbatim):
    * cost_reduction_candidate (원가 절감 후보)
    * anomaly_pattern          (이상 패턴)
    * forecast                 (예측)
- AD-25 cache key 3-tuple: (tenant_id, period_key, calculation_result_hash)
- Discriminator `source_kind` = `auto_analysis` | `ai_reference`
  (Story 10.3 forward-bind, AD-7 verbatim).
- Pure canonical string serialization for cache lookup.

Why a separate kernel (vs. extending extraction_port):
- AD-5 engine purity — no I/O, no clock, no random.
- AD-7 strict invariant — auto_analysis only (10-2 wire 진입 시점).
- AD-15 cross-language parity — TS mirror at `apps/web/lib/ai-insights.ts`
  mirrors this kernel (drift caught by `apps/web/__tests__/lib/ai-insights-parity.test.ts`).
- AD-1 / AD-11 layering — service layer (apps/api/modules/m10_ai/service.py)
  imports this kernel; UI / handlers never reach into raw values.

Anti-pattern guards:
- Do NOT call any I/O (no DB, no network, no clock, no random).
- Do NOT import Pydantic — these are kept at the service layer boundary.
- Do NOT import AI SDK — pure kernel only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Final

# ── Insight kind discriminator (master PRD §12 verbatim) ─────
# Three insight categories per master PRD §12:
#   - cost_reduction_candidate (원가 절감 후보)
#   - anomaly_pattern          (이상 패턴)
#   - forecast                 (예측)  # noqa: ERA001
# Each is a rule-based template that gets materialized on cache miss.
# AD-15 cross-language parity SSOT: TS mirror
# `apps/web/lib/ai-insights.ts` MUST mirror this frozenset.
INSIGHT_KIND_VALUES: Final[frozenset[str]] = frozenset(
    {
        "cost_reduction_candidate",
        "anomaly_pattern",
        "forecast",
    }
)


class InsightKind(str, Enum):
    """Canonical insight_kind discriminator. Mirrors INSIGHT_KIND_VALUES."""

    COST_REDUCTION_CANDIDATE = "cost_reduction_candidate"
    ANOMALY_PATTERN = "anomaly_pattern"
    FORECAST = "forecast"


# ── Source kind discriminator (AD-7 + 10-3 forward-bind) ──────
# Discriminated union discriminator for insight source:
#   - auto_analysis = rule-based template, immediately computed (10-2 wire 진입 시점)
#   - ai_reference  = AI commentary, NOT authoritative (10-3 wire 진입 시점)
# AD-7 strict invariant: 10-2 wire 진입 시점에 all 3 default insights are
# `source_kind='auto_analysis'` ONLY. `ai_reference` 항목 추가는
# Story 10.3 wire 진입 시점에 detailed wire.
SOURCE_KIND_VALUES: Final[frozenset[str]] = frozenset(
    {
        "auto_analysis",
        "ai_reference",
    }
)


#
# Story 10.3 wire note (cj-style Epic 10 4번째 진입점, cj-style 30번째 epic 연속):
# 10-3 wire 진입 시점에 `ai_reference` opinion 은 **별도 surface** 로 진입한다
# (`apps/api/modules/m10_ai/service.py::CommentService` + `ai_insight_comments`
# ORM/alembic 0031). 본 kernel 의 SSOT invariant 는 **그대로 보존**:
#   - `SOURCE_KIND_VALUES` frozenset 2 values (auto_analysis | ai_reference)
#   - `make_default_insights()` 는 `auto_analysis` ONLY 반환 (AD-7 strict invariant)
# F10.2-(a)~(d) verbatim bind 보존 (master PRD §SM-3a counter increment for
# invalid source_kind + auto_analysis modify attempt). 로직 변경 0건.
class SourceKind(str, Enum):
    """Canonical source_kind discriminator. Mirrors SOURCE_KIND_VALUES."""

    AUTO_ANALYSIS = "auto_analysis"
    AI_REFERENCE = "ai_reference"


# ── Typed exception (AD-25 cache key shape 검증) ──────────────
class InsightCacheKeyShapeError(ValueError):
    """Raised when cache key components have invalid shape.

    Maps to HTTP 422 INSIGHT_CACHE_KEY_ERROR envelope via
    `apps/api/main.py` envelope handler (CR 12-5 D-14 verbatim).

    Why ValueError subclass: matches the existing typed-exception
    pattern used in `monthly_extraction_kernel.InvalidMonthlyFieldValueError`.
    """

    def __init__(
        self,
        *,
        component: str,
        value: object,
        reason: str,
    ) -> None:
        self.component = component
        self.value = value
        self.reason = reason
        super().__init__(
            f"InsightCacheKey shape error on {component}: " f"value='{value}' reason={reason}"
        )


# ── Frozen dataclasses (AD-5 engine purity) ───────────────────
@dataclass(frozen=True)
class InsightEntry:
    """One AI insight entry returned by the M10 cache lookup.

    AD-7 strict invariant: 10-2 wire 진입 시점에
    `source_kind == AUTO_ANALYSIS` ONLY. `AI_REFERENCE` 항목 추가는
    Story 10.3 wire 진입 시점에 detailed wire (auto_analysis vs ai_reference
    badge separation).

    `evidence_ref` references the underlying data point (period_key +
    insight_kind + calculation_result_hash) for traceability.
    """

    insight_kind: InsightKind
    question: str
    answer: str
    source_kind: SourceKind
    evidence_ref: str | None
    generated_at: datetime


@dataclass(frozen=True)
class InsightCacheKey:
    """AD-25 verbatim 3-tuple cache key.

    Per AD-25 (ARCHITECTURE-SPINE.md §296-301 + epics.md 10.2 verbatim):
    "M10 cache key is (tenant_id, period_key, calculation_result_hash).
    A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
    one DB notification per channel."

    Per F10.1-(d) verbatim: "channel = 'ai_cache' filter 강제"
    (cross-channel contamination 방지).
    """

    tenant_id: uuid.UUID
    period_key: str
    calculation_result_hash: str


# ── Pure function: compose_insight_cache_key ───────────────────
def compose_insight_cache_key(
    *,
    tenant_id: uuid.UUID,
    period_key: str,
    calculation_result_hash: str,
) -> str:
    """Compose canonical string serialization of AD-25 3-tuple key.

    Format: `f"{tenant_id}|{period_key}|{calculation_result_hash}"`

    Used as a dict-cache lookup key by the service layer
    (`apps/api/modules/m10_ai/service.py:get_or_compute_insights`).

    AD-5 engine purity: no I/O, no clock, no random. Pure function.

    Args:
        tenant_id: Canonical UUID for the tenant (UUID v7).
        period_key: Fiscal period key in YYYY-MM format
            (master PRD §V4 fiscal key format).
        calculation_result_hash: SHA-256 hex digest from
            `fiscal_period_snapshots.calculation_result_hash`
            (Epic 4 calc-hash publisher).

    Returns:
        Canonical string key for dict cache lookup.

    Raises:
        InsightCacheKeyShapeError: any component has invalid shape.
    """
    if not isinstance(tenant_id, uuid.UUID):
        raise InsightCacheKeyShapeError(
            component="tenant_id",
            value=tenant_id,
            reason="tenant_id must be uuid.UUID, got " + type(tenant_id).__name__,
        )

    if not isinstance(period_key, str):
        raise InsightCacheKeyShapeError(
            component="period_key",
            value=period_key,
            reason="period_key must be str, got " + type(period_key).__name__,
        )

    if not period_key:
        raise InsightCacheKeyShapeError(
            component="period_key",
            value=period_key,
            reason="period_key is empty",
        )

    if not isinstance(calculation_result_hash, str):
        raise InsightCacheKeyShapeError(
            component="calculation_result_hash",
            value=calculation_result_hash,
            reason="calculation_result_hash must be str, got "
            + type(calculation_result_hash).__name__,
        )

    if not calculation_result_hash:
        raise InsightCacheKeyShapeError(
            component="calculation_result_hash",
            value=calculation_result_hash,
            reason="calculation_result_hash is empty",
        )

    return f"{tenant_id}|{period_key}|{calculation_result_hash}"


# ── Pure function: make_default_insights ──────────────────────
def make_default_insights(period_key: str) -> tuple[InsightEntry, ...]:
    """Return exactly 3 default rule-based insights for cache miss.

    AD-7 strict invariant: ALL 3 entries are `source_kind=AUTO_ANALYSIS`.
    `source_kind=AI_REFERENCE` 항목 추가는 Story 10.3 wire 진입 시점에
    detailed wire (10-3 badge separation forward-bind).

    Deterministic — same `period_key` always yields the same tuple of
    InsightEntry objects (AD-5 engine purity + V8 byte-identical determinism).

    Args:
        period_key: Fiscal period key in YYYY-MM format. Embedded into
            each entry's question + answer for traceability.

    Returns:
        Tuple of exactly 3 InsightEntry objects in stable order:
        (cost_reduction_candidate, anomaly_pattern, forecast).
    """
    base_generated_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=None)
    return (
        InsightEntry(
            insight_kind=InsightKind.COST_REDUCTION_CANDIDATE,
            question=f"{period_key} 원가 절감 후보 항목",
            answer=f"{period_key} 마감 데이터 기반 원가 절감 후보 분석 결과",
            source_kind=SourceKind.AUTO_ANALYSIS,
            evidence_ref=f"period={period_key}|kind=cost_reduction_candidate",
            generated_at=base_generated_at,
        ),
        InsightEntry(
            insight_kind=InsightKind.ANOMALY_PATTERN,
            question=f"{period_key} 이상 패턴 항목",
            answer=f"{period_key} 마감 데이터 기반 이상 패턴 분석 결과",
            source_kind=SourceKind.AUTO_ANALYSIS,
            evidence_ref=f"period={period_key}|kind=anomaly_pattern",
            generated_at=base_generated_at,
        ),
        InsightEntry(
            insight_kind=InsightKind.FORECAST,
            question=f"{period_key} 예측 항목",
            answer=f"{period_key} 마감 데이터 기반 예측 분석 결과",
            source_kind=SourceKind.AUTO_ANALYSIS,
            evidence_ref=f"period={period_key}|kind=forecast",
            generated_at=base_generated_at,
        ),
    )


__all__: Final[tuple[str, ...]] = (
    "INSIGHT_KIND_VALUES",
    "SOURCE_KIND_VALUES",
    "InsightKind",
    "SourceKind",
    "InsightCacheKeyShapeError",
    "InsightEntry",
    "InsightCacheKey",
    "compose_insight_cache_key",
    "make_default_insights",
)
