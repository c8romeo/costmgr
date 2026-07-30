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


# ── Industry → drivers_required map ────────────────────────────
_DRIVERS_REQUIRED: Final[dict[Industry, bool]] = {
    Industry.MANUFACTURING: False,  # no ABC engine → drivers skipped
    Industry.SERVICE: True,          # ABC engine needs drivers (A11)
    Industry.MANUFACTURING_SERVICE: True,
    Industry.MANUFACTURING_SERVICE_OTHER: True,
}


# ── Public API ────────────────────────────────────────────────
def compute_completion(
    industry: Industry | None,
    tenant_settings: dict | None,
    allocation_counts: dict[str, int] | None,
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

    Returns:
        `CompletionStatus` — the frontend renders the [계산] button state +
        the missing-fields tooltip directly from this object.

    Anti-pattern guards (spec §Anti-pattern prevention):
    - No DB calls. No clock reads.
    - No side effects. Safe to call from request handlers + tests.
    """
    ts = dict(tenant_settings or {})
    counts = dict(allocation_counts or {})

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
    is_complete = all(s.completed for s in all_statuses)

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
        currency_value=(
            ts["currency"] if ts.get("currency") in ("KRW", "USD") else None
        ),
        industry=industry,
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