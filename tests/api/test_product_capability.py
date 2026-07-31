"""tests.api.test_product_capability — capability × product-type matrix (Story 2.1 — T6.4).

Pure-logic parametrize over `is_type_allowed_for_industry` from
`apps.api.modules.m1_baseline.services.product_service`. Mirrors the
`_INDUSTRY_CAPABILITIES` map in `apps.api.core.capability.py`:

  - manufacturing  → PRODUCT ✓ + PRODUCT_MATERIAL ✓  → all 5 types
  - service        → PRODUCT ✓ + PRODUCT_MATERIAL ✗ → only `service` type
  - manufacturing_service              → both ✓    → all 5 types
  - manufacturing_service_other         → both ✓    → all 5 types

Service tenants get a 403 INDUSTRY_NOT_SUPPORTED when they POST
`product_type='material'` or `'semi_product'`. Defense in depth —
the menu UI hides those types, the backend rejects them anyway.
"""

from __future__ import annotations

import pytest

from apps.api.modules.m1_baseline.services.product_service import (
    is_type_allowed_for_industry,
)
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m1_baseline.schemas import ProductType


# ── Type inventory ────────────────────────────────────────────
def test_all_five_product_types_exist() -> None:
    """PRD §8.M1 specifies 5 types — drift sentinel."""
    assert {pt.value for pt in ProductType} == {
        "product",
        "semi_product",
        "material",
        "goods",
        "service",
    }


# ── Manufacturing: all 5 types allowed ────────────────────────
@pytest.mark.parametrize("pt", list(ProductType))
def test_manufacturing_allows_every_type(pt: ProductType) -> None:
    """Manufacturing tenants (PRODUCT + PRODUCT_MATERIAL capabilities)
    may register any of the 5 product types."""
    assert is_type_allowed_for_industry(Industry.MANUFACTURING, pt) is True


# ── Service: only `service` allowed ────────────────────────────
@pytest.mark.parametrize(
    "pt",
    [ProductType.SERVICE],
)
def test_service_industry_allows_service_type(pt: ProductType) -> None:
    """Service tenants (PRODUCT capability only — no PRODUCT_MATERIAL)
    may register the `service` product type."""
    assert is_type_allowed_for_industry(Industry.SERVICE, pt) is True


@pytest.mark.parametrize(
    "pt",
    [ProductType.MATERIAL, ProductType.SEMI_PRODUCT],
)
def test_service_industry_rejects_physical_types(pt: ProductType) -> None:
    """Service tenants CANNOT register material/semi_product (AC #6).

    These two types need PRODUCT_MATERIAL capability, which is NOT
    granted to `service` industry tenants. `product`/`goods`/`service`
    types are unrestricted — service tenants may register them for
    ABC catalog purposes.
    """
    assert is_type_allowed_for_industry(Industry.SERVICE, pt) is False


@pytest.mark.parametrize(
    "pt",
    [ProductType.PRODUCT, ProductType.GOODS, ProductType.SERVICE],
)
def test_service_industry_allows_non_physical_types(pt: ProductType) -> None:
    """Service tenants CAN register product/goods/service types (no
    PRODUCT_MATERIAL needed for these). Only material/semi_product
    are gated."""
    assert is_type_allowed_for_industry(Industry.SERVICE, pt) is True


# ── Manufacturing + service hybrid (③): all 5 types ───────────
@pytest.mark.parametrize("pt", list(ProductType))
def test_manufacturing_service_allows_every_type(pt: ProductType) -> None:
    """Hybrid industries (PRODUCT + PRODUCT_MATERIAL) allow all 5 types."""
    assert (
        is_type_allowed_for_industry(Industry.MANUFACTURING_SERVICE, pt) is True
    )
    assert (
        is_type_allowed_for_industry(
            Industry.MANUFACTURING_SERVICE_OTHER, pt
        )
        is True
    )


# ── Defensive: industry=None is a conservative deny ────────────
@pytest.mark.parametrize(
    "pt",
    [ProductType.MATERIAL, ProductType.SEMI_PRODUCT],
)
def test_no_industry_rejects_physical_types(pt: ProductType) -> None:
    """When the tenant has no industry selected (None), physical types
    are denied even for non-service paths. Conservative default."""
    assert is_type_allowed_for_industry(None, pt) is False


# ── Defensive: industry=None is a conservative deny ────────────
@pytest.mark.parametrize(
    "pt",
    [ProductType.MATERIAL, ProductType.SEMI_PRODUCT],
)
def test_no_industry_rejects_physical_types(pt: ProductType) -> None:
    """When the tenant has no industry selected (None), physical types
    are denied even for non-service paths. Conservative default."""
    assert is_type_allowed_for_industry(None, pt) is False


@pytest.mark.parametrize(
    "pt",
    [ProductType.PRODUCT, ProductType.GOODS, ProductType.SERVICE],
)
def test_no_industry_allows_non_physical_types(pt: ProductType) -> None:
    """Non-physical types (product / goods / service) are allowed even
    when industry is unset — these don't need PRODUCT_MATERIAL."""
    assert is_type_allowed_for_industry(None, pt) is True
