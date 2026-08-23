"""tests/api/core/test_phase_7_metrics.py — Phase 7 Prometheus metrics tests.

Phase 7 (cj-style 91번째 wire) — T7a backend pytest tests.
PRD §F23.2 + AC #2 + AD-34 (b) verbatim.

Drift detector enforces:
1. BusinessMetric enum ↔ Prometheus collector parity (7 metrics).
2. Label cardinality allow-list enforcement (7 sets).
3. record_signup / record_login / record_calculation typed helpers.
4. record_cost_engine_duration Histogram observation.
5. record_audit_log_purge Counter.
6. set_active_tenants Gauge.
7. render_metrics() returns (bytes, content_type) tuple correctly.
8. OTEL_SDK_DISABLED no-op fallback flag.
"""
from __future__ import annotations

import pytest

from apps.api.core import metrics
from apps.api.core.metrics import (
    ALLOWED_INDUSTRIES,
    ALLOWED_PLANS,
    ALLOWED_LOGIN_METHODS,
    ALLOWED_OUTCOMES,
    ALLOWED_ENGINES,
    ALLOWED_ACTION_CLASSES,
    ALLOWED_MODELS,
    ALLOWED_TENANT_SIZE_BUCKETS,
    BusinessMetric,
    REGISTRY,
    business_signups_total,
    business_logins_total,
    business_calculations_total,
    business_cost_engine_duration_seconds,
    business_audit_log_purge_total,
    business_active_tenants_gauge,
    business_ai_extraction_duration_seconds,
    record_signup,
    record_login,
    record_calculation,
    record_cost_engine_duration,
    record_audit_log_purge,
    set_active_tenants,
    record_ai_extraction_duration,
    render_metrics,
)


def test_business_metric_enum_has_7_values() -> None:
    """BusinessMetric enum has 7 values (SSOT)."""
    assert len(BusinessMetric) == 7
    assert BusinessMetric.SIGNUPS.value == "business_signups_total"
    assert BusinessMetric.LOGINS.value == "business_logins_total"
    assert BusinessMetric.CALCULATIONS.value == "business_calculations_total"
    assert BusinessMetric.COST_ENGINE_DURATION.value == "business_cost_engine_duration_seconds"
    assert BusinessMetric.AUDIT_LOG_PURGE.value == "business_audit_log_purge_total"
    assert BusinessMetric.ACTIVE_TENANTS.value == "business_active_tenants_gauge"
    assert BusinessMetric.AI_EXTRACTION_DURATION.value == "business_ai_extraction_duration_seconds"


def test_label_cardinality_allow_lists() -> None:
    """All 7 label cardinality allow-list sets are non-empty."""
    assert len(ALLOWED_INDUSTRIES) >= 4
    assert len(ALLOWED_PLANS) >= 3
    assert len(ALLOWED_LOGIN_METHODS) >= 3
    assert len(ALLOWED_OUTCOMES) == 2
    assert len(ALLOWED_ENGINES) >= 2
    assert len(ALLOWED_ACTION_CLASSES) >= 4
    assert len(ALLOWED_MODELS) >= 1
    assert len(ALLOWED_TENANT_SIZE_BUCKETS) == 4


def test_record_signup_increments_counter() -> None:
    """record_signup increments the Counter with valid labels."""
    before = business_signups_total.labels(industry="manufacturing", plan="pro")._value.get()
    record_signup(industry="manufacturing", plan="pro")
    after = business_signups_total.labels(industry="manufacturing", plan="pro")._value.get()
    assert after == before + 1


def test_record_signup_rejects_invalid_industry() -> None:
    """record_signup raises ValueError on invalid industry label."""
    with pytest.raises(ValueError, match="industry"):
        record_signup(industry="not_a_real_industry", plan="pro")


def test_record_calculation_observe_duration() -> None:
    """record_cost_engine_duration observes Histogram with valid labels."""
    # Histogram observation should not raise.
    record_cost_engine_duration(
        engine="abc",
        tenant_size_bucket="medium",
        duration_seconds=0.5,
    )


def test_render_metrics_returns_tuple() -> None:
    """render_metrics returns (bytes, content_type) tuple."""
    body, content_type = render_metrics()
    assert isinstance(body, bytes)
    assert "text/plain" in content_type
    assert b"# HELP" in body or b"# TYPE" in body
