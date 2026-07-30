"""apps.api.core.jsonb_schemas — JSONB validation helpers (Story 1.2).

The `tenant_settings.onboarding` aggregate is a flexible JSONB namespace, but
each module writes only its own keys (AD-23). This module provides:

- `OnboardingField` — enum of the canonical field names written under
  `tenant_settings.onboarding.*` by the M0 onboarding wizard.
- `OnboardingSchemaError` — typed exception (mapped to 400 JSONB_SCHEMA_VIOLATION).
- `validate_onboarding_schema(jsonb, *, partial=True)` — best-effort schema
  check that returns a list of errors without mutating the JSONB. The check
  is partial by default — Story 1.2 only verifies the fields that are wired
  so far (industry / fiscal_year_start / currency / language /
  allocation_criteria).

Canonical schema lives at `docs/onboarding-schema.md`.

Per AD-23: validation is namespace-scoped (this module covers the
`onboarding.*` namespace only; future modules add their own helpers).
Per AD-15: snake_case field names throughout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

from packages.services.m0_onboarding.industry_menu import Industry


class OnboardingField(str, Enum):
    """Canonical field names under `tenant_settings.onboarding.*`.

    Used as `field` argument to `SettingsService.update_onboarding_field()`
    so the dispatch stays statically type-checked.
    """

    INDUSTRY = "industry"
    FISCAL_YEAR_START = "fiscal_year_start"
    CURRENCY = "currency"
    LANGUAGE = "language"
    ALLOCATION_CRITERIA = "allocation_criteria"


# A1 — fiscal year start is stored as `YYYY-MM` (AD-24 typed period keys).
_FISCAL_YEAR_RE: Final[re.Pattern[str]] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# A6 — currency must be one of the AD-8 monetary types. MVP supports KRW + USD.
_SUPPORTED_CURRENCIES: Final[frozenset[str]] = frozenset({"KRW", "USD"})

# NFR-18 — MVP language is ko-KR only (ux-locked-decisions §4).
_SUPPORTED_LANGUAGES: Final[frozenset[str]] = frozenset({"ko-KR"})

# Allocation criteria 3종 (PRD §8.M0(b)).
_ALLOCATION_CRITERION_KEYS: Final[frozenset[str]] = frozenset(
    {"direct_indirect", "fixed_variable", "drivers"}
)


@dataclass(frozen=True)
class OnboardingSchemaError:
    """A single schema-violation finding.

    Returned in `details` of the 400 JSONB_SCHEMA_VIOLATION response so the
    frontend can highlight the offending field.
    """

    field: str
    reason: str
    value: Any = None


class OnboardingValidationError(Exception):
    """Raised when `tenant_settings.onboarding` violates the canonical schema.

    The handler maps this to HTTP 400 with `{code, message_ko, details, trace_id}`
    per AD-15 contract.
    """

    def __init__(
        self,
        *,
        errors: list[OnboardingSchemaError],
        trace_id: str,
    ) -> None:
        super().__init__(f"onboarding schema violation: {len(errors)} error(s)")
        self.errors = errors
        self.trace_id = trace_id


# ── Per-field validators ──────────────────────────────────────
def _validate_industry(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if value is None:
        return errors  # industry is optional until first selection
    if not isinstance(value, str):
        errors.append(
            OnboardingSchemaError(
                field="industry",
                reason="must be a string",
                value=value,
            )
        )
        return errors
    try:
        Industry(value)
    except ValueError:
        errors.append(
            OnboardingSchemaError(
                field="industry",
                reason=f"unknown industry value: {value!r}",
                value=value,
            )
        )
    return errors


def _validate_fiscal_year_start(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if value is None:
        return errors  # field is optional until saved
    if not isinstance(value, str) or not _FISCAL_YEAR_RE.match(value):
        errors.append(
            OnboardingSchemaError(
                field="fiscal_year_start",
                reason="must match YYYY-MM with month 01-12 (A1 / AD-24)",
                value=value,
            )
        )
    return errors


def _validate_currency(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if value is None:
        return errors
    if not isinstance(value, str) or value not in _SUPPORTED_CURRENCIES:
        errors.append(
            OnboardingSchemaError(
                field="currency",
                reason=f"must be one of {sorted(_SUPPORTED_CURRENCIES)} (AD-8)",
                value=value,
            )
        )
    return errors


def _validate_language(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if value is None:
        return errors
    if not isinstance(value, str) or value not in _SUPPORTED_LANGUAGES:
        errors.append(
            OnboardingSchemaError(
                field="language",
                reason=f"must be one of {sorted(_SUPPORTED_LANGUAGES)} (NFR-18)",
                value=value,
            )
        )
    return errors


def _validate_allocation_criteria(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if value is None:
        return errors
    if not isinstance(value, dict):
        errors.append(
            OnboardingSchemaError(
                field="allocation_criteria",
                reason="must be an object",
                value=value,
            )
        )
        return errors
    for key in value:
        if key not in _ALLOCATION_CRITERION_KEYS:
            errors.append(
                OnboardingSchemaError(
                    field=f"allocation_criteria.{key}",
                    reason=(
                        f"unknown criterion (must be one of "
                        f"{sorted(_ALLOCATION_CRITERION_KEYS)})"
                    ),
                    value=key,
                )
            )
            continue
        criterion = value[key]
        if not isinstance(criterion, dict):
            errors.append(
                OnboardingSchemaError(
                    field=f"allocation_criteria.{key}",
                    reason="must be an object with {completed, count, last_updated}",
                    value=criterion,
                )
            )
            continue
        if "completed" in criterion and not isinstance(criterion["completed"], bool):
            errors.append(
                OnboardingSchemaError(
                    field=f"allocation_criteria.{key}.completed",
                    reason="must be boolean",
                    value=criterion.get("completed"),
                )
            )
        if "count" in criterion and not isinstance(criterion["count"], int):
            errors.append(
                OnboardingSchemaError(
                    field=f"allocation_criteria.{key}.count",
                    reason="must be integer ≥ 1",
                    value=criterion.get("count"),
                )
            )
    return errors


# ── Public API ────────────────────────────────────────────────
def validate_onboarding_schema(
    jsonb: dict[str, Any] | None,
    *,
    partial: bool = True,
) -> list[OnboardingSchemaError]:
    """Validate `tenant_settings.onboarding` against the canonical schema.

    Args:
        jsonb: The current onboarding JSONB (None is treated as {}).
        partial: When True (default), only fields that are present are
            validated. When False, every canonical field is required —
            used by tests that want to assert a "fully populated" row.

    Returns:
        List of `OnboardingSchemaError` (empty if clean). Does NOT raise.

    Raises:
        OnboardingValidationError: Only via `enforce_onboarding_schema()` —
            this pure function returns errors instead.
    """
    jsonb = jsonb or {}
    errors: list[OnboardingSchemaError] = []

    # Always-validated fields (industry is checked because it's read by Story 1.1).
    errors.extend(_validate_industry(jsonb.get("industry")))

    # Wizard-only fields are validated when present OR when partial=False.
    if not partial or "fiscal_year_start" in jsonb:
        errors.extend(_validate_fiscal_year_start(jsonb.get("fiscal_year_start")))
    if not partial or "currency" in jsonb:
        errors.extend(_validate_currency(jsonb.get("currency")))
    if not partial or "language" in jsonb:
        errors.extend(_validate_language(jsonb.get("language")))
    if not partial or "allocation_criteria" in jsonb:
        errors.extend(_validate_allocation_criteria(jsonb.get("allocation_criteria")))

    return errors


def enforce_onboarding_schema(
    jsonb: dict[str, Any] | None,
    *,
    trace_id: str,
    partial: bool = True,
) -> None:
    """Raise `OnboardingValidationError` if the schema check fails.

    Convenience wrapper for service-layer writes that should hard-fail when
    the persisted state is corrupt (the GET path also uses this defensively).
    """
    errors = validate_onboarding_schema(jsonb, partial=partial)
    if errors:
        raise OnboardingValidationError(errors=errors, trace_id=trace_id)