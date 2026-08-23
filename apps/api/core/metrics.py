"""apps.api.core.metrics — Prometheus custom metrics + Grafana dashboards.

Phase 7 (cj-style 91번째 wire) — Observability Stack 강화 territory.
PRD §F23.2 + AC #2 + AD-34 (b) sub-decision.

This module provides:

1. `BusinessMetric` — typed enum of business metric names (Counter / Histogram /
   Gauge).
2. `business_signups_total` — Counter: tenant signup events (industry, plan).
3. `business_logins_total` — Counter: login events (method, outcome).
4. `business_calculations_total` — Counter: calc engine executions
   (engine, outcome).
5. `business_cost_engine_duration_seconds` — Histogram: cost engine latency
   (engine, tenant_size_bucket).
6. `business_audit_log_purge_total` — Counter: audit log purge events
   (action_class — Phase 6 wire `24e1cd7` carry-over).
7. `business_active_tenants_gauge` — Gauge: active tenant count.
8. `business_ai_extraction_duration_seconds` — Histogram: AI extraction
   latency (model, outcome — Epic 10 carry-over).
9. `render_metrics()` — Prometheus exposition format bytes.
10. `OTEL_SDK_DISABLED` — Phase 4 Sentry conditional init pattern mirror
    (no-op TracerProvider fallback when observability SDK disabled).

Label cardinality is intentionally bounded: only enum-bound labels are
allowed (industry, plan, method, outcome, engine, action_class, model,
severity, tenant_size_bucket). Free-form `tenant_id` labels are
EXPLICITLY FORBIDDEN — Prometheus cardinality explosion + tenant info
leakage prevention (CR 0-2 RLS + NFR4 PII minimization).

Drift detector: tests/api/core/test_phase_7_metrics.py enforces
BusinessMetric enum ↔ Prometheus collector parity.
"""
from __future__ import annotations

import os
from enum import Enum
from typing import Final

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ────────────────────────────────────────────────────────────
# 1. Registry — single shared CollectorRegistry (AD-14 stack pin)
# ────────────────────────────────────────────────────────────
# Per Prometheus docs: a single CollectorRegistry per process is the
# canonical pattern. Multi-worker setups (gunicorn) would need
# multiprocess mode (PROMETHEUS_MULTIPROC_DIR) — out of scope for
# Phase 7 wire (single-worker FastAPI dev / uvicorn prod baseline).
REGISTRY: Final[CollectorRegistry] = CollectorRegistry()


# ────────────────────────────────────────────────────────────
# 2. BusinessMetric enum — typed SSOT
# ────────────────────────────────────────────────────────────
class BusinessMetric(str, Enum):
    """Business metric names (SSOT). Order = introduction order."""

    SIGNUPS = "business_signups_total"
    LOGINS = "business_logins_total"
    CALCULATIONS = "business_calculations_total"
    COST_ENGINE_DURATION = "business_cost_engine_duration_seconds"
    AUDIT_LOG_PURGE = "business_audit_log_purge_total"
    ACTIVE_TENANTS = "business_active_tenants_gauge"
    AI_EXTRACTION_DURATION = "business_ai_extraction_duration_seconds"


# ────────────────────────────────────────────────────────────
# 3. Label cardinality guards (enum-bound labels only)
# ────────────────────────────────────────────────────────────
# Industry — from packages.services.m0_onboarding.industry_menu.Industry
ALLOWED_INDUSTRIES: Final[frozenset[str]] = frozenset(
    {"manufacturing", "service", "mfg+service", "mfg+service+other"}
)

# Plan — from packages.services.m0_onboarding.plan_menu.Plan (CR 12-1 L4)
ALLOWED_PLANS: Final[frozenset[str]] = frozenset(
    {"free", "starter", "pro", "enterprise"}
)

# Login method
ALLOWED_LOGIN_METHODS: Final[frozenset[str]] = frozenset(
    {"password", "magic_link", "social_oauth", "sso_saml", "service_role"}
)

# Outcome (binary success/fail with explicit enum values)
ALLOWED_OUTCOMES: Final[frozenset[str]] = frozenset({"success", "failure"})

# Engine (calc engine type — Epic 1-4 carry-over)
ALLOWED_ENGINES: Final[frozenset[str]] = frozenset(
    {"abc", "tdabc", "opening_inventory", "reversal"}
)

# Action class — Phase 6 wire `24e1cd7` ActionClass enum values verbatim
ALLOWED_ACTION_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "tenant_settings",
        "auth",
        "two_factor_auth",
        "audit",
        "infra",
        "ai_extraction_executed",
        "ai_insight_cache_accessed",
        "observability",
    }
)

# AI extraction model — Epic 10 carry-over
ALLOWED_MODELS: Final[frozenset[str]] = frozenset(
    {"claude-sonnet-4.5", "claude-haiku-4.5", "fallback_regex"}
)

# Tenant size bucket (free-form tenant size is FORBIDDEN — buckets only)
ALLOWED_TENANT_SIZE_BUCKETS: Final[frozenset[str]] = frozenset(
    {"small", "medium", "large", "xlarge"}
)


def _validate_labels(label_name: str, value: str, allowed: frozenset[str]) -> None:
    """Raise ValueError if `value` is not in `allowed` cardinality set."""
    if value not in allowed:
        raise ValueError(
            f"metrics: invalid {label_name}={value!r}. "
            f"Allowed: {sorted(allowed)}. "
            f"Free-form labels are forbidden (Prometheus cardinality explosion "
            f"+ NFR4 PII minimization + tenant info leakage prevention)."
        )


# ────────────────────────────────────────────────────────────
# 4. Metric collectors (Counter / Histogram / Gauge)
# ────────────────────────────────────────────────────────────

# 4.1 — business_signups_total{industry, plan} Counter
business_signups_total: Final[Counter] = Counter(
    "business_signups_total",
    "Total tenant signup events (industry, plan) — Counter.",
    labelnames=("industry", "plan"),
    registry=REGISTRY,
)

# 4.2 — business_logins_total{method, outcome} Counter
business_logins_total: Final[Counter] = Counter(
    "business_logins_total",
    "Total login events (method, outcome) — Counter.",
    labelnames=("method", "outcome"),
    registry=REGISTRY,
)

# 4.3 — business_calculations_total{engine, outcome} Counter
business_calculations_total: Final[Counter] = Counter(
    "business_calculations_total",
    "Total calc engine executions (engine, outcome) — Counter.",
    labelnames=("engine", "outcome"),
    registry=REGISTRY,
)

# 4.4 — business_cost_engine_duration_seconds{engine, tenant_size_bucket} Histogram
# Buckets: 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s, 30s (NFR11 P95 ≤ 30s SLO)
_COST_ENGINE_BUCKETS: Final[tuple[float, ...]] = (
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
)
business_cost_engine_duration_seconds: Final[Histogram] = Histogram(
    "business_cost_engine_duration_seconds",
    "Cost engine execution duration seconds (engine, tenant_size_bucket) — Histogram.",
    labelnames=("engine", "tenant_size_bucket"),
    buckets=_COST_ENGINE_BUCKETS,
    registry=REGISTRY,
)

# 4.5 — business_audit_log_purge_total{action_class} Counter
# Phase 6 wire `24e1cd7` audit log retention carry-over — purge / archive /
# PII mask / cold-archive / personal-data-erased events.
business_audit_log_purge_total: Final[Counter] = Counter(
    "business_audit_log_purge_total",
    "Total audit log purge events (action_class) — Counter.",
    labelnames=("action_class",),
    registry=REGISTRY,
)

# 4.6 — business_active_tenants_gauge Gauge
business_active_tenants_gauge: Final[Gauge] = Gauge(
    "business_active_tenants_gauge",
    "Active tenant count — Gauge.",
    registry=REGISTRY,
)

# 4.7 — business_ai_extraction_duration_seconds{model, outcome} Histogram
# Buckets: 500ms, 1s, 2.5s, 5s, 10s, 30s, 60s (AI extraction can be slow)
_AI_EXTRACTION_BUCKETS: Final[tuple[float, ...]] = (
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    60.0,
)
business_ai_extraction_duration_seconds: Final[Histogram] = Histogram(
    "business_ai_extraction_duration_seconds",
    "AI extraction duration seconds (model, outcome) — Histogram.",
    labelnames=("model", "outcome"),
    buckets=_AI_EXTRACTION_BUCKETS,
    registry=REGISTRY,
)


# ────────────────────────────────────────────────────────────
# 5. Typed increment / observe helpers (label validation enforcement)
# ────────────────────────────────────────────────────────────
def record_signup(*, industry: str, plan: str) -> None:
    """Increment business_signups_total{industry, plan}.

    Raises ValueError if industry/plan not in cardinality-allowed enum set.
    """
    _validate_labels("industry", industry, ALLOWED_INDUSTRIES)
    _validate_labels("plan", plan, ALLOWED_PLANS)
    business_signups_total.labels(industry=industry, plan=plan).inc()


def record_login(*, method: str, outcome: str) -> None:
    """Increment business_logins_total{method, outcome}."""
    _validate_labels("method", method, ALLOWED_LOGIN_METHODS)
    _validate_labels("outcome", outcome, ALLOWED_OUTCOMES)
    business_logins_total.labels(method=method, outcome=outcome).inc()


def record_calculation(*, engine: str, outcome: str) -> None:
    """Increment business_calculations_total{engine, outcome}."""
    _validate_labels("engine", engine, ALLOWED_ENGINES)
    _validate_labels("outcome", outcome, ALLOWED_OUTCOMES)
    business_calculations_total.labels(engine=engine, outcome=outcome).inc()


def record_cost_engine_duration(
    *, engine: str, tenant_size_bucket: str, duration_seconds: float
) -> None:
    """Observe business_cost_engine_duration_seconds{engine, tenant_size_bucket}."""
    _validate_labels("engine", engine, ALLOWED_ENGINES)
    _validate_labels("tenant_size_bucket", tenant_size_bucket, ALLOWED_TENANT_SIZE_BUCKETS)
    business_cost_engine_duration_seconds.labels(
        engine=engine, tenant_size_bucket=tenant_size_bucket
    ).observe(duration_seconds)


def record_audit_log_purge(*, action_class: str) -> None:
    """Increment business_audit_log_purge_total{action_class}."""
    _validate_labels("action_class", action_class, ALLOWED_ACTION_CLASSES)
    business_audit_log_purge_total.labels(action_class=action_class).inc()


def set_active_tenants(count: int) -> None:
    """Set business_active_tenants_gauge."""
    if count < 0:
        raise ValueError(f"metrics: active_tenants count must be >= 0, got {count}")
    business_active_tenants_gauge.set(count)


def record_ai_extraction_duration(
    *, model: str, outcome: str, duration_seconds: float
) -> None:
    """Observe business_ai_extraction_duration_seconds{model, outcome}."""
    _validate_labels("model", model, ALLOWED_MODELS)
    _validate_labels("outcome", outcome, ALLOWED_OUTCOMES)
    business_ai_extraction_duration_seconds.labels(
        model=model, outcome=outcome
    ).observe(duration_seconds)


# ────────────────────────────────────────────────────────────
# 6. /metrics endpoint renderer
# ────────────────────────────────────────────────────────────
def render_metrics() -> tuple[bytes, str]:
    """Render Prometheus exposition format for the /metrics endpoint.

    Returns:
        (body, content_type) — body is the Prometheus exposition format
        bytes; content_type is the canonical `text/plain; version=0.0.4`
        MIME type from prometheus_client.CONTENT_TYPE_LATEST.

    Endpoint wiring: GET /api/v1/metrics (apps/api/main.py EXTENSION).
    """
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


# ────────────────────────────────────────────────────────────
# 7. Conditional init pattern mirror (Phase 4 Sentry)
# ────────────────────────────────────────────────────────────
# Phase 4 wire `71a033a` Sentry init conditional pattern — observability
# SDK can be disabled via env var (e.g. local dev without OTLP collector).
# When disabled, no-op TracerProvider fallback (Phase 4 Sentry conditional
# init pattern verbatim).
OTEL_SDK_DISABLED: Final[bool] = os.environ.get("OTEL_SDK_DISABLED", "false").lower() == "true"


__all__ = [
    "BusinessMetric",
    "REGISTRY",
    "OTEL_SDK_DISABLED",
    "ALLOWED_INDUSTRIES",
    "ALLOWED_PLANS",
    "ALLOWED_LOGIN_METHODS",
    "ALLOWED_OUTCOMES",
    "ALLOWED_ENGINES",
    "ALLOWED_ACTION_CLASSES",
    "ALLOWED_MODELS",
    "ALLOWED_TENANT_SIZE_BUCKETS",
    "business_signups_total",
    "business_logins_total",
    "business_calculations_total",
    "business_cost_engine_duration_seconds",
    "business_audit_log_purge_total",
    "business_active_tenants_gauge",
    "business_ai_extraction_duration_seconds",
    "record_signup",
    "record_login",
    "record_calculation",
    "record_cost_engine_duration",
    "record_audit_log_purge",
    "set_active_tenants",
    "record_ai_extraction_duration",
    "render_metrics",
]
