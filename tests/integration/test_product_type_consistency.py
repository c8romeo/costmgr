"""tests.integration.test_product_type_consistency — drift guard for ProductType.

Story 2.1 — Task 6.7. The canonical product type vocabulary lives in TWO
places:

  - `packages/services/m1_baseline/schemas.py` (Python, source of truth)
  - `apps/web/lib/menu-config.ts` (TypeScript mirror, consumed by Next.js)

This test parses the TypeScript file and asserts that:

  1. The set of ProductType values matches.
  2. The Korean label dictionary matches (PRD §8.M1 "코드" labels).
  3. The code prefix dictionary matches (PRD §8.M1 3-letter codes).

The test does NOT use Node / ts-node — just regex parsing, so it's
hermetic to the engine workspace.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m1_baseline.schemas import (
    PRODUCT_TYPE_LABEL_KO,
    PRODUCT_TYPE_PREFIX,
    ProductType,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_PATH = REPO_ROOT / "apps" / "web" / "lib" / "menu-config.ts"


def _read_ts_source() -> str:
    """Read the TS file as text, stripping line + block comments.

    F-25 (Story 0.2 lesson): strip comments so doc-comment text doesn't
    satisfy label-matching regexes.

    M11b: missing TS mirror is a HARD FAIL, not a skip. The test's
    purpose is drift detection — silently skipping it would let
    production code ship with a Python/TS mismatch. Mirrors the
    pattern in `test_menu_config_consistency.py`.
    """
    if not TS_PATH.exists():
        pytest.fail(
            f"Required TypeScript mirror not found at {TS_PATH}. "
            "Story 2.1 T5.7 must create this file alongside the Python enum."
        )
    raw = TS_PATH.read_text(encoding="utf-8")
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", no_block, flags=re.MULTILINE)


def _extract_ts_product_type_values(ts_src: str) -> list[str]:
    """Extract the array literal under `export const PRODUCT_TYPE_VALUES = [...]`."""
    m = re.search(
        r"export\s+const\s+PRODUCT_TYPE_VALUES\s*=\s*\[(.*?)\]\s*as\s+const",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail("PRODUCT_TYPE_VALUES declaration not found in TS mirror")
    body = m.group(1)
    return re.findall(r'"([a-z_]+)"', body)


def _extract_ts_dict(ts_src: str, name: str) -> dict[str, str]:
    """Extract a `name: Record<...>` block — keys are quoted strings.

    Handles the `Record<ProductType, string> = { key: "label", ... }` shape.
    Returns a dict.
    """
    m = re.search(
        rf"export\s+const\s+{name}\s*:\s*Record<[^>]+>\s*=\s*\{{(.*?)\}};",
        ts_src,
        flags=re.DOTALL,
    )
    if not m:
        pytest.fail(f"{name} declaration not found in TS mirror")
    body = m.group(1)
    pairs = re.findall(r'([a-z_]+)\s*:\s*"([^"]+)"', body)
    return dict(pairs)


# ── Test cases ────────────────────────────────────────────────

def test_product_type_values_match_python() -> None:
    """PRODUCT_TYPE_VALUES (TS) == ProductType (Py)."""
    ts_src = _read_ts_source()
    ts_values = sorted(_extract_ts_product_type_values(ts_src))
    py_values = sorted(pt.value for pt in ProductType)
    assert ts_values == py_values, (
        f"ProductType drift: TS={ts_values!r}, Py={py_values!r}"
    )


def test_product_type_label_ko_matches_python() -> None:
    """Korean labels match (PRD §8.M1)."""
    ts_src = _read_ts_source()
    ts_labels = _extract_ts_dict(ts_src, "PRODUCT_TYPE_LABEL_KO")
    py_labels = {pt.value: PRODUCT_TYPE_LABEL_KO[pt] for pt in ProductType}
    assert ts_labels == py_labels, (
        f"Label drift: TS={ts_labels!r}, Py={py_labels!r}"
    )


def test_product_type_prefix_matches_python() -> None:
    """3-letter code prefixes match (PRD §8.M1 '코드')."""
    ts_src = _read_ts_source()
    ts_prefixes = _extract_ts_dict(ts_src, "PRODUCT_TYPE_PREFIX")
    py_prefixes = {pt.value: PRODUCT_TYPE_PREFIX[pt] for pt in ProductType}
    assert ts_prefixes == py_prefixes, (
        f"Prefix drift: TS={ts_prefixes!r}, Py={py_prefixes!r}"
    )


# ── Capability gate × product type (Story 2.1 AC #6, R6 review patch) ─────
# Per-industry allowed-type list is intentionally NOT compared against
# TS word-for-word in this test — the TS export (`INDUSTRY_ALLOWED_PRODUCT_TYPES`)
# is the consumer view; the *enforcement* lives in `apps/api/core/capability.py`.
# We assert here that the Python source-of-truth reflects Story 2.1 AC #6:
#   - `manufacturing` industries get all 5 types (PRODUCT + PRODUCT_MATERIAL)
#   - `service` (②) gets `{product, goods, service}` — no BOM menu, so
#     no `material` / `semi_product` (PRODUCT_MATERIAL capability is denied),
#     but it CAN register finished products and trade goods.
@pytest.mark.parametrize(
    ("industry", "expected_types"),
    [
        (Industry.MANUFACTURING, {"product", "semi_product", "material", "goods", "service"}),
        (Industry.SERVICE, {"product", "goods", "service"}),
        (Industry.MANUFACTURING_SERVICE, {"product", "semi_product", "material", "goods", "service"}),
        (Industry.MANUFACTURING_SERVICE_OTHER, {"product", "semi_product", "material", "goods", "service"}),
    ],
)
def test_capability_matrix_service_no_material(industry: Industry, expected_types: set[str]) -> None:
    """Service industry cannot register material/semi_product (Story 2.1 AC #6).

    The Python Capability gate source-of-truth is exercised via the
    derived "allowed types" set. The TS frontend uses
    INDUSTRY_ALLOWED_PRODUCT_TYPES for UI filtering.
    """
    from apps.api.core.capability import (
        Capability,
        industry_supports,
    )

    product_caps = {Capability.PRODUCT, Capability.PRODUCT_MATERIAL}

    # The PRODUCT capability is granted by every industry (catalog CRUD).
    # The PRODUCT_MATERIAL capability gates `material` + `semi_product` only.
    # R6: even without PRODUCT_MATERIAL, service tenants keep the
    # `product` + `goods` catalog subset — finished-good sales and
    # trading catalog rows are BOM-independent.
    if industry_supports(industry, Capability.PRODUCT):
        material_subset = (
            {"material", "semi_product"}
            if industry_supports(industry, Capability.PRODUCT_MATERIAL)
            else set()
        )
        allowed = {"product", "goods", "service"} | material_subset
    else:
        pytest.fail(f"Industry {industry.value} should always have PRODUCT capability")

    assert allowed == expected_types, (
        f"Cap matrix drift: industry={industry.value} "
        f"allowed={allowed!r}, expected={expected_types!r}, capabilities={product_caps!r}"
    )
