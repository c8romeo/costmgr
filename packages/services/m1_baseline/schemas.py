"""packages.services.m1_baseline.schemas — M1 baseline canonical enums (Story 2.1).

Pure-Python module — **no Pydantic, no DB, no web** (AD-1/AD-5).

Defines the canonical product-type vocabulary (PRD §4.1 + §8.M1) that flows
through every layer:

    API Pydantic schemas  ──┐
    ProductService         ──┼──> ProductType (this module, AD-15 §0.5 mirror)
    Capability gate        ──┘
    Frontend (TS mirror)  ────> test_product_type_consistency.py

AD binds enforced here:
- AD-15 — snake_case enum values, PascalCase class names. Korean labels are
  user-facing strings, not code identifiers.
- AD-23 — `ProductType` is per-row enum, NOT a JSONB namespace. Each row in
  `products` carries its own `product_type` value.
- AD-18 — single product identity: `products.id` (UUID v7) is the sole key.
  `code` (PRD §8.M1 "코드") is a per-tenant per-type sequence number used
  for human-readable display, not the primary identifier.
"""

from __future__ import annotations

from enum import Enum
from typing import Final, FrozenSet


class ProductType(str, Enum):
    """PRD §4.1 / §8.M1 — 제품·반제품·원자재·상품·서비스 5지선다.

    Backend canonical enum values (snake_case). Mapped to a Korean label via
    `PRODUCT_TYPE_LABEL_KO` for UI display, and to a code prefix via
    `PRODUCT_TYPE_PREFIX` for the auto-generated code (e.g. `MAT-0042`).

    Codes:
    - `product`        = ① 제품      prefix PRD
    - `semi_product`   = ② 반제품     prefix SEM
    - `material`       = ③ 원자재     prefix MAT
    - `goods`          = ④ 상품      prefix GDS
    - `service`        = ⑤ 서비스     prefix SVC

    Note: industry gate (PRODUCT + PRODUCT_MATERIAL capabilities) is enforced
    separately at write time — see `apps.api.core.capability`.
    """

    PRODUCT = "product"
    SEMI_PRODUCT = "semi_product"
    MATERIAL = "material"
    GOODS = "goods"
    SERVICE = "service"


# ── Type → Code prefix map (PRD §8.M1 "코드") ─────────────────
# 3-letter uppercase prefix (Korean romanization / English initials).
# The prefix is intentionally NOT equal to the enum literal value because
# Snake_case (`material`, `semi_product`) → noisy prefix. Shorter codes
# improve readability in lists & spreadsheets.
PRODUCT_TYPE_PREFIX: Final[dict[ProductType, str]] = {
    ProductType.PRODUCT: "PRD",
    ProductType.SEMI_PRODUCT: "SEM",
    ProductType.MATERIAL: "MAT",
    ProductType.GOODS: "GDS",
    ProductType.SERVICE: "SVC",
}


# ── Type → Korean label map (UI-facing) ───────────────────────
# PRD §4.1 / §8.M1 user-facing labels. Used by:
# - `ProductTypeBadge` (TS) for the colored badges in the list.
# - The form's product_type radio grid.
# - Tooltip copy for the industry-conditional gating.
PRODUCT_TYPE_LABEL_KO: Final[dict[ProductType, str]] = {
    ProductType.PRODUCT: "제품",
    ProductType.SEMI_PRODUCT: "반제품",
    ProductType.MATERIAL: "원자재",
    ProductType.GOODS: "상품",
    ProductType.SERVICE: "서비스",
}


# ── Bidirectional prefix ↔ type helpers ──────────────────────
# Used by `product_code.py` for code parsing (MAT-0042 → ('material', 42)).
# Exposed here so both sides use the same source-of-truth (no drift).
def prefix_to_type(prefix: str) -> ProductType:
    """Resolve a 3-letter prefix to its ProductType. Raises KeyError."""
    for pt, pfx in PRODUCT_TYPE_PREFIX.items():
        if pfx == prefix:
            return pt
    raise KeyError(f"unknown product prefix: {prefix}")


def type_to_prefix(product_type: ProductType) -> str:
    """Return the 3-letter code prefix for the given type."""
    return PRODUCT_TYPE_PREFIX[product_type]


# ── BOM type rules (PRD §6.1(1) + §8.M1(b)) ────────────────────
# Story 2.2 — which product types can be a BOM parent, and which can be a
# BOM child. Mirrored on the TS side via `apps/web/lib/bom-validation.ts`
# (drift-checked by `tests/integration/test_bom_validation_consistency.py`).
#
# Per PRD §6.1(1) — only `material` (and `semi_product` for multi-level
# rollups) participate as BOM children. `product`, `goods`, `service` have
# no sub-components.
#
# Per PRD §6.1 — `material` / `goods` / `service` cannot be BOM parents
# (`material` is the BOM leaf, `goods` is trade-merchandise with no BOM,
# `service` is an ABC cost object). Only `product` and `semi_product`
# can be parents.
#
# These sets are **service-layer enforcement** — the database has no CHECK
# constraint on these (a DB-level check would require a trigger that
# JOINs to `products`, which is impractical). The service is the source
# of truth.
BOMParentType: Final[FrozenSet[ProductType]] = frozenset(
    {
        ProductType.PRODUCT,
        ProductType.SEMI_PRODUCT,
    }
)

BOMChildType: Final[FrozenSet[ProductType]] = frozenset(
    {
        ProductType.MATERIAL,
        ProductType.SEMI_PRODUCT,
    }
)


def is_valid_bom_parent(product_type: ProductType) -> bool:
    """Pure helper: can `product_type` be a BOM parent?

    Mirrors Story 2.2 AC #6 — only `product` and `semi_product`.
    """
    return product_type in BOMParentType


def is_valid_bom_child(product_type: ProductType) -> bool:
    """Pure helper: can `product_type` be a BOM child?

    Mirrors Story 2.2 AC #5 — only `material` and `semi_product`.
    """
    return product_type in BOMChildType
