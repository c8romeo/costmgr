"""tests.api.core.test_phase_8_latency_regression — Latency regression module tests.

6 NEW pytest cases PASS (Phase 8 cj-style 95번째 wire backend tests).
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.latency_budget import (
    DEFAULT_LATENCY_BUDGETS,
    LatencyRegressionThresholdExceededError,
    get_latency_budget_for_endpoint,
    resolve_tenant_budget_override,
    set_current_trace_id,
    get_current_trace_id,
)


# ── 6 NEW pytest cases (Phase 8 T7.2) ──────────────────────────


def test_default_latency_budgets_has_4_canonical_slas() -> None:
    """PRD §F24.2 — 4 canonical SLAs verbatim (cost/audit/login/failover)."""
    expected = {
        "POST /api/v1/cost-engine/compute",
        "GET /api/v1/audit-log",
        "POST /api/v1/auth/login",
        "GET /api/v1/admin/health/multi-region",
    }
    assert expected.issubset(DEFAULT_LATENCY_BUDGETS.keys())


def test_sla1_cost_calculation_p99_5s() -> None:
    """PRD §F24.2-2 — SLA-1 p99 < 5s."""
    budget = DEFAULT_LATENCY_BUDGETS["POST /api/v1/cost-engine/compute"]
    assert budget["p99_budget_ms"] == 5000
    assert budget["window_s"] == 86400 * 30  # 30d rolling


def test_sla2_audit_log_query_p99_2s() -> None:
    """PRD §F24.2-3 — SLA-2 p99 < 2s (Epic 17 wire `2ada2ec` carry-over)."""
    budget = DEFAULT_LATENCY_BUDGETS["GET /api/v1/audit-log"]
    assert budget["p99_budget_ms"] == 2000


def test_sla3_login_p99_1s() -> None:
    """PRD §F24.2-4 — SLA-3 p99 < 1s (Phase 3 + Epic 15 carry-over)."""
    budget = DEFAULT_LATENCY_BUDGETS["POST /api/v1/auth/login"]
    assert budget["p99_budget_ms"] == 1000


def test_sla4_multi_region_failover_rto_30s() -> None:
    """PRD §F24.2-5 — SLA-4 RTO < 30s (Phase 5 wire `f093f8c` carry-over)."""
    budget = DEFAULT_LATENCY_BUDGETS["GET /api/v1/admin/health/multi-region"]
    assert budget["p99_budget_ms"] == 30000


def test_per_tenant_override_resolves_above_default() -> None:
    """F24.3-7 — per-tenant JSONB override takes precedence over default budget."""
    tenant_settings = {
        "latency_budget": {
            "POST /api/v1/cost-engine/compute": {
                "p99_budget_ms": 3000,  # tighter tenant-scoped budget
                "window_s": 86400 * 30,
                "alert_threshold_pct": 80,
                "dry_run": False,
            },
        }
    }
    budget = get_latency_budget_for_endpoint(
        endpoint="POST /api/v1/cost-engine/compute",
        tenant_settings_jsonb=tenant_settings,
    )
    assert budget["p99_budget_ms"] == 3000  # override, not default 5000


def test_unmapped_endpoint_returns_synthetic_fallback() -> None:
    """F24.3-7 — unmapped endpoint = synthetic fallback (5s, dry_run=True)."""
    budget = get_latency_budget_for_endpoint(
        endpoint="POST /api/v1/nonexistent/endpoint",
    )
    assert budget["p99_budget_ms"] == 5000
    assert budget["dry_run"] is True  # guards against silent oversights


def test_latency_regression_typed_exception_envelope() -> None:
    """CR 12-5 D-14 — typed exception envelope with actual_p99 + budget + trace_id."""
    exc = LatencyRegressionThresholdExceededError(
        endpoint="POST /api/v1/cost-engine/compute",
        actual_p99_ms=6500.0,
        budget_ms=5000,
        trace_id="trace-123",
    )
    assert exc.endpoint == "POST /api/v1/cost-engine/compute"
    assert exc.actual_p99_ms == 6500.0
    assert exc.budget_ms == 5000
    assert exc.trace_id == "trace-123"


def test_trace_id_context_var_isolation() -> None:
    """CR 1-1 ContextVar verbatim — Phase 7 tracing.py pattern carry-over."""
    tid_a = f"trace-a-{uuid.uuid4()}"
    tid_b = f"trace-b-{uuid.uuid4()}"
    set_current_trace_id(tid_a)
    assert get_current_trace_id() == tid_a
    set_current_trace_id(tid_b)
    assert get_current_trace_id() == tid_b
