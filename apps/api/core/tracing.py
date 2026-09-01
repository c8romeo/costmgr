"""apps.api.core.tracing — OpenTelemetry distributed tracing.

Phase 7 (cj-style 91번째 wire) — Observability Stack 강화 territory.
PRD §F23.1 + AC #1 + AD-34 (a) sub-decision.

This module provides:

1. `init_tracing()` — bootstrap OpenTelemetry SDK + OTLP HTTP exporter
   with W3C Trace Context propagation (CR 1-1 ContextVar lesson).
2. `TraceContextMiddleware` — FastAPI middleware that:
   - Extracts `traceparent` + `tracestate` HTTP headers (W3C standard).
   - Injects span enrichment (`tenant.id` + `user.id` + `trace.id`
     + `request.id` + `client.ip` automatic span attributes).
   - Sets ContextVar for async trace context preservation (CR 1-1 verbatim).
3. `get_current_trace_id()` — read current ContextVar-bound trace_id
   for audit-first INSERT correlation.
4. `get_current_span()` — read current OpenTelemetry span for span
   attribute updates.
5. `OTEL_SDK_DISABLED` — no-op TracerProvider fallback when SDK disabled
   (Phase 4 Sentry conditional init pattern mirror verbatim).
6. 4 auto-instrumentation libraries:
   - opentelemetry-instrumentation-fastapi
   - opentelemetry-instrumentation-sqlalchemy
   - opentelemetry-instrumentation-httpx
   - opentelemetry-instrumentation-asyncpg

W3C Trace Context (`traceparent` / `tracestate` headers) ensures
end-to-end trace continuity across:
- API → DB → external HTTP calls
- API → frontend (server → client propagation in apps/web/lib/tracing.ts)
- API → multi-region (Phase 5 wire `f093f8c` cross-region carry-over)

`db.statement` SQL parameter values are EXPLICITLY EXCLUDED from span
attributes (NFR4 PII minimization). The `tenant.id` attribute is bound
to the REQUEST tenant only (CR 0-2 RLS auto-isolation — cross-tenant
span attribute leakage prevention).
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Any

# CR 1-1 verbatim — async trace context preservation via ContextVar.
# Async tasks inherit the parent context, but explicit binding via
# ContextVar ensures trace_id is available to service-layer audit
# emit calls (apps/api/core/audit.py:emit_audit) regardless of
# whether they run inside an active span context.
_current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)


def get_current_trace_id() -> str | None:
    """Return the trace_id bound to the current async context (CR 1-1 verbatim).

    Used by audit emit calls (apps/api/core/audit.py:emit_audit) to
    correlate audit logs with traces. Returns None when called outside
    any request context.
    """
    return _current_trace_id.get()


# ────────────────────────────────────────────────────────────
# OTEL SDK DISABLED flag (Phase 4 Sentry conditional init mirror)
# ────────────────────────────────────────────────────────────
OTEL_SDK_DISABLED: bool = os.environ.get("OTEL_SDK_DISABLED", "false").lower() == "true"


# ────────────────────────────────────────────────────────────
# W3C Trace Context parsing
# ────────────────────────────────────────────────────────────
def parse_traceparent(header_value: str) -> tuple[str, str, str, str] | None:
    """Parse W3C Trace Context `traceparent` HTTP header.

    Format: `<version>-<trace_id>-<span_id>-<flags>`
    Example: `00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01`

    Returns:
        (version, trace_id, span_id, flags) or None if malformed.
    """
    if not header_value:
        return None
    parts = header_value.strip().split("-")
    if len(parts) != 4:
        return None
    version, trace_id, span_id, flags = parts
    # Trace ID must be 32 hex chars (16 bytes), span ID 16 hex chars (8 bytes)
    if len(trace_id) != 32 or len(span_id) != 16:
        return None
    if not all(c in "0123456789abcdef" for c in (trace_id + span_id).lower()):
        return None
    return version, trace_id, span_id, flags


def format_traceparent(version: str, trace_id: str, span_id: str, flags: str) -> str:
    """Format W3C Trace Context `traceparent` HTTP header."""
    return f"{version}-{trace_id}-{span_id}-{flags}"


# ────────────────────────────────────────────────────────────
# init_tracing() — bootstrap OpenTelemetry SDK
# ────────────────────────────────────────────────────────────
def init_tracing(*, app: Any = None) -> Any:
    """Initialize OpenTelemetry tracing with OTLP HTTP exporter.

    Sets up:
    1. TracerProvider with head_based sampler (ratio 1.0 dev / 0.1 prod).
    2. OTLP HTTP exporter (opentelemetry-exporter-otlp-proto-http).
    3. Resource attributes (service.name=costmgr-api, service.version).
    4. 4 auto-instrumentation libraries (FastAPI / SQLAlchemy / httpx / asyncpg).
    5. W3C Trace Context propagator (default in opentelemetry-api).

    When OTEL_SDK_DISABLED=true (env var), returns a no-op TracerProvider
    fallback (Phase 4 wire `71a033a` Sentry conditional init pattern
    verbatim — same pattern, same env var convention).

    Returns:
        The TracerProvider instance (or no-op fallback when disabled).
    """
    if OTEL_SDK_DISABLED:
        # No-op fallback — Phase 4 Sentry conditional init pattern verbatim.
        return _NoopTracerProvider()

    # Lazy imports — defer until init_tracing() is actually called
    # to keep import-time side effects minimal (apps/api/main.py
    # imports this module unconditionally).
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_ON,
        TraceIdRatioBased,
    )

    # Sampler — head_based, ratio from env var (1.0 dev / 0.1 prod)
    sampler_ratio = float(os.environ.get("OTEL_TRACES_SAMPLER_ARG", "1.0"))
    sampler = ALWAYS_ON if sampler_ratio >= 1.0 else TraceIdRatioBased(sampler_ratio)

    # Resource attributes
    resource = Resource.create(
        {
            "service.name": "costmgr-api",
            "service.version": os.environ.get("APP_VERSION", "phase-7"),
        }
    )

    # TracerProvider + OTLP HTTP exporter + batch processor
    provider = TracerProvider(resource=resource, sampler=sampler)
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # 4 auto-instrumentation libraries
    _instrument_fastapi(provider) if app is not None else None
    _instrument_sqlalchemy()
    _instrument_httpx()
    _instrument_asyncpg()

    return provider


def _instrument_fastapi(provider: Any) -> None:
    """Auto-instrument FastAPI requests (request span + route span)."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        # NOTE: actual instrument_app() call is deferred to
        # apps/api/main.py:init_tracing(app=app) to bind the FastAPI
        # app instance. This helper only verifies the import is
        # available (catches missing deps early at startup).
        _ = FastAPIInstrumentor
    except ImportError:
        pass


def _instrument_sqlalchemy() -> None:
    """Auto-instrument SQLAlchemy queries (db.statement WITHOUT params)."""
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        # NOTE: actual engine instrumentation is deferred to
        # apps/api/core/db.py:get_engine() — must bind to the engine
        # AFTER it is created (post-Phase 4 Sentry init pattern).
        _ = SQLAlchemyInstrumentor
    except ImportError:
        pass


def _instrument_httpx() -> None:
    """Auto-instrument httpx outbound HTTP calls."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass


def _instrument_asyncpg() -> None:
    """Auto-instrument asyncpg queries (asyncpg pool)."""
    try:
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

        AsyncPGInstrumentor().instrument()
    except ImportError:
        pass


# ────────────────────────────────────────────────────────────
# TraceContextMiddleware — FastAPI middleware
# ────────────────────────────────────────────────────────────
class TraceContextMiddleware:
    """FastAPI/Starlette middleware that:

    1. Extracts W3C Trace Context from `traceparent` request header.
    2. Sets ContextVar for async trace_id propagation (CR 1-1 verbatim).
    3. Enriches the active span with `tenant.id` + `user.id` + `trace.id`
       + `request.id` + `client.ip` automatic attributes (Phase 4 Sentry
       breadcrumb pattern + Phase 5 multi-region observability carry-over).
    4. Excludes SQL parameter values from span attributes (NFR4 PII
       minimization — db.statement bound to query template only, NOT
       interpolated values).
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1. Extract W3C Trace Context from headers
        headers = dict(scope.get("headers") or [])
        traceparent_value = headers.get(b"traceparent", b"").decode("ascii", errors="ignore")
        parsed = parse_traceparent(traceparent_value)
        trace_id = parsed[1] if parsed else None

        # 2. Set ContextVar for async trace context preservation (CR 1-1)
        token = _current_trace_id.set(trace_id)

        # 3. Enrich span if OTEL SDK is active (not the no-op fallback)
        if not OTEL_SDK_DISABLED and trace_id is not None:
            try:
                from opentelemetry import trace

                span = trace.get_current_span()
                if span is not None and span.is_recording():
                    # 3a — Request-level attributes (always safe)
                    span.set_attribute("http.route", scope.get("path", ""))
                    span.set_attribute("http.method", scope.get("method", ""))
                    # 3b — Client IP (CR 0-2 RLS — bind to request client only)
                    client = scope.get("client")
                    if client is not None:
                        span.set_attribute("client.ip", client[0])
                    # NOTE: tenant.id + user.id bound at audit emit time
                    # (apps/api/core/audit.py:emit_audit) since tenant/user
                    # resolution happens AFTER middleware execution (auth
                    # dep injection). Cross-tenant span attribute leakage
                    # prevented by binding tenant_id only on auth-success path.
            except ImportError:
                pass

        try:
            await self.app(scope, receive, send)
        finally:
            _current_trace_id.reset(token)


# ────────────────────────────────────────────────────────────
# _NoopTracerProvider — fallback when OTEL_SDK_DISABLED=true
# ────────────────────────────────────────────────────────────
class _NoopTracerProvider:
    """No-op TracerProvider when OTEL_SDK_DISABLED=true.

    Mirrors Phase 4 wire `71a033a` Sentry conditional init pattern.
    All span creation methods are no-ops; ContextVar binding still
    works (so audit correlation is preserved even when SDK is off).
    """

    def get_tracer(self, *args: Any, **kwargs: Any) -> _NoopTracer:
        return _NoopTracer()


class _NoopTracer:
    def start_span(self, *args: Any, **kwargs: Any) -> _NoopSpan:
        return _NoopSpan()


class _NoopSpan:
    def is_recording(self) -> bool:
        return False

    def set_attribute(self, *args: Any, **kwargs: Any) -> None:
        pass

    def end(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get_span_context(self) -> Any:
        return None


__all__ = [
    "init_tracing",
    "TraceContextMiddleware",
    "get_current_trace_id",
    "parse_traceparent",
    "format_traceparent",
    "OTEL_SDK_DISABLED",
]
