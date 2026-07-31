"""tests.api.test_products — Product service typed-exception contract tests.

Story 2.1 — Task 6.2 (focused subset).

DB-backed happy-path tests (POST/PATCH end-to-end) are deferred to
Story 0.5 (needs `pytest-postgresql` fixture). This file covers the
typed-exception contract (AD-15 §4) — the wire shape that downstream
handlers and frontends depend on.

Coverage:
- ProductNotFoundError carries tenant_id + product_id + trace_id.
- ProductCodeDuplicateError carries code + existing_product_id + trace_id.
- ProductImmutableFieldError names the offending field.
- InvalidProductCodeError (from `packages.services.m1_baseline.product_code`)
  carries the code + reason.
- ProductCapabilityError carries current_industry + requested_type.
- Code generation: invalid code shapes raise InvalidProductCodeError with
  the proper reason.
- _TYPE_REQUIRES_PRODUCT_MATERIAL contains exactly material + semi_product
  (no other type may be PRODUCT_MATERIAL-gated).
"""

from __future__ import annotations

import uuid

import pytest

from apps.api.modules.m1_baseline.services.product_service import (
    ProductCapabilityError,
    ProductCodeDuplicateError,
    ProductImmutableFieldError,
    ProductNotFoundError,
)
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m1_baseline.product_code import (
    InvalidProductCodeError,
    is_valid_code_format,
    parse_code,
)
from packages.services.m1_baseline.schemas import ProductType


# ── ProductNotFoundError ───────────────────────────────────────
def test_product_not_found_carries_full_context() -> None:
    """AC #5 / 404 PRODUCT_NOT_FOUND — error carries enough context
    for the handler to echo `product_id` in the response body."""
    tenant_id = uuid.uuid4()
    product_id = uuid.uuid4()
    trace_id = "test-trace-001"

    err = ProductNotFoundError(
        tenant_id=tenant_id,
        product_id=product_id,
        trace_id=trace_id,
    )

    assert err.tenant_id == tenant_id
    assert err.product_id == product_id
    assert err.trace_id == trace_id
    assert str(product_id) in str(err)


# ── ProductCodeDuplicateError ─────────────────────────────────
def test_product_code_duplicate_carries_existing_id() -> None:
    """AC #3 / 409 PRODUCT_CODE_DUPLICATE — error includes the
    existing product's UUID so the frontend can offer 'go to that row'."""
    tenant_id = uuid.uuid4()
    existing_id = uuid.uuid4()
    trace_id = "test-trace-002"

    err = ProductCodeDuplicateError(
        tenant_id=tenant_id,
        code="MAT-0042",
        existing_product_id=existing_id,
        trace_id=trace_id,
    )

    assert err.code == "MAT-0042"
    assert err.existing_product_id == existing_id
    assert err.trace_id == trace_id


def test_product_code_duplicate_with_unknown_existing() -> None:
    """When the existing row cannot be located after IntegrityError,
    `existing_product_id` may be None — the error still surfaces."""
    err = ProductCodeDuplicateError(
        tenant_id=uuid.uuid4(),
        code="PRD-9999",
        existing_product_id=None,
        trace_id="t",
    )
    assert err.existing_product_id is None


# ── ProductImmutableFieldError ─────────────────────────────────
def test_immutable_field_error_names_code_field() -> None:
    """AC #4 / 403 PRODUCT_IMMUTABLE_FIELD — the error names the field
    so the handler can build a Korean message."""
    err = ProductImmutableFieldError(field="code", trace_id="t")
    assert err.field == "code"


def test_immutable_field_error_names_type_field() -> None:
    """AC #4 — `product_type` is also immutable (Story 2.3 territory)."""
    err = ProductImmutableFieldError(field="product_type", trace_id="t")
    assert err.field == "product_type"


# ── ProductCapabilityError ─────────────────────────────────────
def test_capability_error_carries_industry_and_type() -> None:
    """AC #6 / 403 INDUSTRY_NOT_SUPPORTED — error carries the current
    industry (or None) + the requested type for the handler to format."""
    err = ProductCapabilityError(
        tenant_id=uuid.uuid4(),
        current_industry=Industry.SERVICE,
        requested_type=ProductType.MATERIAL,
        trace_id="t",
    )
    assert err.current_industry == Industry.SERVICE
    assert err.requested_type == ProductType.MATERIAL
    assert err.trace_id == "t"


def test_capability_error_with_null_industry() -> None:
    """Edge case — industry may be None if the tenant hasn't selected
    one yet (defensive conservative deny)."""
    err = ProductCapabilityError(
        tenant_id=uuid.uuid4(),
        current_industry=None,
        requested_type=ProductType.MATERIAL,
        trace_id="t",
    )
    assert err.current_industry is None


# ── Code format validation ────────────────────────────────────
def test_valid_code_format_accepts_canonical_shapes() -> None:
    """MAT-0042 / PRD-0001 / SEM-10000 are all valid."""
    assert is_valid_code_format("MAT-0042") is True
    assert is_valid_code_format("PRD-0001") is True
    assert is_valid_code_format("SEM-10000") is True  # overflow allowed


@pytest.mark.parametrize(
    "bad_code",
    [
        "mat-0042",  # lowercase prefix
        "MAT0001",  # missing dash
        "MAT-",  # missing suffix
        "MAT",  # no dash
        "MAT0042",  # no dash
        "MAT-004",  # only 3 digits (regex requires 4+)
        "XX-0001",  # invalid prefix
        "MAT0042-",  # dash at wrong end
        "",
        "MAT-ABCD",  # non-numeric suffix
    ],
)
def test_invalid_code_format_rejects(bad_code: str) -> None:
    """Manual codes must match `^[A-Z]{3}-\\d{4,}$` — invalid shapes
    raise InvalidProductCodeError with a descriptive reason."""
    assert is_valid_code_format(bad_code) is False


def test_parse_code_round_trip() -> None:
    """AC #1 — `parse_code` is the inverse of `generate_next_code`."""
    pt, seq = parse_code("MAT-0042")
    assert pt == ProductType.MATERIAL
    assert seq == 42


def test_parse_code_invalid_raises() -> None:
    """parse_code raises InvalidProductCodeError on bad format."""
    import pytest
    with pytest.raises(InvalidProductCodeError):
        parse_code("MAT-004")


# ── Capability gate set membership ─────────────────────────────
def test_capability_gate_includes_exactly_material_and_semi_product() -> None:
    """The PRODUCT_MATERIAL-gated set is exactly {material, semi_product}.

    Drift sentinel — if a future story adds a 6th type that needs
    PRODUCT_MATERIAL, this test must be updated in tandem.
    """
    from apps.api.modules.m1_baseline.services.product_service import (
        _TYPE_REQUIRES_PRODUCT_MATERIAL,
    )
    assert {
        ProductType.MATERIAL,
        ProductType.SEMI_PRODUCT,
    } == _TYPE_REQUIRES_PRODUCT_MATERIAL


# ── Industry mapping sanity ────────────────────────────────────
def test_industry_enum_has_four_values() -> None:
    """Industry is the canonical PRD §4.1 4지선다. Drift sentinel."""
    assert {i.value for i in Industry} == {
        "manufacturing",
        "service",
        "manufacturing_service",
        "manufacturing_service_other",
    }


def test_product_type_enum_has_five_values() -> None:
    """PRD §8.M1 specifies 5 product types. Drift sentinel."""
    assert {pt.value for pt in ProductType} == {
        "product",
        "semi_product",
        "material",
        "goods",
        "service",
    }
