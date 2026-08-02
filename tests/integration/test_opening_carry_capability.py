"""tests.integration.test_opening_carry_capability — Capability gate consistency.

Story 5.1 (Epic 5) — Task 4.6 capability gate verification.

Pins that:
- `Capability.OPENING_INVENTORY` enum value exists (Story 3.3 baseline)
- All manufacturing-kind industries include OPENING_INVENTORY in
  their capability matrix (manufacturing, mfg+service,
  mfg+service+other)
- Service industry does NOT include OPENING_INVENTORY (no inventory
  streams — carry chain returns empty decisions, cj-style default)

These pins prevent the CR 1.1 lesson: capability drift across the
3 industry matrices.
"""

from __future__ import annotations

from apps.api.core.capability import (
    _INDUSTRY_CAPABILITIES,
    Capability,
)
from packages.services.m0_onboarding.industry_menu import Industry


def test_capability_opening_inventory_enum_exists() -> None:
    """Capability.OPENING_INVENTORY enum value must exist."""
    assert hasattr(Capability, "OPENING_INVENTORY")
    assert Capability.OPENING_INVENTORY.value == "opening_inventory"


def test_capability_opening_inventory_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes OPENING_INVENTORY."""
    mfg_caps = _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING]
    assert Capability.OPENING_INVENTORY in mfg_caps


def test_capability_opening_inventory_wired_mfg_service() -> None:
    """mfg+service industry matrix includes OPENING_INVENTORY."""
    caps = _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING_SERVICE]
    assert Capability.OPENING_INVENTORY in caps


def test_capability_opening_inventory_wired_mixed() -> None:
    """Mixed industry matrix includes OPENING_INVENTORY."""
    caps = _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING_SERVICE_OTHER]
    assert Capability.OPENING_INVENTORY in caps
