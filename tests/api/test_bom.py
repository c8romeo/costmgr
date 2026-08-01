"""tests.api.test_bom — BOM service typed-exception contract tests.

Story 2.2 — Task 6.2.

DB-backed happy-path tests (full BOM CRUD end-to-end) are deferred to
Story 0.5 (needs `pytest-postgresql` fixture). This file covers the
typed-exception contract (AD-15 §4) — the wire shape that downstream
handlers and frontends depend on.

Coverage:
- BOMParentNotFoundError / BOMInvalidParentTypeError / BOMInvalidChildTypeError /
  BOMDuplicateChildError / BOMInvalidRatioError all carry the right fields
  for the handler to format the AD-15 envelope.
- BOMService._is_noop_replace distinguishes first-write from idempotent
  re-PUT.
- BOMService._diff_ratios computes the symmetric difference correctly
  (added / changed / removed).
- BOMService._is_unique_bom_violation recognizes asyncpg/psycopg2 23505.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from apps.api.modules.m1_baseline.services.bom_service import (
    BOMDuplicateChildError,
    BOMInvalidChildTypeError,
    BOMInvalidParentTypeError,
    BOMInvalidRatioError,
    BOMParentNotFoundError,
    BOMService,
)
from packages.services.m1_baseline.schemas import ProductType


# ── BOMParentNotFoundError ────────────────────────────────────
def test_bom_parent_not_found_carries_full_context() -> None:
    """404 BOM_PARENT_NOT_FOUND — error carries tenant_id + parent_product_id + trace_id."""
    tenant_id = uuid.uuid4()
    parent_product_id = uuid.uuid4()
    trace_id = "test-trace-bom-001"

    err = BOMParentNotFoundError(
        tenant_id=tenant_id,
        parent_product_id=parent_product_id,
        trace_id=trace_id,
    )

    assert err.tenant_id == tenant_id
    assert err.parent_product_id == parent_product_id
    assert err.trace_id == trace_id
    assert str(parent_product_id) in str(err)


# ── BOMInvalidParentTypeError ─────────────────────────────────
def test_bom_invalid_parent_type_error_carries_type() -> None:
    """422 BOM_INVALID_PARENT_TYPE — error carries the parent type
    so the handler can build the Korean message + the allowed-types list."""
    err = BOMInvalidParentTypeError(
        tenant_id=uuid.uuid4(),
        parent_product_id=uuid.uuid4(),
        parent_type=ProductType.MATERIAL,
        trace_id="t",
    )
    assert err.parent_type == ProductType.MATERIAL
    assert err.trace_id == "t"


@pytest.mark.parametrize(
    "pt",
    [ProductType.MATERIAL, ProductType.GOODS, ProductType.SERVICE],
)
def test_bom_invalid_parent_type_for_each_blocked_type(pt: ProductType) -> None:
    """Defense in depth — every non-{product, semi_product} type can raise."""
    err = BOMInvalidParentTypeError(
        tenant_id=uuid.uuid4(),
        parent_product_id=uuid.uuid4(),
        parent_type=pt,
        trace_id="t",
    )
    assert err.parent_type == pt


# ── BOMInvalidChildTypeError ──────────────────────────────────
def test_bom_invalid_child_type_error_carries_type() -> None:
    """422 BOM_INVALID_CHILD_TYPE — error carries the child type."""
    err = BOMInvalidChildTypeError(
        tenant_id=uuid.uuid4(),
        child_product_id=uuid.uuid4(),
        child_type=ProductType.SERVICE,
        trace_id="t",
    )
    assert err.child_type == ProductType.SERVICE
    assert err.trace_id == "t"


@pytest.mark.parametrize(
    "pt",
    [ProductType.PRODUCT, ProductType.GOODS, ProductType.SERVICE],
)
def test_bom_invalid_child_type_for_each_blocked_type(pt: ProductType) -> None:
    """Defense in depth — every non-{material, semi_product} type can raise."""
    err = BOMInvalidChildTypeError(
        tenant_id=uuid.uuid4(),
        child_product_id=uuid.uuid4(),
        child_type=pt,
        trace_id="t",
    )
    assert err.child_type == pt


# ── BOMDuplicateChildError ────────────────────────────────────
def test_bom_duplicate_child_error_carries_occurrences() -> None:
    """422 BOM_DUPLICATE_CHILD — error includes the duplicate child id + count."""
    dup_id = uuid.uuid4()
    err = BOMDuplicateChildError(
        tenant_id=uuid.uuid4(),
        duplicate_child_product_id=dup_id,
        occurrences=3,
        trace_id="t",
    )
    assert err.duplicate_child_product_id == dup_id
    assert err.occurrences == 3
    assert err.trace_id == "t"


# ── BOMInvalidRatioError ───────────────────────────────────────
def test_bom_invalid_ratio_error_carries_ratio() -> None:
    """422 BOM_INVALID_RATIO — error carries the offending ratio value."""
    err = BOMInvalidRatioError(
        tenant_id=uuid.uuid4(),
        child_product_id=uuid.uuid4(),
        ratio=Decimal("12.345678"),
        max_decimal_places=4,
        trace_id="t",
    )
    assert err.ratio == Decimal("12.345678")
    assert err.max_decimal_places == 4
    assert err.trace_id == "t"


# ── Service internal helpers (pure) ───────────────────────────
class TestIsNoopReplace:
    """CR 2.1 lesson — idempotent no-op audit skip."""

    def test_first_write_is_not_noop(self) -> None:
        """Empty existing + new rows → not no-op (first write emits audit)."""
        existing: dict[uuid.UUID, Decimal] = {}
        new = {uuid.uuid4(): Decimal("100")}
        assert BOMService._is_noop_replace(existing, new) is False

    def test_identical_payloads_is_noop(self) -> None:
        """Same keys + same ratios → no-op (skip audit)."""
        cid = uuid.uuid4()
        existing = {cid: Decimal("100")}
        new = {cid: Decimal("100")}
        assert BOMService._is_noop_replace(existing, new) is True

    def test_different_key_is_not_noop(self) -> None:
        """Different child added → not no-op (audit the change)."""
        cid_a = uuid.uuid4()
        cid_b = uuid.uuid4()
        existing = {cid_a: Decimal("100")}
        new = {cid_b: Decimal("100")}
        assert BOMService._is_noop_replace(existing, new) is False

    def test_different_ratio_is_not_noop(self) -> None:
        """Same child, different ratio → not no-op (audit the change)."""
        cid = uuid.uuid4()
        existing = {cid: Decimal("50")}
        new = {cid: Decimal("60")}
        assert BOMService._is_noop_replace(existing, new) is False


class TestDiffRatios:
    """AC #3 — changed_ratios payload shape."""

    def test_added_only(self) -> None:
        """First write → all entries are (cid, None, new_ratio)."""
        cid = uuid.uuid4()
        existing: dict[uuid.UUID, Decimal] = {}
        new = {cid: Decimal("100")}
        out = BOMService._diff_ratios(existing, new)
        assert out == [(cid, None, Decimal("100"))]

    def test_changed_only(self) -> None:
        """Same key, different ratio → (cid, before, after)."""
        cid = uuid.uuid4()
        existing = {cid: Decimal("50")}
        new = {cid: Decimal("60")}
        out = BOMService._diff_ratios(existing, new)
        assert out == [(cid, Decimal("50"), Decimal("60"))]

    def test_removed_only_skipped(self) -> None:
        """Removed rows ARE in changed_ratios with `after=None` (M7 Review)."""
        cid_removed = uuid.uuid4()
        cid_kept = uuid.uuid4()
        existing = {cid_removed: Decimal("40"), cid_kept: Decimal("60")}
        new = {cid_kept: Decimal("60")}
        out = BOMService._diff_ratios(existing, new)
        # L10 (Review): set iteration is now `sorted()` for stable order.
        # M7 (Review): removed rows are emitted with `after=None` so the
        # audit payload is self-describing (CR 1.1 lesson).
        assert out == [(cid_removed, Decimal("40"), None)]

    def test_mixed_add_change_remove(self) -> None:
        """Full diff — added + changed + removed (M7 Review)."""
        cid_add = uuid.uuid4()
        cid_change = uuid.uuid4()
        cid_remove = uuid.uuid4()
        cid_keep = uuid.uuid4()
        existing = {
            cid_change: Decimal("40"),
            cid_remove: Decimal("30"),
            cid_keep: Decimal("30"),
        }
        new = {
            cid_add: Decimal("20"),
            cid_change: Decimal("50"),
            cid_keep: Decimal("30"),
        }
        out = BOMService._diff_ratios(existing, new)
        # L10 (Review): set iteration is now `sorted()` for stable order.
        # M7 (Review): cid_remove is now emitted as (cid, Decimal('30'), None).
        out_set = set(out)
        assert (cid_add, None, Decimal("20")) in out_set
        assert (cid_change, Decimal("40"), Decimal("50")) in out_set
        assert (cid_remove, Decimal("30"), None) in out_set
        assert len(out) == 3


class TestIsUniqueBomViolation:
    """Defense-in-depth race condition check."""

    def test_recognizes_sqlstate_23505(self) -> None:
        """asyncpg-style: `.sqlstate == '23505'` + constraint_name match → True.

        M10 (Review): now requires the constraint name to match too, so an
        unrelated 23505 (e.g. another table's unique violation) is not
        misclassified as a BOM duplicate.
        """
        from sqlalchemy.exc import IntegrityError

        class _Orig:
            sqlstate = "23505"

            class diag:
                constraint_name = "uq_bom_lines_tenant_parent_child"

        err = IntegrityError("INSERT", {}, _Orig())  # type: ignore[arg-type]
        assert BOMService._is_unique_bom_violation(err) is True

    def test_recognizes_pgcode_23505(self) -> None:
        """psycopg2-style: `.pgcode == '23505'` + constraint_name match → True.

        M10 (Review): same as test_recognizes_sqlstate_23505 — the
        constraint name must also match.
        """
        from sqlalchemy.exc import IntegrityError

        class _Orig:
            pgcode = "23505"

            class diag:
                constraint_name = "uq_bom_lines_tenant_parent_child"

        err = IntegrityError("INSERT", {}, _Orig())  # type: ignore[arg-type]
        assert BOMService._is_unique_bom_violation(err) is True

    def test_recognizes_string_match(self) -> None:
        """Fallback — string match for `uq_bom_lines_tenant_parent_child`."""
        from sqlalchemy.exc import IntegrityError

        err = IntegrityError(
            "INSERT",
            {},
            Exception("duplicate key value violates unique constraint "
                      '"uq_bom_lines_tenant_parent_child"'),
        )  # type: ignore[arg-type]
        assert BOMService._is_unique_bom_violation(err) is True

    def test_rejects_other_sqlstate(self) -> None:
        """Different SQLSTATE (e.g. 23503 FK violation) → False."""
        from sqlalchemy.exc import IntegrityError

        class _Orig:
            sqlstate = "23503"

        err = IntegrityError("INSERT", {}, _Orig())  # type: ignore[arg-type]
        assert BOMService._is_unique_bom_violation(err) is False


# ── Capability matrix (AC #4) ──────────────────────────────────
def test_capability_bom_granted_to_manufacturing_industries() -> None:
    """AC #4 — Capability.BOM granted to manufacturing / service hybrids.

    service tenant cannot access BOM routes → 403 INDUSTRY_NOT_SUPPORTED.
    """
    from apps.api.core.capability import (
        Capability,
        _INDUSTRY_CAPABILITIES,
    )
    from packages.services.m0_onboarding.industry_menu import Industry

    # manufacturing + 2 service hybrids → have BOM
    assert Capability.BOM in _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING]
    assert Capability.BOM in _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING_SERVICE]
    assert Capability.BOM in _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING_SERVICE_OTHER]

    # pure service → does NOT have BOM
    assert Capability.BOM not in _INDUSTRY_CAPABILITIES[Industry.SERVICE]