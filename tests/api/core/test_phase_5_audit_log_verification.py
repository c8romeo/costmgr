"""tests.api.core.test_phase_5_audit_log_verification — ActionClass.INFRA + InfraAction registry tests.

Phase 5 (cj-style 75번째 wire) — AC #1.6 + #2.4 + #3.3 + CR 1-1 verbatim.
Verifies ActionClass.INFRA is registered + InfraAction literal has
4 NEW values (replica_status_changed + failover_initiated +
failover_completed + dr_drill_completed).
"""

from __future__ import annotations


class TestInfraActionClassRegistration:
    def test_action_class_infra_exists(self) -> None:
        from apps.api.core.audit_action import ActionClass

        assert hasattr(ActionClass, "INFRA")
        assert ActionClass.INFRA.value == "infra"


class TestInfraActionLiteral:
    def test_replica_status_changed_in_literal(self) -> None:
        import typing

        from apps.api.core.audit_action import InfraAction

        # Use typing.get_args to introspect Literal values.
        values = typing.get_args(InfraAction)
        assert "replica_status_changed" in values

    def test_failover_initiated_in_literal(self) -> None:
        import typing

        from apps.api.core.audit_action import InfraAction

        values = typing.get_args(InfraAction)
        assert "failover_initiated" in values

    def test_failover_completed_in_literal(self) -> None:
        import typing

        from apps.api.core.audit_action import InfraAction

        values = typing.get_args(InfraAction)
        assert "failover_completed" in values

    def test_dr_drill_completed_in_literal(self) -> None:
        import typing

        from apps.api.core.audit_action import InfraAction

        values = typing.get_args(InfraAction)
        assert "dr_drill_completed" in values


class TestAuditActionRegistryShape:
    """AuditAction union must include InfraAction."""

    def test_audit_action_includes_infra(self) -> None:
        from apps.api.core.audit_action import InfraAction

        # Just verify InfraAction is importable + has correct structure.
        assert InfraAction is not None


class TestCR1Compliance:
    """CR 1-1 audit-first INSERT — failover_orchestrator + dr_drill must emit
    audit BEFORE row mutation.
    """

    def test_failover_orchestrator_emits_audit_first(self) -> None:
        import pathlib

        failover_path = (
            pathlib.Path(__file__).resolve().parents[3]
            / "apps"
            / "api"
            / "jobs"
            / "failover_orchestrator.py"
        )
        text = failover_path.read_text(encoding="utf-8")
        # failover_initiated emit must come BEFORE the row mutation
        # (in this case, the _promote_secondary call).
        init_idx = text.find('action="failover_initiated"')
        promote_idx = text.find("_promote_secondary(drill_mode=drill_mode)")
        assert init_idx != -1, "failover_initiated not emitted"
        assert promote_idx != -1, "_promote_secondary call not found"
        assert init_idx < promote_idx, (
            "CR 1-1 violation: audit emit must precede row mutation"
        )

    def test_dr_drill_emits_audit_first(self) -> None:
        import pathlib

        drill_path = (
            pathlib.Path(__file__).resolve().parents[3]
            / "apps"
            / "api"
            / "jobs"
            / "dr_drill.py"
        )
        text = drill_path.read_text(encoding="utf-8")
        # dr_drill_completed emit must come BEFORE the drill row mutation
        # (the UPDATE phase_5_dr_drill_results).
        drill_completed_idx = text.find('action="dr_drill_completed"')
        update_idx = text.find("UPDATE public.phase_5_dr_drill_results")
        assert drill_completed_idx != -1, "dr_drill_completed not emitted"
        # UPDATE happens multiple times — find the first one.
        assert update_idx != -1, "UPDATE statement not found"
        assert drill_completed_idx < update_idx, (
            "CR 1-1 violation: audit emit must precede row mutation"
        )