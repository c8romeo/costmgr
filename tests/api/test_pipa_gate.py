"""tests.api.test_pipa_gate — pure unit tests for the PIPA gate env-flag.

Epic 1 회고 A3 + Epic 3 회고 A1 — operations kill-switch.

The PIPA gate is a 2-layer check:
  Layer 1: operations kill-switch (env-var `PIPA_REVIEW_COMPLETED=false`)
  Layer 2: per-tenant consent + region (Story 1.3)

These tests cover Layer 1 (the kill-switch) — pure unit tests with no DB
dependency. Layer 2 is covered by the existing Story 1.3 / test_ai_documents
tests (DB-backed, skip-gated).

The env-var is read at function call time, not module load, so tests
can monkey-patch `os.environ` without re-importing the module.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.core.pipa_gate import (
    PIPA_REVIEW_COMPLETED_ENV,
    PipaConsentMissingError,
    PipaReviewRequiredError,
    pipa_review_completed,
    require_pipa_review,
)


# ─────────────────────────────────────────────────────────────
# Pure helper tests — `pipa_review_completed()` env-var parsing
# ─────────────────────────────────────────────────────────────


def test_pipa_review_completed_unset_returns_true() -> None:
    """Default behavior: env-var unset → kill-switch OFF → return True.

    Backward compatible — existing deployments without the env-var
    set work as before (per-tenant check is the only gate).
    """
    os.environ.pop(PIPA_REVIEW_COMPLETED_ENV, None)
    assert pipa_review_completed() is True


def test_pipa_review_completed_true_returns_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-var set to 'true' → kill-switch OFF → return True."""
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "true")
    assert pipa_review_completed() is True


def test_pipa_review_completed_one_returns_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-var set to '1' → kill-switch OFF → return True."""
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "1")
    assert pipa_review_completed() is True


def test_pipa_review_completed_false_returns_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-var set to 'false' → kill-switch ON → return False.

    This is the operations kill-switch: legal review pending.
    """
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "false")
    assert pipa_review_completed() is False


def test_pipa_review_completed_zero_returns_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-var set to '0' → kill-switch ON → return False."""
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "0")
    assert pipa_review_completed() is False


def test_pipa_review_completed_mixed_case_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-var set to 'False' (mixed case) → kill-switch ON → return False.

    Operations often use mixed-case env values; we accept all common
    case variants of 'false' but NOT 'no', 'off', 'disabled' (those
    are ambiguous — operators should use explicit true/false).
    """
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "False")
    assert pipa_review_completed() is False
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "FALSE")
    assert pipa_review_completed() is False


def test_pipa_review_completed_arbitrary_string_returns_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env-var set to a non-recognized value → fail-OPEN (True).

    Conservative: unknown values are treated as ON. This prevents
    typos in env-vars from accidentally locking the system. Operators
    must use explicit 'false' / '0' to enable the kill-switch.
    """
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "yes")
    assert pipa_review_completed() is True
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "no")
    assert pipa_review_completed() is True
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "")
    # Empty string is treated as unset → True (fail-open)
    assert pipa_review_completed() is True


def test_pipa_review_completed_strips_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env-var with surrounding whitespace → stripped before comparison."""
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "  false  ")
    assert pipa_review_completed() is False
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "  true  ")
    assert pipa_review_completed() is True


# ─────────────────────────────────────────────────────────────
# Dependency tests — `require_pipa_review()` Layer 1 behavior
# ─────────────────────────────────────────────────────────────


def _make_tenant_context() -> MagicMock:
    """Build a TenantContext-like mock for the dependency call."""
    ctx = MagicMock()
    ctx.tenant_id = uuid.uuid4()
    return ctx


def test_require_pipa_review_kill_switch_on_raises_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env-var 'false' → gate raises PipaReviewRequiredError BEFORE per-tenant check.

    No DB call should occur (the kill-switch is the FIRST line of defense).
    The exception is mapped to 503 PIPA_REVIEW_REQUIRED by main.py handler.
    """
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "false")
    ctx = _make_tenant_context()
    session = MagicMock()  # should NOT be called

    with pytest.raises(PipaReviewRequiredError) as exc_info:
        asyncio.run(require_pipa_review(ctx=ctx, session=session))  # type: ignore[arg-type]

    assert exc_info.value.trace_id  # trace_id is set


def test_require_pipa_review_kill_switch_on_503_typed_envelope_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the exception carries the fields main.py handler reads."""
    monkeypatch.setenv(PIPA_REVIEW_COMPLETED_ENV, "0")
    ctx = _make_tenant_context()
    session = MagicMock()

    with pytest.raises(PipaReviewRequiredError) as exc_info:
        asyncio.run(require_pipa_review(ctx=ctx, session=session))  # type: ignore[arg-type]

    exc = exc_info.value
    assert hasattr(exc, "trace_id")
    assert isinstance(exc.trace_id, str) and len(exc.trace_id) > 0


def test_require_pipa_review_kill_switch_off_falls_through_to_tenant_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env-var unset → gate proceeds to per-tenant check (Layer 2).

    Without a valid tenant settings row, the per-tenant check raises
    PipaConsentMissingError (the existing 451 path). This verifies
    that Layer 1 does NOT block when kill-switch is OFF.

    SettingsService is lazy-imported inside `require_pipa_review`, so
    we patch the class in its source module to inject a mock that
    raises `TenantSettingsNotFoundError` (the 451 path).
    """
    os.environ.pop(PIPA_REVIEW_COMPLETED_ENV, None)
    ctx = _make_tenant_context()

    from apps.api.modules.m0_onboarding.services.settings_service import (
        SettingsService,
        TenantSettingsNotFoundError,
    )

    mock_service_instance = MagicMock()
    mock_service_instance.get_tenant_settings = AsyncMock(
        side_effect=TenantSettingsNotFoundError(tenant_id=ctx.tenant_id, trace_id="test")
    )
    mock_service_cls = MagicMock(return_value=mock_service_instance)

    monkeypatch.setattr(SettingsService, "__init__", lambda self, *a, **kw: None)
    monkeypatch.setattr(SettingsService, "get_tenant_settings", mock_service_instance.get_tenant_settings)

    with pytest.raises(PipaConsentMissingError) as exc_info:
        asyncio.run(require_pipa_review(ctx=ctx, session=MagicMock()))  # type: ignore[arg-type]
    assert exc_info.value.reason == "consent_missing"
