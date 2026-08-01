"""tests.integration.test_product_type_change_consistency — Story 2.3 drift guard.

Task 4.1 / Task 6.4 — Python ↔ TS wire-shape consistency for the type
change integrity guard. Mirrors the pattern of
`test_bom_validation_consistency.py` and `test_product_type_consistency.py`:

- Python 409 PRODUCT_TYPE_HAS_REFERENCES envelope (`handlers.py`)
- TS `ProductUpdateRequest` exposes `product_type` as optional field
- TS `updateProduct()` function exists and accepts the new body
- TS `ApiError` can carry the new code (the `code` field is already
  `string`, so this is a presence-only assertion — meaningful once
  consumers start branching on it)

The test does NOT use vitest — regex-only static parse, hermetic to the
engine workspace.

Pattern: CR 1.1 lesson — DB/integration tests skip when infra missing;
pure-logic drift tests xfail strict=False. This file is pure regex, so
all assertions are strict and missing files are HARD FAIL.

Post-review changes (2026-08-01):
- D1 (post-review): pinned AC #1 literal wording — assert
  `"BOM {N}건에서 참조 중"` substring present.
- P3 (post-review): tightened `code NOT in ProductUpdateRequest` assertion —
  the previous `or True` short-circuit made AD-18 invariant vacuous.
- P15 (post-review): added `trace_id` assertion in 409 envelope test.
- P16 (post-review): added mixed same-type scenario test
  (PATCH with `name` + unchanged `product_type`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDLERS_PATH = REPO_ROOT / "apps" / "api" / "modules" / "m1_baseline" / "handlers.py"
API_CLIENT_PATH = REPO_ROOT / "apps" / "web" / "lib" / "api-client.ts"
SCHEMAS_PATH = REPO_ROOT / "apps" / "api" / "modules" / "m1_baseline" / "schemas.py"
SERVICE_PATH = (
    REPO_ROOT / "apps" / "api" / "modules" / "m1_baseline" / "services" / "product_service.py"
)


def _read(path: Path) -> str:
    if not path.exists():
        pytest.fail(
            f"Required file not found at {path}. "
            "Story 2.3 implementation must create this file."
        )
    return path.read_text(encoding="utf-8")


# ── Python side — guardrails ─────────────────────────────────


def test_handlers_emit_product_type_has_references_409() -> None:
    """AD-15 §4 — handler returns 409 with code PRODUCT_TYPE_HAS_REFERENCES.

    P15 (post-review): also assert `trace_id` is present in the
    handler's error envelope per AD-15 §4 contract.
    """
    src = _read(HANDLERS_PATH)
    # 409 status code
    assert "status.HTTP_409_CONFLICT" in src
    # Code literal
    assert '"PRODUCT_TYPE_HAS_REFERENCES"' in src
    # Mapping clause for the exception
    assert "ProductTypeHasReferencesError" in src
    # The clause is BEFORE the immutable field clause (more specific first)
    pos_409 = src.find("except ProductTypeHasReferencesError as err")
    pos_immutable = src.find("except ProductImmutableFieldError as err")
    assert 0 < pos_409 < pos_immutable, (
        "ProductTypeHasReferencesError clause must precede ProductImmutableFieldError "
        "clause (more specific exception first per AD-15 §4)."
    )
    # P15 (post-review): trace_id is part of the AD-15 §4 envelope contract.
    # The handler must populate `trace_id` in the details (or pass the
    # request-level trace through). Look for both the literal `trace_id`
    # key AND a meaningful non-empty default.
    assert "trace_id" in src
    assert "trace_id=trace_id" in src or "trace_id=err.trace_id" in src, (
        "handler must propagate trace_id into the 409 details envelope"
    )


def test_handlers_message_ko_helper_present() -> None:
    """Korean-aware formatter builds the user-facing message.

    D1 (post-review): AC #1 pins the wording to include `"BOM {N}건에서
    참조 중"` substring. The previous implementation used `"다른 곳에서"`
    which doesn't pin to BOM. Tightened assertion.
    """
    src = _read(HANDLERS_PATH)
    assert "def _format_type_references_message_ko" in src
    # AC #1 literal substring pin — "BOM N건에서 참조 중"
    assert "BOM {err.bom_count}건에서 참조 중" in src or "BOM {n}건에서 참조 중" in src, (
        "AC #1 pins message_ko to 'BOM N건에서 참조 중 — ...'. "
        "The implementation must include the BOM prefix and '건에서 참조 중'."
    )
    # Mentions ledger count (Korean: 수불) — appears when ledger_count > 0
    assert "수불" in src
    # Mentions 이관 (migration) — AC #1 second clause
    assert "이관" in src


def test_schemas_product_update_request_has_product_type_field() -> None:
    """Pydantic schema accepts `product_type` (P5: non-nullable when present)."""
    src = _read(SCHEMAS_PATH)
    # Class name is `ProductUpdateRequest`
    assert "class ProductUpdateRequest" in src
    # The field is part of the body (no longer Optional — P5 post-review)
    assert "product_type" in src
    # P5 (post-review): the schema makes `product_type` non-nullable to
    # prevent the silent-ignore bug. Find the field declaration and
    # ensure it does NOT use `| None`.
    # Look for `product_type: ProductType` (without `| None`).
    field_decl = src.split("class ProductUpdateRequest", 1)[1].split(
        "class ProductResponse", 1
    )[0]
    # The field must be declared with `ProductType` (not `ProductType | None`)
    assert "product_type: ProductType" in field_decl, (
        "P5 post-review: ProductUpdateRequest.product_type must be non-nullable. "
        "Wire-level null is meaningless and must be rejected at validation."
    )


def test_service_raises_typed_exception_with_counts() -> None:
    """Service emits `ProductTypeHasReferencesError` with bom/ledger/total counts."""
    src = _read(SERVICE_PATH)
    # Exception class
    assert "class ProductTypeHasReferencesError" in src
    # Constructor takes bom_count + ledger_count
    assert "bom_count" in src
    assert "ledger_count" in src
    # Total property
    assert "total_count" in src


# ── TS side — guardrails ──────────────────────────────────────


def test_ts_api_client_product_update_request_has_product_type() -> None:
    """TS `ProductUpdateRequest` exposes `product_type?: ProductType` (optional)."""
    src = _read(API_CLIENT_PATH)
    # Interface declaration present
    assert "interface ProductUpdateRequest" in src
    # New field present and optional
    assert "product_type?: ProductType" in src


def test_ts_api_client_update_product_function_present() -> None:
    """`updateProduct(id, body, ...)` is the existing typed PATCH helper."""
    src = _read(API_CLIENT_PATH)
    assert "export async function updateProduct" in src


# ── Cross-language — error envelope contract ──────────────────


def test_error_envelope_details_match_across_python_and_ts() -> None:
    """Both sides carry `{product_id, requested_type, bom_count, ledger_count, total_count}`.

    The Python side emits them as `details={...}` in the handler. The
    TS side's `ApiError.payload.details` is already typed as
    `Record<string, unknown>`, so this is a SHAPE-presence check on
    the producer (Python handler). The consumer branching is at the
    frontend call site (T5).
    """
    src = _read(HANDLERS_PATH)
    # All five detail keys present in the 409 clause
    for key in ("product_id", "requested_type", "bom_count", "ledger_count", "total_count"):
        assert key in src, f"Missing details key {key!r} in product_type handler 409 clause"


# ── Drift sentinels — wire shape stability ────────────────────


def test_product_update_request_field_set_is_stable() -> None:
    """PRD §8.M1 + AD-18 — fields allowed on PATCH.

    Pins the editable surface. Adding a field requires also adding the
    matching handler clause + test. Any drift here is a signal that the
    API contract changed — review and update consumers.

    P3 (post-review): the previous assertion
    ``assert "code?" not in ... or True`` made AD-18 invariant vacuous
    (always passes regardless of whether `code` is in the interface).
    Tightened: extract the ProductUpdateRequest block first, then
    fail HARD if `code?:` appears in it.
    """
    src = _read(API_CLIENT_PATH)
    editable = ("name", "unit", "unit_cost_krw", "unit_cost_usd", "description",
                "is_active", "product_type")
    for field in editable:
        assert f"{field}?" in src or f"{field}?:" in src or f"{field}: string" in src, (
            f"TS ProductUpdateRequest missing editable field {field!r}"
        )
    # P3 (post-review): extract the ProductUpdateRequest interface body
    # and assert `code` is NOT in it. AD-18 single product identity.
    interface_block = src.split("export interface ProductUpdateRequest", 1)[1].split(
        "}", 1
    )[0]
    assert "code" not in interface_block, (
        f"AD-18 violation: `code` MUST NOT be in ProductUpdateRequest. "
        f"Found `code` in: {interface_block!r}"
    )


def test_service_same_type_with_other_field_change_skips_count() -> None:
    """P16 (post-review): AC #9 — same-type PATCH must skip BOM count even
    when other mutable fields are also in the body.

    The service guards the BOM-count block behind
    ``if new_type.value != row.product_type`` — when the type is sent
    but equals the current value, the count query must NOT run. This
    regression test prevents a future refactor from inverting the
    condition and triggering the count for no-op type PATCHes.
    """
    src = _read(SERVICE_PATH)
    # Find the section between the load and the field-update loop.
    # Look for the guard that triggers the count + mutation block.
    # The block must be inside an `if` that compares `new_type.value`
    # against `row.product_type`.
    assert "new_type.value != row.product_type" in src, (
        "AC #9 guard must be `new_type.value != row.product_type` — "
        "triggers BOM-count only on actual type change."
    )
    # The `_count_product_references` call must be inside that guard.
    guard_pos = src.find("new_type.value != row.product_type")
    count_call_pos = src.find("_count_product_references")
    mutation_pos = src.find("row.product_type = new_type.value")
    assert guard_pos < count_call_pos < mutation_pos, (
        "BOM-count + mutation must be inside the type-change guard. "
        "AC #9: same-type PATCH must skip both."
    )
