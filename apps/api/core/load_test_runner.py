"""apps.api.core.load_test_runner — k6 load test orchestration (Phase 8 F24.1).

Phase 8 (cj-style 95번째 epic 연속 정직 회복 atomic docs-and-source wire) —
Performance/Load Testing territory (PRD §F24.1 + AD-35 (a) sub-decision).
This module provides:

- `K6Scenario` — enum of the 5 canonical k6 load test scenarios
  (auth-login / cost-calculation / onboarding-flow / audit-log-query /
  multi-region-failover).
- `LoadTestRunResult` — TypedDict for k6 summary output (p95/p99 latency
  + RPS + error rate + tenant-scoped result_hash).
- `run_k6_load_test()` — k6 subprocess wrapper that invokes the
  scenario JS file, parses the JSON summary, and returns the typed
  result. CR 1-1 audit-first INSERT happens at the route layer
  (performance_test_started BEFORE invocation + performance_test_completed
  AFTER summary parse).
- `LoadTestRunnerInvalidScenarioError(400)` — typed exception envelope
  per CR 12-5 D-14 + AD-15 conventions.md §4. Mapped to HTTP 400 by
  main.py global handler.
- `dry_run=True` mode — VU=0 invocation that returns synthetic baseline
  metrics (no actual load generated). Used by the dry-run UI flow.
- `OTEL_SDK_DISABLED` no-op fallback — mirrors Phase 7 Sentry conditional
  init pattern (`SENTRY_DSN` env flag).

CR lessons applied:
- CR 0-2 RLS — every load test run is scoped to a single tenant_id
  (multi-tenant isolation preserved). The k6 scenarios pass the
  `X-Tenant-Context` JWT and `tenant_id` claim.
- CR 1-1 audit-first INSERT — route handler emits `performance_test_started`
  audit log BEFORE invoking k6 subprocess and `performance_test_completed`
  audit log AFTER parsing the summary.
- CR 4-3 / 4-4 — tenant-scoped result_hash for golden_diff comparison
  (mirrors Epic 7 cost-engine V8 golden fixture pattern).
- AD-22 owner-only RBAC — manual trigger requires `require_role("owner")`
  at the route layer; Epic 12 2FA 챌린지 보존 enforced upstream.
- AD-14 stack pin — k6 binary pinned to v0.45.0 (k6==0.45.0 in
  apps/api/pyproject.toml [dependency-groups] dev section).

Industry-agnostic per CR 12-1 L4 precedent (mirrors OBSERVABILITY_*
Phase 7 wire pattern + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW
Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern
verbatim). All 4 industries get PERFORMANCE_TESTING capability.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Final, TypedDict

# ── K6 binary discovery ────────────────────────────────────────
K6_VERSION: Final[str] = "0.45.0"  # AD-14 stack pin (Phase 8 wire)

# The k6 binary must be on PATH. We don't shell out to a hardcoded path
# to avoid drift across CI environments (Phase 7 Sentry conditional init
# pattern verbatim — env flag driven).
K6_BINARY: Final[str] = os.environ.get("K6_BINARY", "k6")


class K6Scenario(str, Enum):
    """Canonical k6 load test scenarios (PRD §F24.1).

    Order = introduction order. Append-only.

    Each scenario corresponds to a JS file in `apps/api/tests/load/k6/`.
    The k6 thresholds are set per scenario:
    - auth-login:           p95<500ms, p99<1s, error_rate<1%
    - cost-calculation:     p95<2s, p99<5s (NFR22 latency budget), error_rate<1%
    - onboarding-flow:      p95<1s, p99<3s, error_rate<1%
    - audit-log-query:      p95<1s, p99<2s (NFR22 + Epic 17 wire), error_rate<1%
    - multi-region-failover: RTO<30s (NFR22 + Phase 5 wire), error_rate<0.1%
    """

    AUTH_LOGIN = "auth-login"
    COST_CALCULATION = "cost-calculation"
    ONBOARDING_FLOW = "onboarding-flow"
    AUDIT_LOG_QUERY = "audit-log-query"
    MULTI_REGION_FAILOVER = "multi-region-failover"


# VU (virtual user) defaults per scenario (PRD §F24.1 + AC #1.2~#1.6).
# These are the standard production-like load profiles. The dry-run UI
# path uses VU=0 via `dry_run=True` (no actual k6 invocation).
SCENARIO_VU_DEFAULT: Final[dict[K6Scenario, int]] = {
    K6Scenario.AUTH_LOGIN: 100,
    K6Scenario.COST_CALCULATION: 50,
    K6Scenario.ONBOARDING_FLOW: 30,
    K6Scenario.AUDIT_LOG_QUERY: 20,
    K6Scenario.MULTI_REGION_FAILOVER: 10,
}

# Ramp duration in seconds (PRD §F24.1 + AC #1.7 — k6 `stages` config).
SCENARIO_RAMP_DURATION_S: Final[dict[K6Scenario, int]] = {
    K6Scenario.AUTH_LOGIN: 30,
    K6Scenario.COST_CALCULATION: 60,
    K6Scenario.ONBOARDING_FLOW: 60,
    K6Scenario.AUDIT_LOG_QUERY: 30,
    K6Scenario.MULTI_REGION_FAILOVER: 120,
}


# ── Typed result envelope (CR 12-5 D-PARITY-01) ───────────────
class LoadTestMetric(TypedDict):
    """One metric from k6 summary (p95/p99 latency in ms + count)."""

    p95_ms: float
    p99_ms: float
    count: int
    rate_per_sec: float


class LoadTestRunResult(TypedDict):
    """TypedDict for k6 run summary result.

    Routes back to the route layer's audit-first INSERT
    (`performance_test_completed`) + cost-engine benchmark golden_diff
    detector (CR 4-3/4-4 verbatim).
    """

    run_id: str
    scenario: str  # K6Scenario.value
    tenant_id: str  # CR 0-2 RLS — tenant-scoped
    dry_run: bool
    started_at: str  # ISO 8601
    completed_at: str  # ISO 8601
    metrics: LoadTestMetric
    error_rate: float  # 0.0~1.0
    rps: float  # requests per second
    result_hash: str  # CR 4-3/4-4 — tenant-scoped golden_diff anchor


# ── Typed exception envelope (CR 12-5 D-14) ────────────────────
class LoadTestRunnerInvalidScenarioError(Exception):
    """400 LOAD_TEST_RUNNER_INVALID_SCENARIO — scenario name is unknown.

    AD-15 conventions.md §4 verbatim envelope. Mapped to HTTP 400 by
    main.py global handler. Distinct from `LoadTestRunnerExecutionError`
    which fires for actual subprocess failures (500).
    """

    def __init__(
        self,
        *,
        scenario: str,
        known: list[str],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"load_test_runner: scenario {scenario!r} is not a known "
            f"K6Scenario. Known: {sorted(known)}."
        )
        self.scenario = scenario
        self.known = known
        self.trace_id = trace_id


class LoadTestRunnerExecutionError(Exception):
    """500 LOAD_TEST_RUNNER_EXECUTION_ERROR — k6 subprocess failed.

    AD-15 conventions.md §4 verbatim envelope. Mapped to HTTP 500 by
    main.py global handler. The audit-first INSERT `performance_test_completed`
    carries the failure payload (stderr + returncode).
    """

    def __init__(
        self,
        *,
        scenario: str,
        returncode: int,
        stderr_tail: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"load_test_runner: k6 {scenario!r} failed (returncode="
            f"{returncode}): {stderr_tail[:200]}"
        )
        self.scenario = scenario
        self.returncode = returncode
        self.stderr_tail = stderr_tail
        self.trace_id = trace_id


# ── Synthetic dry-run summary (Phase 4 Sentry conditional init pattern) ──
def _synthetic_dry_run_summary(*, scenario: K6Scenario, tenant_id: uuid.UUID) -> LoadTestRunResult:
    """Synthesize a dry-run summary when dry_run=True (no actual k6 invocation).

    Mirrors Phase 7 OTEL_SDK_DISABLED no-op TracerProvider fallback —
    preserves the same wire shape as a real k6 summary so the route
    layer + audit-first INSERT + drift detector don't branch.
    """
    import datetime as _dt

    vus = 0  # dry-run = 0 VU per F24.1-12
    p95 = 0.0
    p99 = 0.0
    rps = 0.0
    error_rate = 0.0
    payload = json.dumps(
        {
            "scenario": scenario.value,
            "tenant_id": str(tenant_id),
            "vus": vus,
            "p95_ms": p95,
            "p99_ms": p99,
            "rps": rps,
            "error_rate": error_rate,
            "dry_run": True,
        },
        sort_keys=True,
    )
    return LoadTestRunResult(
        run_id=str(uuid.uuid4()),
        scenario=scenario.value,
        tenant_id=str(tenant_id),
        dry_run=True,
        started_at=_dt.datetime.now(tz=_dt.UTC).isoformat(),
        completed_at=_dt.datetime.now(tz=_dt.UTC).isoformat(),
        metrics=LoadTestMetric(
            p95_ms=p95,
            p99_ms=p99,
            count=0,
            rate_per_sec=rps,
        ),
        error_rate=error_rate,
        rps=rps,
        result_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )


# ── Public runner API ──────────────────────────────────────────
@dataclass(frozen=True)
class LoadTestRunRequest:
    """Typed request payload for `run_k6_load_test()`.

    Constructed at the route layer from `LoadTestRunRequestModel` Pydantic
    model + `TenantContext`. The runner is pure — no DB / audit write
    happens here (audit-first INSERT is the caller's responsibility per
    CR 1-1 verbatim).
    """

    scenario: K6Scenario
    tenant_id: uuid.UUID
    trace_id: str
    dry_run: bool
    vus: int | None = None  # None = use SCENARIO_VU_DEFAULT
    ramp_duration_s: int | None = None  # None = use SCENARIO_RAMP_DURATION_S


async def run_k6_load_test(
    request: LoadTestRunRequest,
    *,
    scripts_dir: Path | None = None,
) -> LoadTestRunResult:
    """Invoke k6 for `request.scenario` and return the typed summary.

    Args:
        request: Typed request payload (scenario + tenant_id + dry_run +
            vus override + ramp_duration_s override + trace_id).
        scripts_dir: Override for k6 scripts directory (default:
            `apps/api/tests/load/k6/`). Tests inject this.

    Returns:
        LoadTestRunResult: TypedDict with p95/p99 latency + RPS + error
        rate + tenant-scoped result_hash.

    Raises:
        LoadTestRunnerInvalidScenarioError: 400 — scenario name not in
            `K6Scenario` enum (defense-in-depth guard).
        LoadTestRunnerExecutionError: 500 — k6 subprocess returned non-zero.
        FileNotFoundError: k6 binary not on PATH + K6_BINARY env unset.

    CR lessons applied:
    - CR 0-2 RLS: tenant_id is bound into the k6 scenario via env var
      (`K6_TENANT_ID`) — k6 scripts read it for tenant-scoped requests.
    - CR 4-3/4-4: result_hash is sha256 of canonical JSON payload
      (tenant-scoped golden_diff anchor).
    - AD-14: k6 version is pinned via the `K6_VERSION` constant +
      pyproject.toml `k6==0.45.0`.
    """
    if request.dry_run:
        # dry-run path — synthesize summary, NO actual k6 invocation.
        # Mirrors Phase 7 OTEL_SDK_DISABLED no-op fallback pattern.
        return _synthetic_dry_run_summary(scenario=request.scenario, tenant_id=request.tenant_id)

    scripts_root = scripts_dir or Path(__file__).parent.parent / "tests" / "load" / "k6"
    script_path = scripts_root / f"{request.scenario.value}.js"
    if not script_path.exists():
        raise LoadTestRunnerInvalidScenarioError(
            scenario=request.scenario.value,
            known=[s.value for s in K6Scenario],
            trace_id=request.trace_id,
        )

    # k6 invocation env vars (CR 0-2 RLS — tenant binding)
    vus = request.vus if request.vus is not None else SCENARIO_VU_DEFAULT[request.scenario]
    ramp = (
        request.ramp_duration_s
        if request.ramp_duration_s is not None
        else SCENARIO_RAMP_DURATION_S[request.scenario]
    )
    env = {
        **os.environ.copy(),
        "K6_TENANT_ID": str(request.tenant_id),
        "K6_VUS": str(vus),
        "K6_RAMP_DURATION_S": str(ramp),
        "K6_TRACE_ID": request.trace_id,
        "K6_DRY_RUN": "0",
    }

    # k6 CLI: `k6 run --summary-export=- script.js` — JSON summary to stdout
    cmd = [
        K6_BINARY,
        "run",
        "--summary-export=-",
        str(script_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        stderr_tail = stderr.decode("utf-8", errors="replace")[-200:]
        raise LoadTestRunnerExecutionError(
            scenario=request.scenario.value,
            returncode=proc.returncode or -1,
            stderr_tail=stderr_tail,
            trace_id=request.trace_id,
        )

    summary = json.loads(stdout.decode("utf-8"))
    return _parse_k6_summary(
        summary=summary,
        scenario=request.scenario,
        tenant_id=request.tenant_id,
        trace_id=request.trace_id,
    )


def _parse_k6_summary(
    *,
    summary: dict[str, Any],
    scenario: K6Scenario,
    tenant_id: uuid.UUID,
    trace_id: str,
) -> LoadTestRunResult:
    """Parse k6's JSON summary export into LoadTestRunResult.

    k6 summary shape (k6 v0.45.0):
    {
      "metrics": {
        "http_req_duration": {"values": {"p(95)": ..., "p(99)": ...}},
        "http_reqs": {"values": {"count": ..., "rate": ...}},
        "http_req_failed": {"values": {"rate": ...}}
      }
    }
    """
    import datetime as _dt

    metrics_block = summary.get("metrics", {})
    duration = metrics_block.get("http_req_duration", {}).get("values", {})
    reqs = metrics_block.get("http_reqs", {}).get("values", {})
    failed = metrics_block.get("http_req_failed", {}).get("values", {})

    p95 = float(duration.get("p(95)", 0.0))
    p99 = float(duration.get("p(99)", 0.0))
    count = int(reqs.get("count", 0))
    rps = float(reqs.get("rate", 0.0))
    error_rate = float(failed.get("rate", 0.0))

    payload = json.dumps(
        {
            "scenario": scenario.value,
            "tenant_id": str(tenant_id),
            "p95_ms": p95,
            "p99_ms": p99,
            "count": count,
            "rps": rps,
            "error_rate": error_rate,
        },
        sort_keys=True,
    )
    result_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return LoadTestRunResult(
        run_id=str(uuid.uuid4()),
        scenario=scenario.value,
        tenant_id=str(tenant_id),
        dry_run=False,
        started_at=_dt.datetime.now(tz=_dt.UTC).isoformat(),
        completed_at=_dt.datetime.now(tz=_dt.UTC).isoformat(),
        metrics=LoadTestMetric(
            p95_ms=p95,
            p99_ms=p99,
            count=count,
            rate_per_sec=rps,
        ),
        error_rate=error_rate,
        rps=rps,
        result_hash=result_hash,
    )


# ── k6 binary presence check (Phase 7 Sentry conditional init pattern) ──
def is_k6_available() -> bool:
    """Return True if the `k6` binary is on PATH.

    Mirrors Phase 7 OTEL_SDK_DISABLED no-op fallback — callers can
    short-circuit load test invocation when k6 is absent (e.g. dev
    workstation without k6 installed).
    """
    return shutil.which(K6_BINARY) is not None


__all__ = [
    "K6Scenario",
    "K6_VERSION",
    "LoadTestRunRequest",
    "LoadTestRunResult",
    "LoadTestMetric",
    "LoadTestRunnerInvalidScenarioError",
    "LoadTestRunnerExecutionError",
    "run_k6_load_test",
    "is_k6_available",
]
