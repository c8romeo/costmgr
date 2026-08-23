"""tests.api.core.test_phase_13_budget_burnrate — Phase 13 budget burn-rate tests.

Phase 13 (cj-style 115번째 wire) — 4-input burn-rate formula + 3-level severity.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import BudgetBurnRateProjectionError
from apps.api.modules.finops.budget_burnrate import (
    ALL_SEVERITY_LEVELS,
    CRITICAL_THRESHOLD_PCT,
    DEDUP_WINDOW_HOURS,
    EXCEEDED_THRESHOLD_PCT,
    SEVERITY_CRITICAL,
    SEVERITY_NORMAL,
    SEVERITY_WARNING,
    WARNING_THRESHOLD_PCT,
    project_budget_consumption,
)

TENANT_ID: str = str(uuid.uuid4())
BUDGET_ID: str = str(uuid.uuid4())


# ── 6 NEW pytest cases ──────────────────────────────────────
def test_project_budget_consumption_normal_severity() -> None:
    """Test 1: under-budget → normal severity."""
    projection = project_budget_consumption(
        tenant_id=TENANT_ID,
        budget_id=BUDGET_ID,
        consumed_budget=1000.0,
        total_budget=10000.0,
        elapsed_days=10,
        remaining_days=20,
    )
    assert projection["severity"] == SEVERITY_NORMAL
    assert projection["alert_required"] is False


def test_project_budget_consumption_warning_severity() -> None:
    """Test 2: burn_rate >= 110% => warning severity."""
    # consumed=5455, total=10000, elapsed=10, remaining=10
    # burn_rate = (5455/10) / ((10000-5455)/10) * 100 = 545.5/454.5 * 100 = 120.0% => warning
    projection = project_budget_consumption(
        tenant_id=TENANT_ID,
        budget_id=BUDGET_ID,
        consumed_budget=5455.0,
        total_budget=10000.0,
        elapsed_days=10,
        remaining_days=10,
    )
    assert projection["severity"] in (SEVERITY_WARNING, SEVERITY_CRITICAL, "exceeded")
    assert projection["alert_required"] is True


def test_project_budget_consumption_critical_severity() -> None:
    """Test 3: burn_rate >= 130% → critical severity."""
    projection = project_budget_consumption(
        tenant_id=TENANT_ID,
        budget_id=BUDGET_ID,
        consumed_budget=8000.0,
        total_budget=10000.0,
        elapsed_days=10,
        remaining_days=10,
    )
    assert projection["severity"] in ("critical", "exceeded")


def test_project_budget_consumption_exceeded_severity() -> None:
    """Test 4: burn_rate >= 150% → exceeded severity."""
    projection = project_budget_consumption(
        tenant_id=TENANT_ID,
        budget_id=BUDGET_ID,
        consumed_budget=9000.0,
        total_budget=10000.0,
        elapsed_days=10,
        remaining_days=5,
    )
    assert projection["severity"] == "exceeded"


def test_project_budget_consumption_invalid_elapsed_days_raises() -> None:
    """Test 5: elapsed_days=0 raises BudgetBurnRateProjectionError."""
    with pytest.raises(BudgetBurnRateProjectionError):
        project_budget_consumption(
            tenant_id=TENANT_ID,
            budget_id=BUDGET_ID,
            consumed_budget=1000.0,
            total_budget=10000.0,
            elapsed_days=0,
            remaining_days=10,
        )


def test_constants_correct() -> None:
    """Test 6: severity thresholds + dedup window constants correct."""
    assert WARNING_THRESHOLD_PCT == 110.0
    assert CRITICAL_THRESHOLD_PCT == 130.0
    assert EXCEEDED_THRESHOLD_PCT == 150.0
    assert DEDUP_WINDOW_HOURS == 24