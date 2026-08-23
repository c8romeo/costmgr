"""tests.api.core.test_phase_9_chaos_game_day — game day job smoke test.

Phase 9 (cj-style 99번째 wire) — 4 NEW pytest cases PASS.
"""
from __future__ import annotations

import pytest

from apps.api.jobs.chaos_game_day import (
    GAME_DAY_DAY_OF_MONTH_MAX,
    GAME_DAY_DAY_OF_WEEK,
    GAME_DAY_HOUR_KST,
    ChaosGameDayTenantScopeError,
)


# ── 4 NEW pytest cases (Phase 9 T2.10) ─────────────────────────


def test_game_day_schedule_constants() -> None:
    """T2.10-1 — KST 1st Sunday 03:00 cron constants verbatim."""
    assert GAME_DAY_HOUR_KST == 3
    assert GAME_DAY_DAY_OF_MONTH_MAX == 7
    assert GAME_DAY_DAY_OF_WEEK == 6  # Sunday


def test_chaos_game_day_tenant_scope_error_inherits_base() -> None:
    """T2.10-2 — typed exception envelope (CR 12-5 D-14) for tenant scope."""
    from apps.api.core.errors import BaseError

    err = ChaosGameDayTenantScopeError(tenant_id="production")
    assert isinstance(err, BaseError)
    assert err.code == "CHAOS_GAME_DAY_TENANT_SCOPE_FORBIDDEN"


def test_chaos_game_day_module_exposes_run_entrypoint() -> None:
    """T2.10-3 — `run_game_day` is the canonical entrypoint."""
    from apps.api.jobs import chaos_game_day

    assert hasattr(chaos_game_day, "run_game_day")
    assert callable(chaos_game_day.run_game_day)
    assert hasattr(chaos_game_day, "start_game_day_scheduler")
    assert hasattr(chaos_game_day, "stop_game_day_scheduler")


def test_chaos_game_day_audit_action_class_registered() -> None:
    """T2.10-4 — CHAOS_ENGINEERING ActionClass + 4 actions reachable."""
    from apps.api.core.audit_action import (
        ActionClass,
        ChaosEngineeringAction,
        _ActionRegistry,
    )

    assert hasattr(ActionClass, "CHAOS_ENGINEERING")
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.CHAOS_ENGINEERING]
    assert log_type == "audit_logs"
    literals = set(ChaosEngineeringAction.__args__)
    # 4 NEW values all present
    for v in (
        "chaos_experiment_started",
        "chaos_experiment_completed",
        "chaos_experiment_aborted",
        "chaos_rollback_triggered",
    ):
        assert v in accepted
        assert v in literals
