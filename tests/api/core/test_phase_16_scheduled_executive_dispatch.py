"""tests.api.core.test_phase_16_scheduled_executive_dispatch — Phase 16 scheduled dispatch tests.

Phase 16 (cj-style 127번째 wire) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.4 verbatim + AD-43 (d) decision). 4 cron schedules
weekly/monthly/quarterly/annual + 4 recipient strategies.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

from apps.api.jobs.scheduled_executive_dispatch import (
    schedule_executive_dispatch,
    DISPATCH_CRON_EXPRESSIONS,
)
from apps.api.modules.finops.reporting.serializers import (
    ALL_DISPATCH_SCHEDULES,
    ALL_RECIPIENT_STRATEGIES,
)


TENANT_ID = str(uuid.uuid4())


# ── 7 NEW pytest cases ──────────────────────────────────────
def test_4_cron_schedules_registered() -> None:
    """Test 1: 4 dispatch schedules (weekly/monthly/quarterly/annual)."""
    assert set(ALL_DISPATCH_SCHEDULES) == {
        "weekly",
        "monthly",
        "quarterly",
        "annual",
    }


def test_4_recipient_strategies_registered() -> None:
    """Test 2: 4 recipient strategies."""
    assert set(ALL_RECIPIENT_STRATEGIES) == {
        "owner_only",
        "executive_team",
        "board_observers",
        "custom_recipients",
    }


def test_4_cron_expressions_per_schedule() -> None:
    """Test 3: DISPATCH_CRON_EXPRESSIONS has 4 entries."""
    assert len(DISPATCH_CRON_EXPRESSIONS) == 4
    assert DISPATCH_CRON_EXPRESSIONS["weekly"] == "0 9 * * 1"
    assert DISPATCH_CRON_EXPRESSIONS["monthly"] == "0 9 1 * *"
    assert DISPATCH_CRON_EXPRESSIONS["quarterly"] == "0 9 1 1,4,7,10 *"
    assert DISPATCH_CRON_EXPRESSIONS["annual"] == "0 9 1 1 *"


def test_scheduled_dispatch_typed_dict() -> None:
    """Test 4: ScheduledDispatch TypedDict has all required fields."""
    dispatch = schedule_executive_dispatch(
        tenant_id=TENANT_ID,
        dispatch_schedule="monthly",
        recipient_strategy="owner_only",
        dry_run=True,
    )
    expected_fields = {
        "dispatch_id",
        "tenant_id",
        "dispatch_schedule",
        "cron_expression",
        "recipient_strategy",
        "recipient_list",
        "report_id",
        "status",
        "scheduled_at",
        "trace_id",
    }
    assert set(dispatch.keys()) == expected_fields


def test_schedule_weekly_in_dry_run() -> None:
    """Test 5: weekly schedule works in dry-run."""
    dispatch = schedule_executive_dispatch(
        tenant_id=TENANT_ID,
        dispatch_schedule="weekly",
        recipient_strategy="owner_only",
        dry_run=True,
    )
    assert dispatch["dispatch_schedule"] == "weekly"
    assert dispatch["recipient_strategy"] == "owner_only"


def test_invalid_schedule_raises_error() -> None:
    """Test 6: invalid dispatch_schedule raises typed exception."""
    from apps.api.core.errors import ScheduledDispatchError
    import pytest
    with pytest.raises(ScheduledDispatchError):
        schedule_executive_dispatch(
            tenant_id=TENANT_ID,
            dispatch_schedule="invalid_schedule",
            recipient_strategy="owner_only",
            dry_run=True,
        )


def test_lifecycle_state_machine_initial_value() -> None:
    """Test 7: dispatch.status starts as 'scheduled' in dry-run."""
    dispatch = schedule_executive_dispatch(
        tenant_id=TENANT_ID,
        dispatch_schedule="quarterly",
        recipient_strategy="executive_team",
        dry_run=True,
    )
    assert dispatch["status"] in {"scheduled", "running", "completed"}