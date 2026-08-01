"""packages.services.m1_baseline — M1 baseline shared domain (Story 2.1).

Pure-Python domain logic for the M1 baseline module. Imports only stdlib
+ `enum` + `re` — **no DB, no Pydantic, no web, no clock** (AD-1/AD-5).

This package is the **single source of truth** for:
- `ProductType` enum (PRD §4.1 + §8.M1 — 제품·반제품·원자재·상품·서비스).
- `PRODUCT_TYPE_PREFIX` map — code prefix (3-letter) per type.
- `PRODUCT_TYPE_LABEL_KO` map — user-facing Korean label per type.
- `generate_next_code` / `parse_code` / `is_valid_code_format` — per-tenant
  per-type sequence code helpers (AD-18 single product identity, AD-15 §3).
- `BOM_REFERENCE_QUERY` + `count_bom_references` / `count_ledger_references` /
  `total_references` — type-change integrity guard (Story 2.3 / PRD §6.1).

Both the API (FastAPI handlers, Pydantic schemas) and the web (TS mirror
in `apps/web/lib/menu-config.ts`) consume these definitions. Drift between
Python and TS is caught by `tests/integration/test_product_type_consistency.py`.

Per AD-11 layer rule (with documented `money.py` exception only):
`packages/services/m1_baseline/` may NOT import from `packages.cost_engine`.
It may NOT import from `apps.api.*` either.
"""

from packages.services.m1_baseline.bom_validation import (  # noqa: F401
    InvalidRatioTypeError,
    TARGET_TOTAL,
    is_complete_bom,
    missing_to_complete,
    quantize_ratio,
    sum_ratios,
)
from packages.services.m1_baseline.product_code import (  # noqa: F401
    InvalidProductCodeError,
    generate_next_code,
    is_valid_code_format,
    parse_code,
)
from packages.services.m1_baseline.product_references import (  # noqa: F401
    BOM_REFERENCE_QUERY,
    count_bom_references,
    count_ledger_references,
    total_references,
)
from packages.services.m1_baseline.schemas import (  # noqa: F401
    BOMChildType,
    BOMParentType,
    PRODUCT_TYPE_LABEL_KO,
    PRODUCT_TYPE_PREFIX,
    ProductType,
    is_valid_bom_child,
    is_valid_bom_parent,
)
