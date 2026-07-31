"""packages.services.m0_onboarding.settings_completion — Settings wizard completion logic.

Story 1.2 — Task 2.

Pure-Python, stdlib-only module. NO DB, NO clock, NO random. AD-1 / AD-5
binding: this is the canonical completion-decision function consumed by
the API service layer + the frontend TS mirror (consistency tested in
`tests/integration/test_completion_consistency.py`).

The function answers: "Given the tenant's current onboarding JSONB + the
allocation criterion counts, is the [계산] button enabled?"

Industry-conditional rules (PRD §8.M0(b)):
- manufacturing (①): drivers is NOT required (no ABC engine).
- service (②) + ③ + ④: drivers IS required (ABC engine is wired).
- All industries require direct_indirect + fixed_variable (A11 CCR needs
  account tags regardless of which engine runs).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from packages.services.m0_onboarding.industry_menu import Industry

# Public constants — Korean labels for the disabled-button tooltip. The
# frontend imports these from the TS mirror (`apps/web/lib/settings-completion.ts`).
# Update both sides together; drift is caught by `test_completion_consistency.py`.
LABEL_FISCAL_YEAR_START: Final[str] = "회계연도 시작월"
LABEL_CURRENCY: Final[str] = "통화"
LABEL_LANGUAGE: Final[str] = "언어"
LABEL_DIRECT_INDIRECT: Final[str] = "직접/간접 계정 분류"
LABEL_FIXED_VARIABLE: Final[str] = "고정/변동 분류"
LABEL_DRIVERS: Final[str] = "동인 정의"


@dataclass(frozen=True)
class FieldStatus:
    """Per-field status — one for each canonical onboarding field.

    `count` is set only for `allocation_criteria.*` rows. `missing_reason`
    is set when `completed == False` so the API can return a precise message
    without re-deriving in the handler.
    """

    field: str
    completed: bool
    count: int | None = None
    missing_reason: str | None = None


@dataclass(frozen=True)
class DraftSummary:
    """Story 1.3 — Summary of an input_drafts row for the completion gate.

    The completion function does NOT reach into the DB or read the full
    input_drafts row. The caller (API service layer) projects the
    minimum fields needed to decide whether a draft is review-required:

    - `review_required`: True iff `confidence IS NULL OR confidence < REVIEW_THRESHOLD`.
      The caller computes this once (and so does the UI), so the same boolean
      flows through three layers (DB row → API response → completion gate).
    - `field_name`: The field label shown to the user (e.g. "사업자등록번호").
      Surfaced in the `missing` tooltip so the user knows what to fix.
    - `confidence`: pass-through; useful for tests and debug logs only.

    Why a separate dataclass (not the full Pydantic draft schema):
    - `compute_completion` must remain stdlib-only and pure. Importing the
      full Pydantic draft schema would drag FastAPI / SQLAlchemy into the
      engine layer (AD-1 / AD-5 violation).
    - Tests can construct `DraftSummary` instances directly without spinning
      up a fixture.
    """

    field_name: str
    review_required: bool
    confidence: float | None = None


@dataclass(frozen=True)
class CompletionStatus:
    """Result of `compute_completion()`.

    The frontend drives both the [계산] button enabled state and the tooltip
    copy from this single object.

    Value-bearing fields (F-7): `fiscal_year_start_value`, `currency_value`,
    `industry` carry the **actual** stored values (not just completion bools)
    so the wizard can seed its pickers on first render without a second
    round-trip. All three are optional — a freshly-created tenant has all
    fields null.
    """

    fiscal_year_start: FieldStatus
    currency: FieldStatus
    language: FieldStatus
    direct_indirect: FieldStatus
    fixed_variable: FieldStatus
    drivers: FieldStatus
    drivers_required: bool
    is_complete: bool
    missing: list[str]  # Korean labels, ordered per PRD §8.M0(b) sequence
    # F-7: stored values for first-render seeding (wizard avoids extra GET).
    fiscal_year_start_value: str | None = None
    currency_value: str | None = None
    industry: Industry | None = None
    # Story 1.3 — count of input_drafts rows that are still review-required
    # (confidence < 0.70 or NULL). Surfaced for the [계산] button tooltip
    # ("AI 추출 미확정: N건") so users know what to revisit. Always ≥ 0.
    pending_extractions_count: int = 0


# ── Industry → drivers_required map ────────────────────────────
_DRIVERS_REQUIRED: Final[dict[Industry, bool]] = {
    Industry.MANUFACTURING: False,  # no ABC engine → drivers skipped
    Industry.SERVICE: True,  # ABC engine needs drivers (A11)
    Industry.MANUFACTURING_SERVICE: True,
    Industry.MANUFACTURING_SERVICE_OTHER: True,
}


# ── Public API ────────────────────────────────────────────────
def compute_completion(
    industry: Industry | None,
    tenant_settings: dict | None,
    allocation_counts: dict[str, int] | None,
    pending_extractions: list[DraftSummary] | None = None,
) -> CompletionStatus:
    """Pure completion-decision function.

    Args:
        industry: The tenant's industry (None if M0 hasn't completed yet).
            Drives whether `drivers` is required.
        tenant_settings: The `tenant_settings.onboarding` JSONB. Read-only;
            this function does NOT mutate. None is treated as {}.
        allocation_counts: Per-criterion row counts, e.g.
            `{"direct_indirect": 5, "fixed_variable": 0, "drivers": 0}`.
            Sourced from M1 baseline + M9 ABC tables (Story 1.2 Task 4).
            None is treated as {}.
        pending_extractions: Story 1.3 — list of `DraftSummary` rows for the
            tenant's current `input_drafts` where the user has not yet
            confirmed the AI value. Each row that is `review_required` is
            added to the `missing` list and blocks `is_complete`. None is
            treated as [].

    Returns:
        `CompletionStatus` — the frontend renders the [계산] button state +
        the missing-fields tooltip directly from this object. The
        `pending_extractions_count` field tells the UI how many AI fields
        need revisiting without leaking the field names into the button
        state.

    Anti-pattern guards (spec §Anti-pattern prevention):
    - No DB calls. No clock reads.
    - No side effects. Safe to call from request handlers + tests.
    - The function does NOT decide whether a draft is "review-required"
      (that's the API service's job — keeps this function pure & decoupled
      from `REVIEW_THRESHOLD` knowledge).
    """
    ts = dict(tenant_settings or {})
    counts = dict(allocation_counts or {})
    pending = list(pending_extractions or [])

    # ── Top-level fields ──
    fiscal_year = bool(ts.get("fiscal_year_start"))
    currency = bool(ts.get("currency"))
    language = bool(ts.get("language"))

    fiscal_year_status = FieldStatus(
        field="fiscal_year_start",
        completed=fiscal_year,
        missing_reason=None if fiscal_year else f"{LABEL_FISCAL_YEAR_START} 미입력",
    )
    currency_status = FieldStatus(
        field="currency",
        completed=currency,
        missing_reason=None if currency else f"{LABEL_CURRENCY} 미선택",
    )
    language_status = FieldStatus(
        field="language",
        completed=language,
        missing_reason=None if language else f"{LABEL_LANGUAGE} 미선택",
    )

    # ── Allocation criteria 3종 ──
    di_count = int(counts.get("direct_indirect", 0))
    fv_count = int(counts.get("fixed_variable", 0))
    dr_count = int(counts.get("drivers", 0))

    di_completed = di_count >= 1
    fv_completed = fv_count >= 1
    # drivers requirement is industry-conditional.
    drivers_required = bool(_DRIVERS_REQUIRED.get(industry, True))
    dr_completed = (not drivers_required) or dr_count >= 1

    direct_indirect_status = FieldStatus(
        field="direct_indirect",
        completed=di_completed,
        count=di_count,
        missing_reason=None if di_completed else f"{LABEL_DIRECT_INDIRECT} 0행",
    )
    fixed_variable_status = FieldStatus(
        field="fixed_variable",
        completed=fv_completed,
        count=fv_count,
        missing_reason=None if fv_completed else f"{LABEL_FIXED_VARIABLE} 0행",
    )
    drivers_status = FieldStatus(
        field="drivers",
        completed=dr_completed,
        count=dr_count,
        missing_reason=(
            None
            if dr_completed
            else (
                f"{LABEL_DRIVERS} 0행"
                if drivers_required
                else f"{LABEL_DRIVERS} 미적용 (제조업은 ABC 엔진 없음)"
            )
        ),
    )

    # ── Aggregate completion ──
    all_statuses: list[FieldStatus] = [
        fiscal_year_status,
        currency_status,
        language_status,
        direct_indirect_status,
        fixed_variable_status,
        drivers_status,
    ]
    # Story 1.3: any review-required AI draft blocks [계산] just like an
    # unfilled wizard field. The user must confirm or edit every low-confidence
    # extraction before the [계산] button can flip to enabled.
    pending_required = [d for d in pending if d.review_required]
    pending_required_field_names = [d.field_name for d in pending_required]

    is_complete = all(s.completed for s in all_statuses) and not pending_required

    # ── Missing list — human-readable Korean labels in PRD §8.M0(b) order ──
    missing: list[str] = []
    if not fiscal_year:
        missing.append(LABEL_FISCAL_YEAR_START)
    if not currency:
        missing.append(LABEL_CURRENCY)
    if not language:
        missing.append(LABEL_LANGUAGE)
    if not di_completed:
        missing.append(LABEL_DIRECT_INDIRECT)
    if not fv_completed:
        missing.append(LABEL_FIXED_VARIABLE)
    if not dr_completed and drivers_required:
        missing.append(LABEL_DRIVERS)
    # Story 1.3: AI extractions are appended AFTER wizard fields so the
    # tooltip preserves the §8.M0(b) order at the top. Field names are
    # surfaced verbatim because each tenant's industry-specific extraction
    # set can include custom labels (e.g. "사업자등록번호", "대표자명").
    for fname in pending_required_field_names:
        missing.append(f"AI 추출 미확정: {fname}")

    return CompletionStatus(
        fiscal_year_start=fiscal_year_status,
        currency=currency_status,
        language=language_status,
        direct_indirect=direct_indirect_status,
        fixed_variable=fixed_variable_status,
        drivers=drivers_status,
        drivers_required=drivers_required,
        is_complete=is_complete,
        missing=missing,
        # F-7: surface the actual stored values so the wizard can seed its
        # pickers on first render. `industry` flows from the function arg
        # (not from `tenant_settings.industry`, which may be stale during
        # the industry-change grace window).
        fiscal_year_start_value=(
            ts["fiscal_year_start"] if isinstance(ts.get("fiscal_year_start"), str) else None
        ),
        currency_value=(ts["currency"] if ts.get("currency") in ("KRW", "USD") else None),
        industry=industry,
        # Story 1.3 — count for the tooltip / banner copy.
        pending_extractions_count=len(pending_required),
    )


# ── Field list (for cross-language consistency test) ──────────
CANONICAL_FIELDS: Final[tuple[str, ...]] = (
    "fiscal_year_start",
    "currency",
    "language",
    "direct_indirect",
    "fixed_variable",
    "drivers",
)
