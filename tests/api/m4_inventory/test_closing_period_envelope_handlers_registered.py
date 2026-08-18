"""tests.api.m4_inventory.test_closing_period_envelope_handlers_registered — smoke-fix T1.

5 typed exceptions from ClosingPeriodService get AD-15 §4 envelope handlers
in apps/api/main.py (CR 11-2/11-3 lesson — no default FastAPI 500 for
typed service exceptions).

Smoke 2026-08-18 revealed: ClosingPeriodAlreadyClosedError → 500 instead
of 409 AD-15 envelope (closing-period/confirm second-click on an already
closed period bubbled up as 500). Same audit-blind pattern repeats for the
other 4 typed exceptions below — all wired to their canonical HTTP code.

Mapping:
- ClosingPeriodAlreadyClosedError       → 409 ALREADY_CLOSED
- ClosingPeriodBlockedError             → 409 CLOSING_PERIOD_BLOCKED
- ClosingPeriodEmptyPeriodError         → 409 EMPTY_PERIOD
- ClosingPeriodSnapshotInconsistencyError → 409 CLOSING_PERIOD_SNAPSHOT_INCONSISTENCY
- ClosingPeriodAuditEmitError           → 500 CLOSING_PERIOD_AUDIT_EMIT_ERROR
"""

from __future__ import annotations

from apps.api.main import app as main_app


def _registered_exception_classes() -> set[type]:
    """Collect the set of exception classes that have handlers registered.

    FastAPI stores exception handlers in `app.exception_handlers` as a
    dict keyed by exception class (or `int` for status-code handlers).
    """
    return set(main_app.exception_handlers.keys())


def test_closing_period_already_closed_handler_registered() -> None:
    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodAlreadyClosedError,
    )

    assert ClosingPeriodAlreadyClosedError in _registered_exception_classes()


def test_closing_period_blocked_handler_registered() -> None:
    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodBlockedError,
    )

    assert ClosingPeriodBlockedError in _registered_exception_classes()


def test_closing_period_empty_period_handler_registered() -> None:
    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodEmptyPeriodError,
    )

    assert ClosingPeriodEmptyPeriodError in _registered_exception_classes()


def test_closing_period_snapshot_inconsistency_handler_registered() -> None:
    from apps.api.modules.m6_verification.services.closing_period_snapshot_verifier import (
        ClosingPeriodSnapshotInconsistencyError,
    )

    assert (
        ClosingPeriodSnapshotInconsistencyError
        in _registered_exception_classes()
    )


def test_closing_period_audit_emit_handler_registered() -> None:
    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodAuditEmitError,
    )

    assert ClosingPeriodAuditEmitError in _registered_exception_classes()


def test_closing_period_handlers_return_ad15_envelope_shape() -> None:
    """Smoke 2026-08-18 target: closing-period/confirm second-click → 409 with
    `{code, message_ko, details, trace_id}` (AD-15 §4 envelope).

    Direct handler invocation (no DB needed) to verify the envelope shape
    matches the contract.
    """
    import uuid

    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodAlreadyClosedError,
    )

    handler = main_app.exception_handlers[ClosingPeriodAlreadyClosedError]
    exc = ClosingPeriodAlreadyClosedError(
        tenant_id=uuid.uuid4(),
        period_key="2026-08",
        finalized_at="2026-08-16T10:48:34+00:00",
        trace_id="test-trace",
    )
    response = _invoke_handler_sync(handler, exc)

    assert response.status_code == 409
    body = _response_body(response)
    assert body["code"] == "ALREADY_CLOSED"
    assert body["message_ko"] == "이미 마감되었습니다"
    assert body["details"]["period_key"] == "2026-08"
    assert body["details"]["finalized_at"] == "2026-08-16T10:48:34+00:00"
    assert body["trace_id"] == "test-trace"


# ── tiny sync helpers (no TestClient needed for direct handler invocation) ──


def _invoke_handler_sync(handler, exc):
    """Invoke an exception handler and return its JSONResponse.

    The handler is registered with a 2-arg signature `(request, exc)`. We
    pass a None `request` placeholder — the registered handlers in main.py
    do not access `request.url` or `request.headers`, only `exc` fields.
    """
    import asyncio

    return asyncio.run(handler(None, exc))


def _response_body(response) -> dict:
    """Return the JSON body of a Starlette Response as a dict."""
    import json

    return json.loads(response.body)
