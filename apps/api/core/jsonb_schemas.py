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
import uuid
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
    # Story 1.3 — AC #3.4 / Option C resolution. AI-confirmed company-identity
    # fields (사업자등록번호, 회사명, etc.) flow into this JSONB subkey inside
    # the `onboarding` namespace. AD-23 4-namespace rule preserved — this is
    # a subkey, not a 5th top-level key.
    COMPANY_SUBBLOCK = "company_subblock"


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

# ── Story 1.3 — `company_subblock` schema (AC #3.4 Option C) ──
# AD-23: this is a SUBKEY inside the existing `onboarding` namespace, not a
# 5th top-level key. AI-confirmed company-identity fields land here. The
# canonical industry lives at `tenant_settings.onboarding.industry` (Story 1.1);
# `industry_hint` here is for display + downstream matching only.

# Korean business registration number: \d{3}-\d{2}-\d{5}
_BUSINESS_NUMBER_RE: Final[re.Pattern[str]] = re.compile(r"^\d{3}-\d{2}-\d{5}$")

# Length bounds — defensive caps. Real-world Korean company names rarely
# exceed 50 chars; 200 is generous. Address uses the legal address field
# which can be long (multi-line). Representative name: 100 is generous.
_COMPANY_NAME_MAX: Final[int] = 200
_ADDRESS_MAX: Final[int] = 500
_REP_NAME_MAX: Final[int] = 100

# ISO-8601 UTC: matches `2026-07-31T08:00:00Z` and `2026-07-31T08:00:00+00:00`.
# Permissive regex — strict RFC 3339 parsing is the service layer's job.
_ISO_8601_RE: Final[re.Pattern[str]] = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$"
)

# Canonical subkey set — anything else is flagged (catches typos).
_COMPANY_SUBBLOCK_KEYS: Final[frozenset[str]] = frozenset(
    {
        "business_registration_number",
        "company_name",
        "address",
        "representative_name",
        "industry_hint",
        "confirmed_at",
        "confirmed_by",
        "source_draft_ids",
    }
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
# ── Story 1.3 — company_subblock validators ────────────────
def _validate_business_registration_number(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, str) or not _BUSINESS_NUMBER_RE.match(value):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.business_registration_number",
                reason="must match pattern \\d{3}-\\d{2}-\\d{5} (KR business number)",
                value=value,
            )
        )
    return errors


def _validate_company_name(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, str):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.company_name",
                reason="must be a string",
                value=value,
            )
        )
        return errors
    if len(value) == 0 or len(value) > _COMPANY_NAME_MAX:
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.company_name",
                reason=f"length must be 1..{_COMPANY_NAME_MAX}",
                value=f"<len={len(value)}>",
            )
        )
    return errors


def _validate_address(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, str):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.address",
                reason="must be a string",
                value=value,
            )
        )
        return errors
    if len(value) == 0 or len(value) > _ADDRESS_MAX:
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.address",
                reason=f"length must be 1..{_ADDRESS_MAX}",
                value=f"<len={len(value)}>",
            )
        )
    return errors


def _validate_representative_name(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, str):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.representative_name",
                reason="must be a string",
                value=value,
            )
        )
        return errors
    if len(value) == 0 or len(value) > _REP_NAME_MAX:
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.representative_name",
                reason=f"length must be 1..{_REP_NAME_MAX}",
                value=f"<len={len(value)}>",
            )
        )
    return errors


def _validate_industry_hint(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, str):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.industry_hint",
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
                field="company_subblock.industry_hint",
                reason=f"unknown industry value: {value!r}",
                value=value,
            )
        )
    return errors


def _validate_confirmed_at(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, str) or not _ISO_8601_RE.match(value):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.confirmed_at",
                reason="must be ISO-8601 UTC string (e.g. 2026-07-31T08:00:00Z)",
                value=value,
            )
        )
    return errors


def _validate_confirmed_by(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, str):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.confirmed_by",
                reason="must be a UUID string",
                value=value,
            )
        )
        return errors
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.confirmed_by",
                reason="must be a UUID string (RFC 4122)",
                value=value,
            )
        )
    return errors


def _validate_source_draft_ids(value: Any) -> list[OnboardingSchemaError]:
    errors: list[OnboardingSchemaError] = []
    if not isinstance(value, list):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock.source_draft_ids",
                reason="must be a list of UUID strings",
                value=value,
            )
        )
        return errors
    for idx, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(
                OnboardingSchemaError(
                    field=f"company_subblock.source_draft_ids[{idx}]",
                    reason="must be a UUID string",
                    value=item,
                )
            )
            continue
        try:
            uuid.UUID(item)
        except (ValueError, AttributeError):
            errors.append(
                OnboardingSchemaError(
                    field=f"company_subblock.source_draft_ids[{idx}]",
                    reason="must be a UUID string (RFC 4122)",
                    value=item,
                )
            )
    return errors


def _validate_company_subblock(value: Any) -> list[OnboardingSchemaError]:
    """Validate `tenant_settings.onboarding.company_subblock` (Story 1.3).

    All fields are independently optional. The validator only checks
    fields that are present. Unknown subkeys are flagged (typo defense).

    Returns:
        List of `OnboardingSchemaError` (empty if clean).
    """
    errors: list[OnboardingSchemaError] = []
    if value is None:
        return errors  # subblock is optional
    if not isinstance(value, dict):
        errors.append(
            OnboardingSchemaError(
                field="company_subblock",
                reason="must be an object",
                value=value,
            )
        )
        return errors
    # Typo defense: unknown subkeys are flagged.
    for key in value:
        if key not in _COMPANY_SUBBLOCK_KEYS:
            errors.append(
                OnboardingSchemaError(
                    field=f"company_subblock.{key}",
                    reason=(
                        f"unknown subkey (must be one of " f"{sorted(_COMPANY_SUBBLOCK_KEYS)})"
                    ),
                    value=key,
                )
            )
    # Per-field validation (only when present — partial semantics).
    if "business_registration_number" in value:
        errors.extend(_validate_business_registration_number(value["business_registration_number"]))
    if "company_name" in value:
        errors.extend(_validate_company_name(value["company_name"]))
    if "address" in value:
        errors.extend(_validate_address(value["address"]))
    if "representative_name" in value:
        errors.extend(_validate_representative_name(value["representative_name"]))
    if "industry_hint" in value:
        errors.extend(_validate_industry_hint(value["industry_hint"]))
    if "confirmed_at" in value:
        errors.extend(_validate_confirmed_at(value["confirmed_at"]))
    if "confirmed_by" in value:
        errors.extend(_validate_confirmed_by(value["confirmed_by"]))
    if "source_draft_ids" in value:
        errors.extend(_validate_source_draft_ids(value["source_draft_ids"]))
    return errors


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
    # Story 1.3 — AI company-identity subblock (AC #3.4 Option C).
    # Always validated when present (partial semantics); not required when absent.
    if "company_subblock" in jsonb:
        errors.extend(_validate_company_subblock(jsonb.get("company_subblock")))

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
