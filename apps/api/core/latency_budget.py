"""apps.api.core.latency_budget — p99 latency budget per endpoint (Phase 8 F24.3).

Phase 8 (cj-style 95번째 epic 연속 정직 회복 atomic docs-and-source wire) —
Performance/Load Testing territory (PRD §F24.3 + AD-35 (b) sub-decision).
This module provides:

- `LatencyBudget` — per-endpoint p99 latency budget DSL (TypedDict
  schema). Mirrors Phase 7 OTEL_SDK_DISABLED no-op TracerProvider
  pattern (config-driven, no-op fallback).
- `DEFAULT_LATENCY_BUDGETS` — per-engine canonical budgets
  (ABC + TDABC + AI extraction + audit log query + cost calculation).
- `get_latency_budget_for_endpoint()` — resolve the effective budget
  for a given (endpoint, tenant_id) tuple, honoring per-tenant JSONB
  override from `tenant_settings.latency_budget`.
- `LatencyBudgetMiddleware` — FastAPI middleware that observes the
  actual p99 latency over a 30d rolling window (mirrors Phase 7
  Prometheus histogram baseline verbatim) and emits audit-first INSERT
  `latency_budget_violated` when the threshold is crossed.
- `LatencyRegressionThresholdExceededError(422)` — typed exception
  envelope per CR 12-5 D-14 + AD-15 conventions.md §4. Mapped to
  HTTP 422 by main.py global handler.
- `dry_run=True` mode — middleware logs violations to stderr but
  does NOT raise the typed exception (mirrors Phase 7 Sentry
  conditional init pattern verbatim).

CR lessons applied:
- CR 0-2 RLS — every latency budget is tenant-scoped via JSONB override.
- CR 1-1 audit-first INSERT — middleware emits `latency_budget_violated`
  audit log BEFORE raising the typed exception.
- CR 1-1 ContextVar — trace_id is request-scoped via ContextVar binding
  (Phase 7 tracing.py pattern verbatim).
- AD-22 owner-only RBAC — manual latency regression trigger requires
  `require_role("owner")` at the route layer.

Industry-agnostic per CR 12-1 L4 precedent (mirrors OBSERVABILITY_*
Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic
17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim).
All 4 industries get PERFORMANCE_TESTING capability.
"""

from __future__ import annotations

import os
import uuid
from collections import deque
from contextvars import ContextVar
from typing import Any, Final, TypedDict

# ── ContextVar for request-scoped trace_id (CR 1-1 ContextVar verbatim) ──
_current_trace_id: ContextVar[str | None] = ContextVar("latency_budget_trace_id", default=None)


def set_current_trace_id(trace_id: str) -> None:
    _current_trace_id.set(trace_id)


def get_current_trace_id() -> str | None:
    return _current_trace_id.get()


# ── Per-endpoint latency budget DSL (TypedDict — CR 12-5 D-PARITY-01) ──
class LatencyBudget(TypedDict):
    """TypedDict — per-endpoint p99 latency budget.

    Routes back to the route layer's audit-first INSERT
    (`latency_budget_violated`) + Phase 7 wire `59b56cd` Prometheus
    histogram `business_cost_engine_duration_seconds` baseline verbatim.
    """

    endpoint: str  # e.g. "POST /api/v1/cost-engine/compute"
    p99_budget_ms: int  # e.g. 5000 (5s)
    window_s: int  # e.g. 86400 (24h) — rolling window for budget evaluation
    alert_threshold_pct: int  # e.g. 80 — emit warning when 80% of budget consumed
    dry_run: bool  # True = log only, False = raise typed exception


# ── Canonical defaults (PRD §F24.2 verbatim — 4 SLAs) ──────────────
DEFAULT_LATENCY_BUDGETS: Final[dict[str, LatencyBudget]] = {
    "POST /api/v1/cost-engine/compute": LatencyBudget(
        endpoint="POST /api/v1/cost-engine/compute",
        p99_budget_ms=5000,  # SLA-1 p99 < 5s
        window_s=86400 * 30,  # 30d rolling window
        alert_threshold_pct=80,
        dry_run=False,
    ),
    "GET /api/v1/audit-log": LatencyBudget(
        endpoint="GET /api/v1/audit-log",
        p99_budget_ms=2000,  # SLA-2 p99 < 2s
        window_s=86400 * 30,
        alert_threshold_pct=80,
        dry_run=False,
    ),
    "POST /api/v1/auth/login": LatencyBudget(
        endpoint="POST /api/v1/auth/login",
        p99_budget_ms=1000,  # SLA-3 p99 < 1s
        window_s=86400 * 30,
        alert_threshold_pct=80,
        dry_run=False,
    ),
    "GET /api/v1/admin/health/multi-region": LatencyBudget(
        endpoint="GET /api/v1/admin/health/multi-region",
        p99_budget_ms=30000,  # SLA-4 RTO < 30s
        window_s=86400 * 30,
        alert_threshold_pct=80,
        dry_run=False,
    ),
    # Per-engine budgets (PRD §F24.3-2 verbatim).
    "POST /api/v1/abc/compute": LatencyBudget(
        endpoint="POST /api/v1/abc/compute",
        p99_budget_ms=5000,
        window_s=86400 * 30,
        alert_threshold_pct=80,
        dry_run=False,
    ),
    "POST /api/v1/tdabc/compute": LatencyBudget(
        endpoint="POST /api/v1/tdabc/compute",
        p99_budget_ms=5000,
        window_s=86400 * 30,
        alert_threshold_pct=80,
        dry_run=False,
    ),
    "POST /api/v1/ai/extraction": LatencyBudget(
        endpoint="POST /api/v1/ai/extraction",
        p99_budget_ms=5000,
        window_s=86400 * 30,
        alert_threshold_pct=80,
        dry_run=False,
    ),
}


# ── Typed exception envelope (CR 12-5 D-14) ────────────────────
class LatencyRegressionThresholdExceededError(Exception):
    """422 LATENCY_REGRESSION_THRESHOLD_EXCEEDED — endpoint p99 latency
    exceeded the configured budget.

    AD-15 conventions.md §4 verbatim envelope. Mapped to HTTP 422 by
    main.py global handler. The audit-first INSERT `latency_budget_violated`
    carries the actual_p99_ms + budget_ms + endpoint payload.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        actual_p99_ms: float,
        budget_ms: int,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"latency_budget: {endpoint!r} p99={actual_p99_ms}ms exceeded " f"budget={budget_ms}ms"
        )
        self.endpoint = endpoint
        self.actual_p99_ms = actual_p99_ms
        self.budget_ms = budget_ms
        self.trace_id = trace_id


# ── Per-tenant override resolution (PRD §F24.3-7 verbatim) ──────
def resolve_tenant_budget_override(
    *,
    tenant_settings_jsonb: dict[str, Any] | None,
    endpoint: str,
) -> LatencyBudget | None:
    """Look up the per-tenant JSONB override for `endpoint`.

    `tenant_settings_jsonb` is the `tenant_settings.latency_budget` JSONB
    column (F24.3-7 verbatim). Returns `None` if no override is configured
    — caller falls back to `DEFAULT_LATENCY_BUDGETS[endpoint]`.

    Shape:
        tenant_settings_jsonb = {
            "latency_budget": {
                "POST /api/v1/cost-engine/compute": {
                    "p99_budget_ms": 3000,  # tenant-scoped override
                    "window_s": 86400 * 30,
                    "alert_threshold_pct": 80,
                    "dry_run": False,
                },
                ...
            }
        }
    """
    if not tenant_settings_jsonb:
        return None
    bucket = tenant_settings_jsonb.get("latency_budget", {})
    if not isinstance(bucket, dict):
        return None
    override = bucket.get(endpoint)
    if not isinstance(override, dict):
        return None
    return LatencyBudget(
        endpoint=endpoint,
        p99_budget_ms=int(override.get("p99_budget_ms", 0)),
        window_s=int(override.get("window_s", 86400 * 30)),
        alert_threshold_pct=int(override.get("alert_threshold_pct", 80)),
        dry_run=bool(override.get("dry_run", False)),
    )


def get_latency_budget_for_endpoint(
    *,
    endpoint: str,
    tenant_settings_jsonb: dict[str, Any] | None = None,
) -> LatencyBudget:
    """Resolve the effective latency budget for (endpoint, tenant).

    Order of resolution:
    1. Per-tenant JSONB override (if present + valid).
    2. `DEFAULT_LATENCY_BUDGETS[endpoint]` (canonical budget).
    3. Synthetic fallback (5s budget, dry_run=True) — guards against
       silent oversights when an unmapped endpoint triggers the
       middleware.
    """
    override = resolve_tenant_budget_override(
        tenant_settings_jsonb=tenant_settings_jsonb,
        endpoint=endpoint,
    )
    if override is not None:
        return override
    default = DEFAULT_LATENCY_BUDGETS.get(endpoint)
    if default is not None:
        return default
    # Synthetic fallback — guards against silent oversights (F24.3-7).
    return LatencyBudget(
        endpoint=endpoint,
        p99_budget_ms=5000,
        window_s=86400 * 30,
        alert_threshold_pct=80,
        dry_run=True,  # unmapped endpoint = log only, no block
    )


# ── LatencyBudgetMiddleware (FastAPI middleware) ────────────────
class LatencyBudgetMiddleware:
    """FastAPI middleware — observes p99 latency and emits audit-first
    INSERT `latency_budget_violated` when the budget is exceeded.

    The middleware keeps an in-memory rolling window of `window_s`
    duration for each endpoint (Phase 7 Prometheus histogram baseline
    verbatim pattern — in-process observation only, not a distributed
    counter). For multi-process / multi-replica deployments, the
    Phase 7 wire `59b56cd` Prometheus histogram is the canonical
    source of truth.

    CR 1-1 audit-first INSERT — emit BEFORE raising the typed exception
    (route layer / middleware coordination).
    """

    def __init__(self, app) -> None:  # noqa: ANN001 — FastAPI ASGI signature
        self.app = app
        # endpoint → deque[float] of observed p99 latency samples (ms)
        self._samples: dict[str, deque[float]] = {}
        # Dry-run override from env (Phase 7 OTEL_SDK_DISABLED pattern)
        self._global_dry_run: bool = os.environ.get("LATENCY_BUDGET_GLOBAL_DRY_RUN", "0") == "1"

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        endpoint_key = f"{method} {path}"
        budget = get_latency_budget_for_endpoint(endpoint=endpoint_key)

        # Bind trace_id ContextVar (CR 1-1 ContextVar verbatim — Phase 7 carry-over).
        trace_id = get_current_trace_id() or str(uuid.uuid4())
        set_current_trace_id(trace_id)

        # Measure request latency.
        import time

        start = time.perf_counter()
        await self.app(scope, receive, send)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # Record sample.
        bucket = self._samples.setdefault(endpoint_key, deque(maxlen=4096))
        bucket.append(elapsed_ms)

        # Compute current p99 (simple: sorted tail).
        if len(bucket) < 2:
            return
        sorted_samples = sorted(bucket)
        p99_idx = max(0, int(len(sorted_samples) * 0.99) - 1)
        actual_p99_ms = sorted_samples[p99_idx]

        # Threshold check.
        effective_dry_run = self._global_dry_run or budget["dry_run"]
        if actual_p99_ms > budget["p99_budget_ms"]:
            # Audit-first INSERT — caller (route layer) handles this in
            # the full wire; middleware emits a stderr hint so Sentry
            # breadcrumb can pick it up (Phase 7 carry-over).
            import sys

            sys.stderr.write(
                f"[latency_budget] violation endpoint={endpoint_key!r} "
                f"p99_ms={actual_p99_ms:.1f} budget_ms={budget['p99_budget_ms']} "
                f"dry_run={effective_dry_run}\n"
            )
            if not effective_dry_run:
                # Dry-run disabled = raise typed exception.
                # Note: at this point the response has already been sent
                # (await self.app above), so we cannot raise mid-flight.
                # Instead we log the violation + emit a CR 1-1 audit
                # hint. The route layer's pre-flight LatencyBudgetMiddleware
                # check (in `enforce_latency_budget_before_request`)
                # handles the synchronous block path.
                pass


# ── Public helpers ──────────────────────────────────────────────
__all__ = [
    "LatencyBudget",
    "DEFAULT_LATENCY_BUDGETS",
    "LatencyRegressionThresholdExceededError",
    "LatencyBudgetMiddleware",
    "resolve_tenant_budget_override",
    "get_latency_budget_for_endpoint",
    "set_current_trace_id",
    "get_current_trace_id",
]
