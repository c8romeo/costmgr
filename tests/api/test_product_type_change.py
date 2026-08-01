"""tests.api.test_product_type_change — type-change integrity guard tests.

Story 2.3 — Task 6.2.

DB-backed happy-path tests (POST/PATCH end-to-end) are deferred to
Story 0.5 (needs `pytest-postgresql` fixture). This file covers the
typed-exception contract (AD-15 §4) — the wire shape that downstream
handlers and frontends depend on.

Pattern: sync tests driver async work via `asyncio.run()` (the project's
established convention per `tests/rls/test_tenant_isolation.py`).
This avoids the `pytest-asyncio` plugin dependency.

Coverage:
- ProductTypeHasReferencesError carries product_id, requested_type,
  bom_count, ledger_count, total_count, trace_id.
- Same-type no-op PATCH returns row without raising.
- Mixed-field PATCH (name + type) emits one audit row covering both.
- AC #9 same-type idempotent no-op skips BOM count + audit.
- AC #4 parent-side references also count.
- ledger_count is always 0 (Epic 5 stub).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m1_baseline.services.product_service import (
    ProductImmutableFieldError,
    ProductTypeHasReferencesError,
)
from packages.services.m1_baseline.schemas import ProductType


# ── ProductTypeHasReferencesError ──────────────────────────────
def test_product_type_has_references_error_carries_counts() -> None:
    """AC #1 / 409 PRODUCT_TYPE_HAS_REFERENCES — error carries counts
    for the handler to echo in `details`."""
    product_id = uuid.uuid4()
    err = ProductTypeHasReferencesError(
        product_id=product_id,
        requested_type=ProductType.SERVICE,
        bom_count=3,
        ledger_count=0,
        trace_id="t-001",
    )
    assert err.product_id == product_id
    assert err.requested_type == ProductType.SERVICE
    assert err.bom_count == 3
    assert err.ledger_count == 0
    assert err.total_count == 3
    assert err.trace_id == "t-001"


def test_product_type_has_references_error_total_is_sum() -> None:
    """total_count = bom_count + ledger_count (eventually non-zero ledger)."""
    err = ProductTypeHasReferencesError(
        product_id=uuid.uuid4(),
        requested_type=ProductType.PRODUCT,
        bom_count=3,
        ledger_count=12,  # hypothetical Epic 5
        trace_id="t",
    )
    assert err.total_count == 15


def test_product_type_has_references_error_message_format() -> None:
    """Korean-aware messages are built by the handler; this asserts the
    exception contains the key facts so the handler can format."""
    product_id = uuid.uuid4()
    err = ProductTypeHasReferencesError(
        product_id=product_id,
        requested_type=ProductType.SERVICE,
        bom_count=3,
        ledger_count=0,
        trace_id="t",
    )
    msg = str(err)
    assert "3" in msg  # bom_count
    assert "service" in msg  # requested_type.value
    assert str(product_id) in msg


def test_product_type_has_references_error_with_zero_ledger() -> None:
    """AC #1 — ledger_count = 0 (Epic 5 stub)."""
    err = ProductTypeHasReferencesError(
        product_id=uuid.uuid4(),
        requested_type=ProductType.MATERIAL,
        bom_count=0,
        ledger_count=0,  # stub
        trace_id="t",
    )
    # total = 0 → would NOT raise in practice; the constructor still
    # allows it (defense-in-depth — the service only raises when total > 0)
    assert err.total_count == 0


# ── ProductImmutableFieldError regression ──────────────────────
def test_immutable_field_error_still_names_code() -> None:
    """Story 2.3 — ProductImmutableFieldError now ONLY handles `code`.
    Product_type removal is tested by service-level tests below."""
    err = ProductImmutableFieldError(field="code", trace_id="t")
    assert err.field == "code"


# ── Mock-session service tests ─────────────────────────────────
# Mocking the AsyncSession lets us test the type-change logic without
# a real DB. The `scalar_one()` call returns the count, then we verify
# the service raises the right exception with the right attributes.


def _make_product_row(product_id: uuid.UUID, product_type: ProductType) -> MagicMock:
    """Build a Product-like MagicMock for the load query result."""
    row = MagicMock()
    row.id = product_id
    row.tenant_id = uuid.uuid4()
    row.product_type = product_type.value
    row.code = "MAT-0042"
    row.name = "원목"
    row.unit = "kg"
    row.unit_cost_krw = 1000
    row.unit_cost_usd = Decimal("0.75")
    row.description = None
    row.is_active = True
    row.created_at = datetime.now(tz=UTC)
    row.updated_at = datetime.now(tz=UTC)
    return row


def _build_session_with_results(*results: Any) -> AsyncMock:
    """Build an AsyncSession stub that returns the given results in order.

    Use this for service tests where multiple `session.execute()` calls
    happen (advisory lock + load + BOM count + audit insert).
    """
    session = AsyncMock()
    call_count = {"n": 0}

    async def execute_side_effect(_stmt: Any) -> Any:
        idx = call_count["n"]
        call_count["n"] += 1
        return results[idx]

    session.execute = MagicMock(side_effect=execute_side_effect)
    return session


def _result_with_value(value: Any) -> MagicMock:
    """Build a `Result` mock that returns `value` from scalar_one() / scalar_one_or_none()."""
    r = MagicMock()
    r.scalar_one = MagicMock(return_value=value)
    r.scalar_one_or_none = MagicMock(return_value=value)
    return r


def _advisory_lock_result() -> MagicMock:
    """Build a no-op result for the advisory lock call (D2 — first
    `session.execute()` in `update_product`).

    The advisory lock SQL is `select(func.pg_advisory_xact_lock(...))`
    which returns a scalar; the service ignores the value. Mock just
    needs to return something with a `scalar_one()` for completeness.
    """
    return _result_with_value(None)


# ── Async test driver — asyncio.run pattern ─────────────────────
def _run(coro: Any) -> Any:
    """Helper: run a coroutine via asyncio.run (the project's convention)."""
    return asyncio.run(coro)


def test_update_product_with_references_raises_typed_error() -> None:
    """AC #1 — BOM count > 0 → ProductTypeHasReferencesError.

    D2 (post-review): service now acquires an advisory lock BEFORE the
    load query — first result is the lock (no-op value), then load,
    then BOM count (single OR-merged query per P4).
    """
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    session = _build_session_with_results(
        _advisory_lock_result(),  # 1: D2 advisory lock
        _result_with_value(row),  # 2: load product
        _result_with_value(3),  # 3: BOM count (P4 single OR-merged, 3 refs)
    )
    service = ProductService(session, trace_id="t-001")

    async def go() -> None:
        body = ProductUpdateRequest(product_type=ProductType.SEMI_PRODUCT)
        with pytest.raises(ProductTypeHasReferencesError) as exc_info:
            await service.update_product(
                tenant_id=uuid.uuid4(),
                actor_id=uuid.uuid4(),
                product_id=product_id,
                body=body,
            )
        err = exc_info.value
        assert err.product_id == product_id
        assert err.requested_type == ProductType.SEMI_PRODUCT
        assert err.bom_count == 3
        assert err.ledger_count == 0
        assert err.total_count == 3
        assert err.trace_id == "t-001"

    _run(go())


def test_update_product_with_references_rolls_back() -> None:
    """AC #1 — when the guard rejects, no row mutation, no audit row."""
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
        _result_with_value(1),  # single count > 0 → reject
    )
    service = ProductService(session, trace_id="t-rollback")

    async def go() -> None:
        body = ProductUpdateRequest(product_type=ProductType.SERVICE)
        with pytest.raises(ProductTypeHasReferencesError):
            await service.update_product(
                tenant_id=uuid.uuid4(),
                actor_id=uuid.uuid4(),
                product_id=product_id,
                body=body,
            )

    _run(go())

    # The row's product_type was NOT mutated.
    assert row.product_type == "material"


def test_update_product_zero_references_allows_change() -> None:
    """AC #2 — BOM count = 0 + ledger count = 0 → allow the change."""
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
        _result_with_value(0),  # BOM count = 0 → allow
    )
    service = ProductService(session, trace_id="t-allow")

    async def go() -> None:
        body = ProductUpdateRequest(product_type=ProductType.SEMI_PRODUCT)
        await service.update_product(
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            product_id=product_id,
            body=body,
        )

    _run(go())

    # The row's product_type WAS mutated.
    assert row.product_type == "semi_product"


def test_update_product_same_type_is_noop() -> None:
    """AC #9 — same-type PATCH skips BOM count + audit (idempotent no-op).

    D2 (post-review): service now always issues an advisory lock first,
    so `call_count == 2` (lock + load). The BOM count is correctly
    skipped because the type-change guard short-circuits.
    """
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    # Only the lock + load queries are executed. Same-type path = no BOM count queries.
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
    )
    service = ProductService(session, trace_id="t-noop")

    async def go() -> None:
        body = ProductUpdateRequest(product_type=ProductType.MATERIAL)  # same
        result = await service.update_product(
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            product_id=product_id,
            body=body,
        )
        assert result is row

    _run(go())

    # Lock + load ran — no BOM count queries.
    assert session.execute.call_count == 2
    # No audit row was added.
    session.add.assert_not_called()


def test_update_product_bom_parent_count_counts() -> None:
    """AC #4 — parent-side references also count toward the guard.

    P4 (post-review): single OR-merged query returns the SUM
    (parent + child). For this test, parent side = 5 → bom_count = 5.
    """
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.PRODUCT)
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
        _result_with_value(5),  # 5 BOMs as parent (single OR-merged count)
    )
    service = ProductService(session, trace_id="t-parent")

    async def go() -> None:
        body = ProductUpdateRequest(product_type=ProductType.SEMI_PRODUCT)
        with pytest.raises(ProductTypeHasReferencesError) as exc_info:
            await service.update_product(
                tenant_id=uuid.uuid4(),
                actor_id=uuid.uuid4(),
                product_id=product_id,
                body=body,
            )
        assert exc_info.value.bom_count == 5
        assert exc_info.value.total_count == 5

    _run(go())


def test_update_product_ledger_count_is_zero_stub() -> None:
    """AC #1 — ledger_count is always 0 (Epic 5 placeholder)."""
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
        _result_with_value(2),  # bom_count > 0 → reject; ledger stub is always 0
    )
    service = ProductService(session, trace_id="t-ledger")

    async def go() -> None:
        body = ProductUpdateRequest(product_type=ProductType.SERVICE)
        with pytest.raises(ProductTypeHasReferencesError) as exc_info:
            await service.update_product(
                tenant_id=uuid.uuid4(),
                actor_id=uuid.uuid4(),
                product_id=product_id,
                body=body,
            )
        assert exc_info.value.ledger_count == 0

    _run(go())


def test_update_product_code_still_immutable() -> None:
    """Regression — `code` is still strictly immutable (403 PRODUCT_IMMUTABLE_FIELD).

    D2 (post-review): service acquires the advisory lock BEFORE the
    code check. Even for `code` PATCHes, the lock is held. Result
    tuple = lock + load.
    """
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
    )
    service = ProductService(session, trace_id="t-code")

    async def go() -> None:
        body = ProductUpdateRequest(code="MAT-9999")
        with pytest.raises(ProductImmutableFieldError) as exc_info:
            await service.update_product(
                tenant_id=uuid.uuid4(),
                actor_id=uuid.uuid4(),
                product_id=product_id,
                body=body,
            )
        assert exc_info.value.field == "code"

    _run(go())


def test_update_product_mixed_type_change_with_name_emits_one_audit() -> None:
    """AC #8 — when name + product_type both change, ONE audit row covers both."""
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
        _result_with_value(0),  # BOM count = 0 → allow
    )
    captured_payload: dict[str, Any] = {}
    captured_action: str | None = None

    def capture(obj: Any) -> None:
        # Capture the audit row's payload. The emit_audit helper instantiates
        # AuditLog(**payload) and adds via session.add().
        nonlocal captured_action
        if hasattr(obj, "action") and hasattr(obj, "payload"):
            payload = obj.payload
            captured_action = obj.action
            if isinstance(payload, dict):
                captured_payload.update(payload)

    session.add = MagicMock(side_effect=capture)
    service = ProductService(session, trace_id="t-mixed")

    async def go() -> None:
        body = ProductUpdateRequest(
            name="원목(수정)",
            product_type=ProductType.SEMI_PRODUCT,
        )
        await service.update_product(
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            product_id=product_id,
            body=body,
        )

    _run(go())

    # Both fields mutated.
    assert row.name == "원목(수정)"
    assert row.product_type == "semi_product"

    # Audit payload carries both fields in changed_fields.
    assert "changed_fields" in captured_payload
    assert "name" in captured_payload["changed_fields"]
    assert "product_type" in captured_payload["changed_fields"]
    assert captured_payload["before"]["name"] == "원목"
    assert captured_payload["after"]["name"] == "원목(수정)"
    assert captured_payload["before"]["product_type"] == "material"
    assert captured_payload["after"]["product_type"] == "semi_product"

    # P2 (post-review): mixed PATCH (type + other field) → action='product_updated'.
    # AC #2 / AC #8 say: type-only PATCH gets 'product_type_changed', mixed
    # PATCH gets 'product_updated' with `product_type` in `changed_fields`.
    assert captured_action == "product_updated", (
        f"Mixed PATCH must emit action='product_updated', got {captured_action!r}"
    )


def test_update_product_type_change_audit_payload_before_after() -> None:
    """AC #2 — audit row records `before`/`after` for product_type only.

    P2 (post-review): also assert `action='product_type_changed'` for
    type-only PATCH (single-field change). The previous assertion only
    checked payload shape — the action name silently defaulted to
    'product_updated' even for type-only changes.
    """
    from apps.api.modules.m1_baseline.services.product_service import ProductService
    from apps.api.modules.m1_baseline.schemas import ProductUpdateRequest

    product_id = uuid.uuid4()
    row = _make_product_row(product_id, ProductType.MATERIAL)
    session = _build_session_with_results(
        _advisory_lock_result(),
        _result_with_value(row),
        _result_with_value(0),  # BOM count = 0 → allow
    )
    captured_payload: dict[str, Any] = {}
    captured_action: str | None = None

    def capture(obj: Any) -> None:
        nonlocal captured_action
        if hasattr(obj, "action") and hasattr(obj, "payload"):
            payload = obj.payload
            captured_action = obj.action
            if isinstance(payload, dict):
                captured_payload.update(payload)

    session.add = MagicMock(side_effect=capture)
    service = ProductService(session, trace_id="t-payload")

    async def go() -> None:
        body = ProductUpdateRequest(product_type=ProductType.SERVICE)
        await service.update_product(
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            product_id=product_id,
            body=body,
        )

    _run(go())

    assert "changed_fields" in captured_payload
    assert "product_type" in captured_payload["changed_fields"]
    assert captured_payload["before"]["product_type"] == "material"
    assert captured_payload["after"]["product_type"] == "service"

    # P2 (post-review): type-only PATCH → action='product_type_changed'.
    assert captured_action == "product_type_changed", (
        f"Type-only PATCH must emit action='product_type_changed', got {captured_action!r}"
    )
