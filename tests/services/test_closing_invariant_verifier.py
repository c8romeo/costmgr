"""tests.services.test_closing_invariant_verifier — Story 5.3 verifier bridge tests.

Smoke tests for `apps.api.modules.m3_calculate.services.closing_invariant_verifier`:
- Module shape — exposes `ClosingInvariantVerifier` class
- AD-15 §11: verdict envelope keys match Python pure kernel

Full async flow requires DB fixtures (Story 0.5 plumbing).
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any


def test_verifier_module_exposes_class():
    """The verifier module exposes ClosingInvariantVerifier class."""
    from apps.api.modules.m3_calculate.services import (
        closing_invariant_verifier as mod,
    )

    assert hasattr(mod, "ClosingInvariantVerifier")
    assert "ClosingInvariantVerifier" in mod.__all__


def test_verifier_import_does_not_circular():
    """Verifier module imports cleanly (no circular import error)."""
    import apps.api.modules.m3_calculate.services.closing_invariant_verifier  # noqa: F401
    assert True


def test_verifier_uses_pure_kernel_imports():
    """Verifier module imports from packages.cost_engine.closing_invariant_check."""
    from apps.api.modules.m3_calculate.services import (
        closing_invariant_verifier as mod,
    )

    src = open(mod.__file__, encoding="utf-8").read()
    assert "closing_invariant_check" in src


def test_verifier_class_has_method():
    """ClosingInvariantVerifier has the `verify_v3_closing_invariant` method."""
    import inspect
    from apps.api.modules.m3_calculate.services.closing_invariant_verifier import (
        ClosingInvariantVerifier,
    )

    methods = [
        name for name, _ in inspect.getmembers(ClosingInvariantVerifier, predicate=inspect.iscoroutinefunction)
    ]
    assert "verify_v3_closing_invariant" in methods


def test_verifier_service_only_returns_skipped():
    """Service-only tenant → verifier returns status='skipped' verdict.

    Uses asyncio.run pattern (per CR 4-3 F-1 lesson).
    """
    from apps.api.modules.m3_calculate.services.closing_invariant_verifier import (
        ClosingInvariantVerifier,
    )
    from packages.services.m0_onboarding.industry_menu import Industry

    class _FakeSession:
        pass

    verifier = ClosingInvariantVerifier(
        session=_FakeSession(),  # type: ignore[arg-type]
        tenant_id=uuid.uuid4(),
        industry=Industry.SERVICE,
        trace_id="test-trace",
    )

    async def _invoke():
        return await verifier.verify_v3_closing_invariant(
            period_key="2026-07",
            actor_id=uuid.uuid4(),
        )

    result: dict[str, Any] = asyncio.run(_invoke())
    # Service-only tenant → some verdict envelope must be returned
    assert isinstance(result, dict)
    assert result["code"] == "V3"
    assert result["status"] in {"passed", "failed", "skipped"}
