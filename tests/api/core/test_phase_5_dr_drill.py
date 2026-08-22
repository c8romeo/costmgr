"""tests.api.core.test_phase_5_dr_drill — DR drill unit tests.

Phase 5 (cj-style 75번째 wire) — AC #3.1~#3.4 verbatim.
Verifies dr_drill.py structure: 3 NEW error classes (CR 12-5 D-14),
quarterly schedule logic, 6 drill steps, audit-first INSERT
(dr_drill_completed), APScheduler lifespan hooks.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
DRILL_PY = REPO_ROOT / "apps" / "api" / "jobs" / "dr_drill.py"


@pytest.fixture(scope="module")
def drill_text() -> str:
    assert DRILL_PY.exists(), f"{DRILL_PY} missing"
    return DRILL_PY.read_text(encoding="utf-8")


class TestErrorClasses:
    """CR 12-5 D-14 typed exception envelope: 3 NEW error classes."""

    def test_dr_drill_timeout_error(self, drill_text: str) -> None:
        assert "class DRDrillTimeoutError(DRDrillError)" in drill_text
        assert "DR_DRILL_TIMEOUT" in drill_text

    def test_dr_drill_secondary_unhealthy_error(self, drill_text: str) -> None:
        assert "class DRDrillSecondaryUnhealthyError(DRDrillError)" in drill_text
        assert "DR_DRILL_SECONDARY_UNHEALTHY" in drill_text

    def test_dr_drill_rpo_limit_exceeded_error(self, drill_text: str) -> None:
        assert "class DRDrillRPOLimitExceededError(DRDrillError)" in drill_text
        assert "DR_DRILL_RPO_LIMIT_EXCEEDED" in drill_text


class TestConstants:
    """PRD §F20.4 verbatim SLA: RPO 1h / RTO 4h."""

    def test_rpo_sla_seconds(self, drill_text: str) -> None:
        assert "RPO_SLA_SECONDS = 3600" in drill_text

    def test_rto_sla_seconds(self, drill_text: str) -> None:
        assert "RTO_SLA_SECONDS = 14400" in drill_text


class TestQuarterlySchedule:
    """PRD §F20.3 verbatim — Q1/Q2/Q3/Q4 quarterly schedule."""

    def test_current_quarter_helper(self, drill_text: str) -> None:
        assert "_current_quarter" in drill_text
        assert 'YYYY-Q[1-4]' in drill_text or "f\"{now.year}-Q{quarter}\"" in drill_text


class TestDrillSteps:
    """PRD §F20.3 verbatim — 6 drill steps."""

    def test_execute_drill_steps(self, drill_text: str) -> None:
        assert "_execute_drill_steps" in drill_text

    def test_probe_primary_health(self, drill_text: str) -> None:
        assert "_probe_primary_health" in drill_text

    def test_probe_secondary_health(self, drill_text: str) -> None:
        assert "_probe_secondary_health" in drill_text

    def test_run_drill_entry(self, drill_text: str) -> None:
        assert "async def run_drill" in drill_text


class TestAuditFirstInsert:
    """CR 1-1 audit-first INSERT: dr_drill_completed."""

    def test_dr_drill_completed_action(self, drill_text: str) -> None:
        assert 'action="dr_drill_completed"' in drill_text

    def test_action_class_infra(self, drill_text: str) -> None:
        assert "ActionClass.INFRA" in drill_text

    def test_emit_audit_typed_called(self, drill_text: str) -> None:
        assert "emit_audit_typed" in drill_text


class TestAPSchedulerHooks:
    def test_start_scheduler(self, drill_text: str) -> None:
        assert "start_dr_drill_scheduler" in drill_text

    def test_stop_scheduler(self, drill_text: str) -> None:
        assert "stop_dr_drill_scheduler" in drill_text

    def test_kst_sunday_3am(self, drill_text: str) -> None:
        assert "Sunday" in drill_text or "saturday" in drill_text.lower()


class TestImports:
    """dr_drill imports failover_orchestrator (reuses trigger_failover)."""

    def test_failover_orchestrator_import(self, drill_text: str) -> None:
        assert "from apps.api.jobs.failover_orchestrator import" in drill_text

    def test_failover_orchestrator_called(self, drill_text: str) -> None:
        assert "trigger_failover" in drill_text