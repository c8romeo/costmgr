"""tests.api.core.test_phase_5_capability_integration — MULTI_REGION_* industry grants tests.

Phase 5 (cj-style 75번째 wire) — AC #6.1~#6.3 verbatim + CR 12-1 L4 precedent.
Verifies MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER are industry-agnostic
(granted to all 4 industries).
"""

from __future__ import annotations


class TestMultiRegionBackupCapability:
    """MULTI_REGION_BACKUP industry-agnostic grant verification."""

    def test_capability_enum_declared(self) -> None:
        from apps.api.core.capability import Capability

        assert hasattr(Capability, "MULTI_REGION_BACKUP")
        assert Capability.MULTI_REGION_BACKUP.value == "multi_region_backup"

    def test_capability_granted_to_all_4_industries(self) -> None:
        from apps.api.core.capability import (
            Capability,
            Industry,
            _INDUSTRY_CAPABILITIES,
        )

        for industry in (
            Industry.MANUFACTURING,
            Industry.SERVICE,
            Industry.MULTI_INDUSTRY,
            Industry.MULTI_INDUSTRY_OTHER,
        ):
            caps = _INDUSTRY_CAPABILITIES[industry]
            assert Capability.MULTI_REGION_BACKUP in caps, (
                f"MULTI_REGION_BACKUP not granted to {industry.value}"
            )


class TestMultiRegionFailoverCapability:
    """MULTI_REGION_FAILOVER industry-agnostic grant verification."""

    def test_capability_enum_declared(self) -> None:
        from apps.api.core.capability import Capability

        assert hasattr(Capability, "MULTI_REGION_FAILOVER")
        assert Capability.MULTI_REGION_FAILOVER.value == "multi_region_failover"

    def test_capability_granted_to_all_4_industries(self) -> None:
        from apps.api.core.capability import (
            Capability,
            Industry,
            _INDUSTRY_CAPABILITIES,
        )

        for industry in (
            Industry.MANUFACTURING,
            Industry.SERVICE,
            Industry.MULTI_INDUSTRY,
            Industry.MULTI_INDUSTRY_OTHER,
        ):
            caps = _INDUSTRY_CAPABILITIES[industry]
            assert Capability.MULTI_REGION_FAILOVER in caps, (
                f"MULTI_REGION_FAILOVER not granted to {industry.value}"
            )


class TestCapabilityDependency:
    """Phase 5 — T6 — capability dep module imports cleanly."""

    def test_capability_dependencies_module_imports(self) -> None:
        from apps.api.dependencies import capability

        assert hasattr(capability, "require_tenant_idp_management")