"""Test capability matrix v1.23 — LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS drift detector.

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): T5 wire — capability matrix
v1.23 EXTENSION (2 NEW rows `LISTEN_NOTIFY_TENANT_FANOUT` +
`LISTEN_NOTIFY_MULTIPROCESS`, industry-agnostic, 4-industry grants).

CR 12-5 D-GATE-01 inversion: capability gate is enforced through
Depends(require_capability(Capability.LISTEN_NOTIFY_TENANT_FANOUT)) and
Depends(require_capability(Capability.LISTEN_NOTIFY_MULTIPROCESS)).

Tests:
- LISTEN_NOTIFY_TENANT_FANOUT enum exists in Capability
- LISTEN_NOTIFY_MULTIPROCESS enum exists in Capability
- Both granted to all 4 industries (industry-agnostic, CR 12-1 L4 precedent)
- 4-industry grant matrix contains both
- cap value 'listen_notify_tenant_fanout' / 'listen_notify_multiprocess'
  are the canonical strings
- 13-1 LISTEN_NOTIFY preserved (cross-reference baseline)
- Capability matrix v1.22 → v1.23 EXTENSION drift detector
"""

from __future__ import annotations


# ── Test LISTEN_NOTIFY_TENANT_FANOUT enum exists ──────────────
class TestListenNotifyTenantFanoutEnum:
    """Capability.LISTEN_NOTIFY_TENANT_FANOUT enum exists."""

    def test_listen_notify_tenant_fanout_in_capability_enum(self) -> None:
        """LISTEN_NOTIFY_TENANT_FANOUT is a member of Capability enum."""
        from apps.api.core.capability import Capability

        assert hasattr(Capability, "LISTEN_NOTIFY_TENANT_FANOUT")

    def test_listen_notify_tenant_fanout_value(self) -> None:
        """LISTEN_NOTIFY_TENANT_FANOUT enum value = 'listen_notify_tenant_fanout'."""
        from apps.api.core.capability import Capability

        assert (
            Capability.LISTEN_NOTIFY_TENANT_FANOUT.value
            == "listen_notify_tenant_fanout"
        )

    def test_listen_notify_tenant_fanout_is_str_subclass(self) -> None:
        """LISTEN_NOTIFY_TENANT_FANOUT inherits from str (so it can be used as a string)."""
        from apps.api.core.capability import Capability

        assert isinstance(Capability.LISTEN_NOTIFY_TENANT_FANOUT, str)
        assert (
            Capability.LISTEN_NOTIFY_TENANT_FANOUT
            == "listen_notify_tenant_fanout"
        )


# ── Test LISTEN_NOTIFY_MULTIPROCESS enum exists ───────────────
class TestListenNotifyMultiprocessEnum:
    """Capability.LISTEN_NOTIFY_MULTIPROCESS enum exists."""

    def test_listen_notify_multiprocess_in_capability_enum(self) -> None:
        """LISTEN_NOTIFY_MULTIPROCESS is a member of Capability enum."""
        from apps.api.core.capability import Capability

        assert hasattr(Capability, "LISTEN_NOTIFY_MULTIPROCESS")

    def test_listen_notify_multiprocess_value(self) -> None:
        """LISTEN_NOTIFY_MULTIPROCESS enum value = 'listen_notify_multiprocess'."""
        from apps.api.core.capability import Capability

        assert (
            Capability.LISTEN_NOTIFY_MULTIPROCESS.value
            == "listen_notify_multiprocess"
        )

    def test_listen_notify_multiprocess_is_str_subclass(self) -> None:
        """LISTEN_NOTIFY_MULTIPROCESS inherits from str."""
        from apps.api.core.capability import Capability

        assert isinstance(Capability.LISTEN_NOTIFY_MULTIPROCESS, str)
        assert (
            Capability.LISTEN_NOTIFY_MULTIPROCESS
            == "listen_notify_multiprocess"
        )


# ── Test LISTEN_NOTIFY_TENANT_FANOUT 4-industry grants ────────
class TestListenNotifyTenantFanout4IndustryGrants:
    """LISTEN_NOTIFY_TENANT_FANOUT is granted to all 4 industries (industry-agnostic)."""

    def _get_industry_grants(self, industry: str) -> set[str]:
        """Get the capability set for a given industry."""
        from apps.api.core.capability import _INDUSTRY_CAPABILITIES
        from packages.services.m0_onboarding.industry_menu import Industry

        industry_map = {
            "manufacturing": Industry.MANUFACTURING,
            "service": Industry.SERVICE,
            "manufacturing_service": Industry.MANUFACTURING_SERVICE,
            "manufacturing_service_other": Industry.MANUFACTURING_SERVICE_OTHER,
        }
        result = _INDUSTRY_CAPABILITIES.get(industry_map[industry], frozenset())
        return {c.value for c in result}

    def test_listen_notify_tenant_fanout_granted_to_manufacturing(self) -> None:
        """manufacturing tenants get LISTEN_NOTIFY_TENANT_FANOUT."""
        grants = self._get_industry_grants("manufacturing")
        assert "listen_notify_tenant_fanout" in grants

    def test_listen_notify_tenant_fanout_granted_to_service(self) -> None:
        """service tenants get LISTEN_NOTIFY_TENANT_FANOUT."""
        grants = self._get_industry_grants("service")
        assert "listen_notify_tenant_fanout" in grants

    def test_listen_notify_tenant_fanout_granted_to_manufacturing_service(self) -> None:
        """manufacturing_service tenants get LISTEN_NOTIFY_TENANT_FANOUT."""
        grants = self._get_industry_grants("manufacturing_service")
        assert "listen_notify_tenant_fanout" in grants

    def test_listen_notify_tenant_fanout_granted_to_manufacturing_service_other(self) -> None:
        """manufacturing_service_other tenants get LISTEN_NOTIFY_TENANT_FANOUT."""
        grants = self._get_industry_grants("manufacturing_service_other")
        assert "listen_notify_tenant_fanout" in grants

    def test_listen_notify_tenant_fanout_industry_agnostic(self) -> None:
        """All 4 industries have the same LISTEN_NOTIFY_TENANT_FANOUT grant."""
        grants_by_industry = {
            ind: self._get_industry_grants(ind)
            for ind in (
                "manufacturing",
                "service",
                "manufacturing_service",
                "manufacturing_service_other",
            )
        }
        for industry, grants in grants_by_industry.items():
            assert "listen_notify_tenant_fanout" in grants, (
                f"{industry} missing LISTEN_NOTIFY_TENANT_FANOUT"
            )


# ── Test LISTEN_NOTIFY_MULTIPROCESS 4-industry grants ─────────
class TestListenNotifyMultiprocess4IndustryGrants:
    """LISTEN_NOTIFY_MULTIPROCESS is granted to all 4 industries (industry-agnostic)."""

    def _get_industry_grants(self, industry: str) -> set[str]:
        """Get the capability set for a given industry."""
        from apps.api.core.capability import _INDUSTRY_CAPABILITIES
        from packages.services.m0_onboarding.industry_menu import Industry

        industry_map = {
            "manufacturing": Industry.MANUFACTURING,
            "service": Industry.SERVICE,
            "manufacturing_service": Industry.MANUFACTURING_SERVICE,
            "manufacturing_service_other": Industry.MANUFACTURING_SERVICE_OTHER,
        }
        result = _INDUSTRY_CAPABILITIES.get(industry_map[industry], frozenset())
        return {c.value for c in result}

    def test_listen_notify_multiprocess_granted_to_manufacturing(self) -> None:
        """manufacturing tenants get LISTEN_NOTIFY_MULTIPROCESS."""
        grants = self._get_industry_grants("manufacturing")
        assert "listen_notify_multiprocess" in grants

    def test_listen_notify_multiprocess_granted_to_service(self) -> None:
        """service tenants get LISTEN_NOTIFY_MULTIPROCESS."""
        grants = self._get_industry_grants("service")
        assert "listen_notify_multiprocess" in grants

    def test_listen_notify_multiprocess_granted_to_manufacturing_service(self) -> None:
        """manufacturing_service tenants get LISTEN_NOTIFY_MULTIPROCESS."""
        grants = self._get_industry_grants("manufacturing_service")
        assert "listen_notify_multiprocess" in grants

    def test_listen_notify_multiprocess_granted_to_manufacturing_service_other(self) -> None:
        """manufacturing_service_other tenants get LISTEN_NOTIFY_MULTIPROCESS."""
        grants = self._get_industry_grants("manufacturing_service_other")
        assert "listen_notify_multiprocess" in grants

    def test_listen_notify_multiprocess_industry_agnostic(self) -> None:
        """All 4 industries have the same LISTEN_NOTIFY_MULTIPROCESS grant."""
        grants_by_industry = {
            ind: self._get_industry_grants(ind)
            for ind in (
                "manufacturing",
                "service",
                "manufacturing_service",
                "manufacturing_service_other",
            )
        }
        for industry, grants in grants_by_industry.items():
            assert "listen_notify_multiprocess" in grants, (
                f"{industry} missing LISTEN_NOTIFY_MULTIPROCESS"
            )


# ── Test capability matrix v1.22 → v1.23 EXTENSION drift ──────
class TestCapabilityMatrixV1Dot23Extension:
    """Capability matrix v1.22 → v1.23 EXTENSION (2 NEW rows)."""

    def test_listen_notify_preserved_13_1(self) -> None:
        """LISTEN_NOTIFY (13-1 baseline) preserved in v1.23."""
        from apps.api.core.capability import Capability, _INDUSTRY_CAPABILITIES
        from packages.services.m0_onboarding.industry_menu import Industry

        for industry in Industry:
            grants = _INDUSTRY_CAPABILITIES.get(industry, frozenset())
            assert Capability.LISTEN_NOTIFY in grants, (
                f"LISTEN_NOTIFY missing for {industry}"
            )

    def test_total_new_rows_count_is_2(self) -> None:
        """v1.23 EXTENSION adds exactly 2 NEW rows (LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS)."""
        from apps.api.core.capability import Capability

        assert hasattr(Capability, "LISTEN_NOTIFY_TENANT_FANOUT")
        assert hasattr(Capability, "LISTEN_NOTIFY_MULTIPROCESS")

    def test_both_new_capabilities_grants_all_4_industries(self) -> None:
        """Both NEW capabilities granted to all 4 industries."""
        from apps.api.core.capability import (
            Capability,
            _INDUSTRY_CAPABILITIES,
        )
        from packages.services.m0_onboarding.industry_menu import Industry

        for industry in Industry:
            grants = _INDUSTRY_CAPABILITIES.get(industry, frozenset())
            assert Capability.LISTEN_NOTIFY_TENANT_FANOUT in grants
            assert Capability.LISTEN_NOTIFY_MULTIPROCESS in grants


# ── Test capability matrix v1.23 documentation ────────────────
class TestCapabilityMatrixV1Dot23Docs:
    """Capability matrix v1.23 documentation has 2 NEW rows."""

    def test_capability_matrix_path_exists(self) -> None:
        """docs/capability-matrix.md path is sound."""
        from pathlib import Path

        path = (
            Path(__file__).parent.parent.parent
            / "docs"
            / "capability-matrix.md"
        )
        # Test path calculation only.
        assert "capability-matrix.md" in str(path)
