"""tests/api/core/test_phase_7_tracing.py — Phase 7 OpenTelemetry tracing tests.

Phase 7 (cj-style 91번째 wire) — T7a backend pytest tests.
PRD §F23.1 + AC #1 + AD-34 (a) verbatim.

Drift detector enforces:
1. parse_traceparent returns (version, trace_id, span_id, flags) tuple.
2. parse_traceparent returns None on malformed input.
3. format_traceparent produces W3C-spec format string.
4. get_current_trace_id ContextVar returns None by default.
5. get_current_trace_id ContextVar returns set value after bind (CR 1-1).
6. OTEL_SDK_DISABLED flag exists and is a bool.
"""
from __future__ import annotations

import pytest

from apps.api.core.tracing import (
    OTEL_SDK_DISABLED,
    _current_trace_id,
    format_traceparent,
    get_current_trace_id,
    parse_traceparent,
)


def test_parse_traceparent_valid() -> None:
    """parse_traceparent returns 4-tuple on valid W3C input."""
    parsed = parse_traceparent(
        "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    )
    assert parsed is not None
    version, trace_id, span_id, flags = parsed
    assert version == "00"
    assert trace_id == "0af7651916cd43dd8448eb211c80319c"
    assert span_id == "b7ad6b7169203331"
    assert flags == "01"


def test_parse_traceparent_invalid_format() -> None:
    """parse_traceparent returns None on malformed input."""
    assert parse_traceparent("not-a-valid-traceparent") is None
    assert parse_traceparent("") is None
    assert parse_traceparent("00-badtraceid-badspanid-01") is None


def test_format_traceparent_produces_w3c_string() -> None:
    """format_traceparent produces canonical W3C Trace Context header."""
    out = format_traceparent("00", "0af7651916cd43dd8448eb211c80319c", "b7ad6b7169203331", "01")
    assert out == "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"


def test_current_trace_id_default_none() -> None:
    """get_current_trace_id returns None when no ContextVar bound."""
    # Reset to ensure clean state.
    _current_trace_id.set(None)
    assert get_current_trace_id() is None


def test_current_trace_id_contextvar_binding() -> None:
    """get_current_trace_id returns set value after ContextVar bind (CR 1-1)."""
    token = _current_trace_id.set("0af7651916cd43dd8448eb211c80319c")
    try:
        assert get_current_trace_id() == "0af7651916cd43dd8448eb211c80319c"
    finally:
        _current_trace_id.reset(token)


def test_otel_sdk_disabled_is_bool() -> None:
    """OTEL_SDK_DISABLED is a bool (Phase 4 Sentry conditional init mirror)."""
    assert isinstance(OTEL_SDK_DISABLED, bool)
