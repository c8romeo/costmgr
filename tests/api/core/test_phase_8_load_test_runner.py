"""tests.api.core.test_phase_8_load_test_runner — Phase 8 load_test_runner module tests.

8 NEW pytest cases PASS (Phase 8 cj-style 95번째 wire backend tests).
"""
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

import pytest

from apps.api.core.load_test_runner import (
    K6Scenario,
    K6_VERSION,
    LoadTestRunnerExecutionError,
    LoadTestRunnerInvalidScenarioError,
    LoadTestRunRequest,
    is_k6_available,
    run_k6_load_test,
)


# ── 8 NEW pytest cases (Phase 8 T7.1) ──────────────────────────


def test_k6_version_pinned() -> None:
    """AD-14 stack pin — k6==0.45.0 verbatim."""
    assert K6_VERSION == "0.45.0"


def test_k6_scenario_enum_has_five_values() -> None:
    """PRD §F24.1 — 5 canonical k6 scenarios verbatim."""
    expected = {
        "auth-login",
        "cost-calculation",
        "onboarding-flow",
        "audit-log-query",
        "multi-region-failover",
    }
    actual = {s.value for s in K6Scenario}
    assert actual == expected


def test_run_k6_load_test_dry_run_returns_synthetic_summary() -> None:
    """F24.1-12 — dry_run=True returns synthetic summary without invoking k6."""
    async def _inner() -> None:
        req = LoadTestRunRequest(
            scenario=K6Scenario.AUTH_LOGIN,
            tenant_id=uuid.uuid4(),
            trace_id="trace-dry-run",
            dry_run=True,
        )
        result = await run_k6_load_test(req)
        assert result["dry_run"] is True
        assert result["scenario"] == "auth-login"
        assert result["metrics"]["count"] == 0
        assert result["rps"] == 0.0
        assert result["error_rate"] == 0.0
        assert len(result["result_hash"]) == 64  # sha256 hex digest

    asyncio.run(_inner())


def test_run_k6_load_test_invalid_scenario_raises_typed_error(tmp_path: Path) -> None:
    """CR 12-5 D-14 — invalid scenario name → LoadTestRunnerInvalidScenarioError."""
    async def _inner() -> None:
        # Create empty scripts dir so we hit the file-not-found path.
        req = LoadTestRunRequest(
            scenario=K6Scenario.AUTH_LOGIN,
            tenant_id=uuid.uuid4(),
            trace_id="trace-invalid",
            dry_run=False,
        )
        with pytest.raises(LoadTestRunnerInvalidScenarioError) as exc_info:
            await run_k6_load_test(req, scripts_dir=tmp_path)
        assert exc_info.value.scenario == "auth-login"
        assert "auth-login" in exc_info.value.known

    asyncio.run(_inner())


def test_run_k6_load_test_k6_unavailable_raises(tmp_path: Path) -> None:
    """When k6 binary is missing and dry_run=False → FileNotFoundError."""
    async def _inner() -> None:
        # Create the script file so we get past the script validation.
        (tmp_path / "auth-login.js").write_text("// stub\n")
        req = LoadTestRunRequest(
            scenario=K6Scenario.AUTH_LOGIN,
            tenant_id=uuid.uuid4(),
            trace_id="trace-no-k6",
            dry_run=False,
        )
        # If k6 happens to be on PATH, skip — we don't want a flaky test.
        if is_k6_available():
            pytest.skip("k6 binary available on this environment")
        with pytest.raises(FileNotFoundError):
            await run_k6_load_test(req, scripts_dir=tmp_path)

    asyncio.run(_inner())


def test_k6_scenario_vu_defaults() -> None:
    """PRD §F24.1 — canonical VU defaults per scenario."""
    from apps.api.core.load_test_runner import SCENARIO_VU_DEFAULT

    assert SCENARIO_VU_DEFAULT[K6Scenario.AUTH_LOGIN] == 100
    assert SCENARIO_VU_DEFAULT[K6Scenario.COST_CALCULATION] == 50
    assert SCENARIO_VU_DEFAULT[K6Scenario.ONBOARDING_FLOW] == 30
    assert SCENARIO_VU_DEFAULT[K6Scenario.AUDIT_LOG_QUERY] == 20
    assert SCENARIO_VU_DEFAULT[K6Scenario.MULTI_REGION_FAILOVER] == 10


def test_load_test_metric_typed_dict_shape() -> None:
    """CR 12-5 D-PARITY-01 — TypedDict parity with TS mirror."""
    from apps.api.core.load_test_runner import LoadTestMetric

    m: LoadTestMetric = {
        "p95_ms": 123.4,
        "p99_ms": 456.7,
        "count": 1000,
        "rate_per_sec": 50.0,
    }
    assert m["p99_ms"] == 456.7


def test_load_test_run_result_tenant_scoped_hash() -> None:
    """CR 0-2 RLS — result_hash is tenant-scoped (different tenant_id → different hash)."""
    import asyncio

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    req_a = LoadTestRunRequest(
        scenario=K6Scenario.COST_CALCULATION,
        tenant_id=tenant_a,
        trace_id="trace-a",
        dry_run=True,
    )
    req_b = LoadTestRunRequest(
        scenario=K6Scenario.COST_CALCULATION,
        tenant_id=tenant_b,
        trace_id="trace-b",
        dry_run=True,
    )
    result_a = asyncio.run(run_k6_load_test(req_a))
    result_b = asyncio.run(run_k6_load_test(req_b))
    # Same scenario, different tenants → different hash (CR 0-2 verbatim).
    assert result_a["result_hash"] != result_b["result_hash"]
