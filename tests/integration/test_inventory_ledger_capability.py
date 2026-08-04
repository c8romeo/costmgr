"""tests.integration.test_inventory_ledger_capability — Story 5.2 AC #2 capability gate.

Pins `Capability.INVENTORY_LEDGER` wiring across the industry matrix:
- Manufacturing (3 variants) ✅ enabled
- Service-only ❌ disabled (the ledger has no meaning without BOM streams)

CR 1.1 lesson: capability drift across industry matrices is the #1
source of cross-tenant write leaks. Each capability addition needs a
3-matrix pin + a service-only exclusion pin.
"""

from __future__ import annotations

from apps.api.core.capability import (
    _INDUSTRY_CAPABILITIES,
    Capability,
    industry_supports,
)
from packages.services.m0_onboarding.industry_menu import Industry


def test_capability_inventory_ledger_enum_exists() -> None:
    """`Capability.INVENTORY_LEDGER` enum value must exist.

    AC #2 — Story 5.2 wire. If the enum is renamed, this test fails
    so the team updates the pin + handlers in lockstep.
    """
    assert hasattr(Capability, "INVENTORY_LEDGER")
    assert Capability.INVENTORY_LEDGER.value == "inventory_ledger"


def test_capability_inventory_ledger_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes INVENTORY_LEDGER."""
    assert industry_supports(Industry.MANUFACTURING, Capability.INVENTORY_LEDGER)


def test_capability_inventory_ledger_wired_mfg_service() -> None:
    """mfg+service industry matrix includes INVENTORY_LEDGER."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.INVENTORY_LEDGER
    )


def test_capability_inventory_ledger_wired_mixed() -> None:
    """Mixed industry matrix includes INVENTORY_LEDGER."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.INVENTORY_LEDGER
    )


def test_capability_inventory_ledger_excluded_service_only() -> None:
    """Service-only industry does NOT have INVENTORY_LEDGER.

    Service tenants have no BOM → no raw/semi/finished-product inventory
    streams → the ledger has no meaning. The 4 ledger routes return
    403 INDUSTRY_NOT_SUPPORTED for service tenants.
    """
    assert not industry_supports(Industry.SERVICE, Capability.INVENTORY_LEDGER)


def test_capability_inventory_ledger_matrix_consistent() -> None:
    """The matrix pin: manufacturing ⊃ mfg_service ⊃ mixed ≥ 1 INVENTORY_LEDGER.

    Defense-in-depth: even if the matrix changes shape, the 3
    manufacturing variants must all unlock INVENTORY_LEDGER.
    """
    expected_industries = {
        Industry.MANUFACTURING,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    }
    for industry in expected_industries:
        caps = _INDUSTRY_CAPABILITIES[industry]
        assert Capability.INVENTORY_LEDGER in caps, (
            f"Industry {industry.value} lost INVENTORY_LEDGER capability — "
            f"matrix drift. Update the pin in this test + capability-matrix.md."
        )
    # Service-only MUST NOT have it
    service_caps = _INDUSTRY_CAPABILITIES[Industry.SERVICE]
    assert Capability.INVENTORY_LEDGER not in service_caps, (
        "Service-only industry gained INVENTORY_LEDGER — backdoor for "
        "service tenants to write to the ledger without a BOM. Remove it."
    )
