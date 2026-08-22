"""tests.api.core.test_phase_5_failover_orchestrator — failover orchestrator unit tests.

Phase 5 (cj-style 75번째 wire) — AC #2.1~#2.5 verbatim.
Verifies FailoverOrchestrator structure: 3 NEW error classes (CR 12-5 D-14),
constants, audit-first INSERT call sites (CR 1-1 verbatim).
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FAILOVER_PY = REPO_ROOT / "apps" / "api" / "jobs" / "failover_orchestrator.py"


@pytest.fixture(scope="module")
def failover_text() -> str:
    assert FAILOVER_PY.exists(), f"{FAILOVER_PY} missing"
    return FAILOVER_PY.read_text(encoding="utf-8")


class TestErrorClasses:
    """CR 12-5 D-14 typed exception envelope: 3 NEW error classes."""

    def test_failover_in_progress_error(self, failover_text: str) -> None:
        assert "class FailoverInProgressError(FailoverError)" in failover_text
        assert "FAILOVER_IN_PROGRESS" in failover_text

    def test_failover_target_unhealthy_error(self, failover_text: str) -> None:
        assert "class FailoverTargetUnhealthyError(FailoverError)" in failover_text
        assert "FAILOVER_TARGET_UNHEALTHY" in failover_text

    def test_failover_timeout_error(self, failover_text: str) -> None:
        assert "class FailoverTimeoutError(FailoverError)" in failover_text
        assert "FAILOVER_TIMEOUT" in failover_text


class TestConstants:
    """PRD §F20.2 verbatim — 5-second probe + 3 consecutive failures + 30s RTO."""

    def test_health_probe_interval(self, failover_text: str) -> None:
        assert "HEALTH_PROBE_INTERVAL_SECONDS = 5" in failover_text

    def test_consecutive_failures_threshold(self, failover_text: str) -> None:
        assert "CONSECUTIVE_FAILURES_THRESHOLD = 3" in failover_text

    def test_rto_sla_seconds(self, failover_text: str) -> None:
        assert "RTO_SLA_SECONDS = 30" in failover_text

    def test_graceful_shutdown_timeout(self, failover_text: str) -> None:
        assert "GRACEFUL_SHUTDOWN_TIMEOUT" in failover_text


class TestAuditFirstInsert:
    """CR 1-1 audit-first INSERT: 2 NEW audit log rows (failover_initiated + completed)."""

    def test_failover_initiated_action(self, failover_text: str) -> None:
        assert 'action="failover_initiated"' in failover_text

    def test_failover_completed_action(self, failover_text: str) -> None:
        assert 'action="failover_completed"' in failover_text

    def test_action_class_infra(self, failover_text: str) -> None:
        assert "ActionClass.INFRA" in failover_text

    def test_emit_audit_typed_called(self, failover_text: str) -> None:
        assert failover_text.count("emit_audit_typed") >= 2


class TestFailoverTriggers:
    """PRD §F20.2 verbatim — 3 trigger paths."""

    def test_health_probe_loop(self, failover_text: str) -> None:
        assert "_health_probe_loop" in failover_text

    def test_trigger_failover_method(self, failover_text: str) -> None:
        assert "async def trigger_failover" in failover_text

    def test_drill_mode_flag(self, failover_text: str) -> None:
        assert "drill_mode" in failover_text

    def test_manual_trigger_reason(self, failover_text: str) -> None:
        assert '"reason"' in failover_text
        assert '"manual"' in failover_text or "'manual'" in failover_text

    def test_health_probe_reason(self, failover_text: str) -> None:
        assert '"health_probe"' in failover_text or "'health_probe'" in failover_text

    def test_drill_reason(self, failover_text: str) -> None:
        assert '"drill"' in failover_text or "'drill'" in failover_text


class TestFailoverOrchestratorClass:
    def test_class_declared(self, failover_text: str) -> None:
        assert "class FailoverOrchestrator" in failover_text

    def test_start_method(self, failover_text: str) -> None:
        assert "async def start" in failover_text

    def test_stop_method(self, failover_text: str) -> None:
        assert "async def stop" in failover_text

    def test_promote_secondary_method(self, failover_text: str) -> None:
        assert "async def _promote_secondary" in failover_text

    def test_probe_primary_method(self, failover_text: str) -> None:
        assert "async def _probe_primary" in failover_text

    def test_probe_secondary_method(self, failover_text: str) -> None:
        assert "async def _probe_secondary" in failover_text

    def test_singleton_exported(self, failover_text: str) -> None:
        assert "orchestrator = FailoverOrchestrator()" in failover_text

    def test_lifespan_hooks(self, failover_text: str) -> None:
        assert "start_failover_orchestrator" in failover_text
        assert "stop_failover_orchestrator" in failover_text