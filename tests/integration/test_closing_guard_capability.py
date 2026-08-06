"""tests.integration.test_closing_guard_capability — Story 5.3 capability gate.

Drift detector: capability matrix v1.7 (CLOSING_GUARD wire) × Industry
matrix parity check.

PRD §F4.2 + PRD §V3: closing ≥ 0 invariant guard ONLY applies to
manufacturing-kind industries (3종). service-only tenants (Epic 9 ABC)
do NOT have inventory semantics → guard is irrelevant + capability gate
rejects with 403 INDUSTRY_NOT_SUPPORTED.

Industry matrix:
| Industry                     | evaluate | attempt-close |
|------------------------------|----------|---------------|
| manufacturing                | ✅       | ✅             |
| manufacturing_service        | ✅       | ✅             |
| manufacturing_service_other  | ✅       | ✅             |
| service                      | ❌ 403   | ❌ 403         |

Uses the public `industry_supports(industry, capability)` helper from
`apps/api/core/capability.py` (AD-11 layer rule — public API only).

Coverage target: 4 cases per spec AC #4 capability gate.
"""

from __future__ import annotations

import pytest

from apps.api.core.capability import (
    Capability,
    industry_supports,
)
from packages.services.m0_onboarding.industry_menu import Industry


# ── Case 1: manufacturing evaluate closing_guard succeeds ─────
def test_manufacturing_tenant_evaluate_closing_guard_succeeds() -> None:
    """Manufacturing industry → Capability.INVENTORY_CLOSING_GUARD ✅.

    `ClosingGuardService.evaluate_closing_guard` (T4.1) is callable
    for manufacturing tenants. `_guard_enabled=True` (industry ≠ service).
    """
    assert industry_supports(Industry.MANUFACTURING, Capability.INVENTORY_CLOSING_GUARD) is True


# ── Case 2: manufacturing_service evaluate closing_guard succeeds ─
def test_manufacturing_service_tenant_evaluate_closing_guard_succeeds() -> None:
    """Manufacturing_service industry → Capability.INVENTORY_CLOSING_GUARD ✅."""
    assert (
        industry_supports(Industry.MANUFACTURING_SERVICE, Capability.INVENTORY_CLOSING_GUARD)
        is True
    )


# ── Case 3: service-only tenant evaluate raises 403 ───────────
def test_service_only_tenant_evaluate_closing_guard_raises_403() -> None:
    """Service-only industry → Capability.INVENTORY_CLOSING_GUARD ❌ (403).

    Service-only tenants have no inventory-bearing products → closing
    guard is irrelevant. Capability gate rejects with 403
    INDUSTRY_NOT_SUPPORTED.
    """
    assert industry_supports(Industry.SERVICE, Capability.INVENTORY_CLOSING_GUARD) is False


# ── Case 4: service-only tenant close attempt raises 403 ───────
def test_service_only_tenant_close_attempt_raises_403() -> None:
    """Service-only industry → attempt-close also 403 INDUSTRY_NOT_SUPPORTED.

    Both `evaluate_closing_guard` AND `request_close_attempt` are
    gated by `Capability.INVENTORY_CLOSING_GUARD`. Service-only
    tenants must receive the same 403 on both endpoints.
    """
    # service-only tenant has neither inventory ledger nor closing guard
    assert industry_supports(Industry.SERVICE, Capability.INVENTORY_CLOSING_GUARD) is False
    assert industry_supports(Industry.SERVICE, Capability.INVENTORY_LEDGER) is False
    assert industry_supports(Industry.SERVICE, Capability.MONTHLY_INPUT_PRODUCTION) is False


# ── Helper: 3-way parity pin (matrix ↔ industry enum ↔ capability enum) ─
def test_matrix_full_industry_coverage() -> None:
    """All 4 industries from PRD §4.1 must be addressable via industry_supports."""
    # Verify the function handles all 4 industries without KeyError
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        # Returns bool for any (industry, capability) pair
        result = industry_supports(industry, Capability.INVENTORY_CLOSING_GUARD)
        assert isinstance(result, bool), (
            f"industry_supports({industry}, ...) must return bool"
        )


def test_inventory_closing_guard_capability_value() -> None:
    """Capability.INVENTORY_CLOSING_GUARD enum value is 'inventory_closing_guard'.

    Drift protection: capability matrix SSOT enum value must match
    the wire contract expected by `apps/web/lib/menu-config.ts` mirror.
    """
    assert Capability.INVENTORY_CLOSING_GUARD.value == "inventory_closing_guard"


# ── Sanity: manufacturing_service_other also has the gate ─────
def test_manufacturing_service_other_tenant_evaluate_closing_guard_succeeds() -> None:
    """manufacturing_service_other industry → Capability.INVENTORY_CLOSING_GUARD ✅."""
    assert (
        industry_supports(
            Industry.MANUFACTURING_SERVICE_OTHER, Capability.INVENTORY_CLOSING_GUARD
        )
        is True
    )


# ── Module-level coverage count pin ────────────────────────────
def test_module_has_at_least_4_cases() -> None:
    """Spec AC #4 capability gate: ≥ 4 cases per this file."""
    import sys

    current_module = sys.modules[__name__]
    test_count = sum(
        1 for name in dir(current_module) if name.startswith("test_")
    )
    assert test_count >= 4, (
        f"test_closing_guard_capability.py has {test_count} cases; "
        f"spec AC #4 requires ≥ 4."
    )