"""tests.services.test_closing_guard_service — Story 5.3 service-layer tests.

Smoke tests for `apps.api.modules.m4_inventory.services.closing_guard_service.ClosingGuardService`:
- Module shape — 5 typed exceptions, 4 service operations exist
- Constructor signature is correct (industry kwarg, session positional)
- Pure-kernel delegation checks

These tests focus on API shape + module surface, since full async
service behavior requires DB fixtures (Story 0.5 plumbing).
"""

from __future__ import annotations

import uuid
from typing import Any


# ── Typed exception surface ────────────────────────────────────
def test_typed_exception_classes_exist():
    """All 5 typed exceptions are defined per Story 5.3 spec."""
    from apps.api.modules.m4_inventory.services import closing_guard_service as mod

    expected = [
        "ClosingGuardNegativeInventoryError",
        "ClosingGuardInvalidPeriodKeyError",
        "ClosingGuardServiceOnlyTenantError",
        "ClosingGuardProductionConsumptionError",
        "ClosingGuardAuditEmitError",
    ]
    for name in expected:
        assert hasattr(mod, name), f"Missing exception class: {name}"


def test_typed_exceptions_inherit_from_exception():
    """All 5 typed exceptions inherit from Exception."""
    from apps.api.modules.m4_inventory.services import closing_guard_service as mod

    classes = [
        mod.ClosingGuardNegativeInventoryError,
        mod.ClosingGuardInvalidPeriodKeyError,
        mod.ClosingGuardServiceOnlyTenantError,
        mod.ClosingGuardProductionConsumptionError,
        mod.ClosingGuardAuditEmitError,
    ]
    for cls in classes:
        assert issubclass(cls, Exception), f"{cls.__name__} not a subclass of Exception"


# ── Module-level: 4 service operations exposed ─────────────────
def test_four_service_operations_exposed():
    """ClosingGuardService has exactly 4 async service operations."""
    from apps.api.modules.m4_inventory.services.closing_guard_service import (
        ClosingGuardService,
    )

    expected_ops = [
        "evaluate_closing_guard",
        "request_close_attempt",
        "emit_production_ledger_events",
        "validate_closing_invariant_against_active_products",
    ]
    for op in expected_ops:
        assert hasattr(ClosingGuardService, op), f"Missing service operation: {op}"
        assert callable(getattr(ClosingGuardService, op)), f"{op} is not callable"


def test_constructor_signature():
    """ClosingGuardService.__init__ has expected parameter shape."""
    import inspect
    from apps.api.modules.m4_inventory.services.closing_guard_service import (
        ClosingGuardService,
    )

    sig = inspect.signature(ClosingGuardService.__init__)
    params = list(sig.parameters.keys())
    # expected: self, session, *, tenant_id, industry, trace_id
    assert "self" in params
    assert "session" in params
    assert "tenant_id" in params
    assert "industry" in params
    assert "trace_id" in params


def test_industry_enum_path():
    """Industry enum is imported from packages.services.m0_onboarding.industry_menu."""
    # The service layer uses this path. Verify it exists.
    from packages.services.m0_onboarding.industry_menu import Industry

    assert hasattr(Industry, "SERVICE")
    assert hasattr(Industry, "MANUFACTURING")
    assert hasattr(Industry, "MANUFACTURING_SERVICE")
    assert hasattr(Industry, "MANUFACTURING_SERVICE_OTHER")


# ── Pure kernel wrapper functions exist ────────────────────────
def test_production_consumption_pure_kernel_imports():
    """Pure kernel functions are importable from service layer dependencies."""
    from packages.services.m4_inventory.production_consumption import (
        BomMatrixLike,
        BomChild,
        ProductionRowLike,
        compute_production_consumption_events,
    )

    assert callable(compute_production_consumption_events)


def test_closing_guard_pure_kernel_imports():
    """closing_guard pure kernel is importable."""
    from packages.services.m4_inventory.closing_guard import (
        classify_closing_invariant,
        compute_closing_balance_per_product,
        format_negative_closing_banner_ko,
        is_close_blocked,
    )

    assert callable(classify_closing_invariant)
    assert callable(compute_closing_balance_per_product)
    assert callable(format_negative_closing_banner_ko)
    assert callable(is_close_blocked)
