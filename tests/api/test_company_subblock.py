r"""tests.api.test_company_subblock — JSONB `company_subblock` validator (Story 1.3 — Task 1.1).

Story 1.3 AC #3.4 / Option C resolution: AI-confirmed company-identity
fields (사업자등록번호, 회사명, 주소, 대표자명, 업종 힌트) flow into
`tenant_settings.onboarding.company_subblock` — a JSONB subkey inside
the existing `onboarding` namespace (AD-23 4-namespace rule preserved).

This subblock is the **single promotion target** for AI extraction in
Epic 1. AD-17's `InputPromoter.promote()` is reserved for Epic 3 monthly
input and is NOT reused here.

Schema:
- `business_registration_number` — optional str, format ``\d{3}-\d{2}-\d{5}``
  (matches Korean business number pattern). Allows NULL until set.
- `company_name`                 — optional str, 1-200 chars
- `address`                      — optional str, 1-500 chars
- `representative_name`          — optional str, 1-100 chars
- `industry_hint`                — optional str, must match `Industry` enum
- `confirmed_at`                 — optional ISO-8601 timestamp (set on review)
- `confirmed_by`                 — optional UUID (set on review)
- `source_draft_ids`             — optional list of UUIDs (audit trail)

All fields are independently optional. The validator only checks fields
that are present (partial semantics — consistent with the rest of the
onboarding JSONB).
"""

from __future__ import annotations

import pytest

from apps.api.core.jsonb_schemas import (
    OnboardingField,
    validate_onboarding_schema,
)


def _onboarding_with_subblock(subblock: dict) -> dict:
    """Wrap a `company_subblock` payload as the full onboarding JSONB."""
    return {"company_subblock": subblock}


# ── Enum: COMPANY_SUBBLOCK is a canonical onboarding field ────
def test_company_subblock_is_onboarding_field() -> None:
    """OnboardingField.COMPANY_SUBBLOCK exists for type-safe dispatch."""
    assert OnboardingField.COMPANY_SUBBLOCK.value == "company_subblock"


# ── Clean payloads ────────────────────────────────────────────
def test_empty_subblock_passes_partial() -> None:
    """Empty subblock (no AI confirmations yet) is a valid state.

    All fields are optional. A tenant who never used AI extraction has
    `{}` here and that must not be flagged.
    """
    errors = validate_onboarding_schema(_onboarding_with_subblock({}))
    assert errors == []


def test_full_subblock_passes_partial() -> None:
    """A fully populated subblock with all 7 fields present is clean."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock(
            {
                "business_registration_number": "123-45-67890",
                "company_name": "주식회사 KJW",
                "address": "서울특별시 강남구 테헤란로 123",
                "representative_name": "홍길동",
                "industry_hint": "manufacturing",
                "confirmed_at": "2026-07-31T08:00:00Z",
                "confirmed_by": "00000000-0000-0000-0000-000000000001",
                "source_draft_ids": [
                    "00000000-0000-0000-0000-000000000002",
                ],
            }
        )
    )
    assert errors == []


# ── business_registration_number ──────────────────────────────
def test_invalid_business_registration_number_format() -> None:
    """Wrong format (e.g. 10 digits without dashes) is flagged."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"business_registration_number": "1234567890"})
    )
    assert any(
        e.field == "company_subblock.business_registration_number" for e in errors
    )


def test_business_registration_number_must_be_string() -> None:
    """Non-string value (e.g. int) is flagged."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"business_registration_number": 1234567890})
    )
    assert any(
        e.field == "company_subblock.business_registration_number" for e in errors
    )


@pytest.mark.parametrize(
    "valid_number",
    [
        "123-45-67890",  # standard 10-digit KR business number
        "100-10-10000",
        "999-99-99999",
    ],
)
def test_business_registration_number_valid_patterns(valid_number: str) -> None:
    """All canonical-pattern numbers pass."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"business_registration_number": valid_number})
    )
    assert errors == []


# ── company_name, address, representative_name length bounds ──
def test_company_name_too_long_flagged() -> None:
    """company_name > 200 chars is flagged."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"company_name": "X" * 201})
    )
    assert any(e.field == "company_subblock.company_name" for e in errors)


def test_company_name_too_short_flagged() -> None:
    """Empty company_name (length 0) is flagged when present.

    The field is optional, but if it's set it must be non-empty. The
    extraction service should strip empty values before persisting.
    """
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"company_name": ""})
    )
    assert any(e.field == "company_subblock.company_name" for e in errors)


def test_address_too_long_flagged() -> None:
    """address > 500 chars is flagged."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"address": "X" * 501})
    )
    assert any(e.field == "company_subblock.address" for e in errors)


def test_representative_name_too_long_flagged() -> None:
    """representative_name > 100 chars is flagged."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"representative_name": "X" * 101})
    )
    assert any(
        e.field == "company_subblock.representative_name" for e in errors
    )


# ── industry_hint ─────────────────────────────────────────────
def test_industry_hint_unknown_value_flagged() -> None:
    """industry_hint outside Industry enum is flagged.

    The hint is not authoritative — the canonical industry is stored
    under `tenant_settings.onboarding.industry` (Story 1.1). The hint
    here is for display + downstream matching only.
    """
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"industry_hint": "construction"})
    )
    assert any(e.field == "company_subblock.industry_hint" for e in errors)


# ── confirmed_at / confirmed_by / source_draft_ids ────────────
def test_confirmed_at_invalid_iso_flagged() -> None:
    """confirmed_at must be ISO-8601 UTC string."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"confirmed_at": "2026-07-31 08:00:00"})  # not ISO
    )
    assert any(e.field == "company_subblock.confirmed_at" for e in errors)


def test_confirmed_by_non_uuid_flagged() -> None:
    """confirmed_by must be a UUID string (RFC 4122 v4 / v7 acceptable)."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"confirmed_by": "not-a-uuid"})
    )
    assert any(e.field == "company_subblock.confirmed_by" for e in errors)


def test_source_draft_ids_must_be_list_of_uuids() -> None:
    """source_draft_ids is a list[str] where each item is a UUID."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock({"source_draft_ids": "not-a-list"})
    )
    assert any(e.field == "company_subblock.source_draft_ids" for e in errors)

    errors = validate_onboarding_schema(
        _onboarding_with_subblock(
            {"source_draft_ids": ["not-a-uuid"]}
        )
    )
    assert any(
        "source_draft_ids[0]" in e.field for e in errors
    )


# ── Nested object structure ──────────────────────────────────
def test_company_subblock_must_be_object() -> None:
    """A non-object company_subblock (e.g. string) is flagged."""
    errors = validate_onboarding_schema(
        _onboarding_with_subblock("broken")  # type: ignore[arg-type]
    )
    assert any(e.field == "company_subblock" for e in errors)


def test_unknown_company_subblock_key_is_flagged() -> None:
    """Unknown sub-keys inside company_subblock are flagged.

    Catches typos like `bussiness_registration_number` (extra 's').
    The flag stays partial — the validator does NOT raise, just reports.
    """
    errors = validate_onboarding_schema(
        _onboarding_with_subblock(
            {"bussiness_registration_number": "123-45-67890"}  # typo
        )
    )
    assert any(
        e.field.startswith("company_subblock.bussiness") for e in errors
    )


# ── Coexistence with other onboarding keys ───────────────────
def test_company_subblock_coexists_with_wizard_fields() -> None:
    """company_subblock does NOT block wizard fields.

    The wizard writes to top-level keys (fiscal_year_start, currency, etc.)
    and the AI extraction writes to `company_subblock`. Both are validated
    in the same pass — both must be clean.
    """
    errors = validate_onboarding_schema(
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
            "company_subblock": {
                "company_name": "주식회사 KJW",
                "business_registration_number": "123-45-67890",
            },
        }
    )
    assert errors == []


def test_company_subblock_invalid_does_not_mask_other_errors() -> None:
    """An invalid subblock AND an invalid wizard field are both flagged."""
    errors = validate_onboarding_schema(
        {
            "fiscal_year_start": "2026-13",  # invalid
            "currency": "EUR",  # invalid
            "company_subblock": {"business_registration_number": "bad"},  # invalid
        }
    )
    # Wizard errors.
    assert any(e.field == "fiscal_year_start" for e in errors)
    assert any(e.field == "currency" for e in errors)
    # Subblock error.
    assert any(
        e.field == "company_subblock.business_registration_number"
        for e in errors
    )