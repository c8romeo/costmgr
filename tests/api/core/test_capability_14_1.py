"""Test capability 14.1 EXTENSION — LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS.

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): T5 EXTENSION.

Verifies the 14.1 EXTENSION to capability.py:
- 2 NEW enum values: LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS
- 4-industry grants ✅/✅/✅/✅ (industry-agnostic, CR 12-1 L4 precedent)
- require_capability Dependency 신규 wire 가능 (CR 12-5 D-GATE-01 inversion)
- capability matrix v1.22 → v1.23 EXTENSION (SSOT RED→GREEN)
"""

from __future__ import annotations

from packages.services.m0_onboarding.industry_menu import Industry

from apps.api.core.capability import (
    Capability,
    _INDUSTRY_CAPABILITIES,
    industry_supports,
)


# ── Test classes ─────────────────────────────────────────────
class TestNewCapabilityEnumValues:
    """2 NEW enum values (capability matrix v1.23 EXTENSION)."""

    def test_listen_notify_tenant_fanout_exists(self) -> None:
        """LISTEN_NOTIFY_TENANT_FANOUT exists in Capability enum."""
        assert hasattr(Capability, "LISTEN_NOTIFY_TENANT_FANOUT")
        assert (
            Capability.LISTEN_NOTIFY_TENANT_FANOUT.value
            == "listen_notify_tenant_fanout"
        )

    def test_listen_notify_multiprocess_exists(self) -> None:
        """LISTEN_NOTIFY_MULTIPROCESS exists in Capability enum."""
        assert hasattr(Capability, "LISTEN_NOTIFY_MULTIPROCESS")
        assert (
            Capability.LISTEN_NOTIFY_MULTIPROCESS.value
            == "listen_notify_multiprocess"
        )

    def test_capability_value_strings(self) -> None:
        """Both new capabilities have the correct value strings."""
        assert (
            Capability.LISTEN_NOTIFY_TENANT_FANOUT
            == "listen_notify_tenant_fanout"
        )
        assert (
            Capability.LISTEN_NOTIFY_MULTIPROCESS
            == "listen_notify_multiprocess"
        )


class TestIndustryGrantsAllFourIndustries:
    """4-industry grants ✅/✅/✅/✅ (industry-agnostic, CR 12-1 L4 precedent)."""

    def test_manufacturing_grants_both(self) -> None:
        """manufacturing ✅ LISTEN_NOTIFY_TENANT_FANOUT + ✅ LISTEN_NOTIFY_MULTIPROCESS."""
        assert industry_supports(
            Industry.MANUFACTURING,
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
        )
        assert industry_supports(
            Industry.MANUFACTURING,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
        )

    def test_service_grants_both(self) -> None:
        """service ✅ LISTEN_NOTIFY_TENANT_FANOUT + ✅ LISTEN_NOTIFY_MULTIPROCESS."""
        assert industry_supports(
            Industry.SERVICE,
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
        )
        assert industry_supports(
            Industry.SERVICE,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
        )

    def test_manufacturing_service_grants_both(self) -> None:
        """manufacturing_service ✅ LISTEN_NOTIFY_TENANT_FANOUT + ✅ LISTEN_NOTIFY_MULTIPROCESS."""
        assert industry_supports(
            Industry.MANUFACTURING_SERVICE,
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
        )
        assert industry_supports(
            Industry.MANUFACTURING_SERVICE,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
        )

    def test_manufacturing_service_other_grants_both(self) -> None:
        """manufacturing_service_other ✅ LISTEN_NOTIFY_TENANT_FANOUT + ✅ LISTEN_NOTIFY_MULTIPROCESS."""
        assert industry_supports(
            Industry.MANUFACTURING_SERVICE_OTHER,
            Capability.LISTEN_NOTIFY_TENANT_FANOUT,
        )
        assert industry_supports(
            Industry.MANUFACTURING_SERVICE_OTHER,
            Capability.LISTEN_NOTIFY_MULTIPROCESS,
        )


class TestCapabilityMatrixV1_23Extension:
    """capability matrix v1.22 → v1.23 EXTENSION (SSOT RED→GREEN)."""

    def test_all_industries_grant_listen_notify_tenant_fanout(self) -> None:
        """Every industry grants LISTEN_NOTIFY_TENANT_FANOUT (industry-agnostic)."""
        for industry in Industry:
            caps = _INDUSTRY_CAPABILITIES.get(industry, frozenset())
            assert (
                Capability.LISTEN_NOTIFY_TENANT_FANOUT in caps
            ), f"Industry {industry.value!r} must grant LISTEN_NOTIFY_TENANT_FANOUT"

    def test_all_industries_grant_listen_notify_multiprocess(self) -> None:
        """Every industry grants LISTEN_NOTIFY_MULTIPROCESS (industry-agnostic)."""
        for industry in Industry:
            caps = _INDUSTRY_CAPABILITIES.get(industry, frozenset())
            assert (
                Capability.LISTEN_NOTIFY_MULTIPROCESS in caps
            ), f"Industry {industry.value!r} must grant LISTEN_NOTIFY_MULTIPROCESS"


class TestBackwardCompat13_1:
    """13-1 LISTEN_NOTIFY capability preserved (cross-reference)."""

    def test_listen_notify_preserved(self) -> None:
        """LISTEN_NOTIFY (13-1) is still in Capability enum."""
        assert hasattr(Capability, "LISTEN_NOTIFY")
        assert Capability.LISTEN_NOTIFY.value == "listen_notify"

    def test_all_industries_grant_listen_notify_13_1(self) -> None:
        """LISTEN_NOTIFY (13-1) preserved — all industries grant."""
        for industry in Industry:
            caps = _INDUSTRY_CAPABILITIES.get(industry, frozenset())
            assert Capability.LISTEN_NOTIFY in caps
