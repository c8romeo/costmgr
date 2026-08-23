/**
 * apps/web/lib/tracing.ts — OpenTelemetry Browser RUM tracing.
 *
 * Phase 7 (cj-style 91번째 wire) — Observability Stack 강화 territory.
 * PRD §F23.4 + AC #4 + AD-34 (d) sub-decision.
 *
 * **RSC boundary:** This module is CLIENT-ONLY (CR 1-1 verbatim). It
 * imports `@opentelemetry/sdk-trace-web` which depends on browser APIs
 * (window / document / performance). Importing it from a Server
 * Component or `instrumentation-node.ts` will crash the build.
 *
 * Provides:
 * 1. `initBrowserTracing()` — bootstrap OpenTelemetry Browser RUM SDK
 *    with Web Vitals auto-collection (LCP + FID + CLS + INP + TTFB).
 * 2. `recordWebVital(name, value)` — record a single Web Vital metric.
 * 3. `getBrowserTraceContext()` — return current W3C Trace Context for
 *    X-Trace-Id header propagation on outbound fetch.
 * 4. W3C Trace Context propagation: server → client (via `traceparent`
 *    response header) + client → server (X-Trace-Id on fetch).
 * 5. Custom span attributes: `user.tenant_id`, `user.role`,
 *    `user.industry`, `route.path`, `route.locale`.
 *
 * Span attributes do NOT include PII (NFR4 PII minimization):
 * - `user.email` is NEVER set (masking + audit log encryption carry-over).
 * - `client.ip` is NEVER set on the browser (only server-side).
 * - `tenant_id` is bound to the authenticated tenant only
 *   (cross-tenant span attribute leakage prevention).
 */
'use client';

import { trace, context, type Span, type Tracer } from '@opentelemetry/api';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import {
  BatchSpanProcessor,
  SimpleSpanProcessor,
} from '@opentelemetry/sdk-trace-base';
import { onLCP, onFID, onCLS, onINP, onTTFB, type Metric } from 'web-vitals';

// ────────────────────────────────────────────────────────────
// 1. Conditional init (Phase 4 Sentry conditional init mirror)
// ────────────────────────────────────────────────────────────
const OTEL_SDK_DISABLED: boolean =
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_OTEL_SDK_DISABLED === 'true') ||
  false;

let _provider: WebTracerProvider | null = null;
let _tracer: Tracer | null = null;

/**
 * Initialize OpenTelemetry Browser RUM tracing. Idempotent — repeated
 * calls return the same provider/tracer instance.
 *
 * @param otlpEndpoint - OTLP HTTP endpoint (default: /api/v1/observability/traces).
 */
export function initBrowserTracing(otlpEndpoint?: string): Tracer {
  if (OTEL_SDK_DISABLED) {
    // No-op fallback (Phase 4 Sentry conditional init pattern mirror).
    return _getNoopTracer();
  }
  if (_tracer !== null) {
    return _tracer;
  }

  const endpoint =
    otlpEndpoint ??
    (typeof process !== 'undefined'
      ? process.env?.NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT
      : undefined) ??
    '/api/v1/observability/traces';

  const resource = new Resource({
    'service.name': 'costmgr-web',
    'service.version':
      (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_APP_VERSION) ??
      'phase-7',
  });

  _provider = new WebTracerProvider({ resource });
  const exporter = new OTLPTraceExporter({ url: endpoint });
  // SimpleSpanProcessor for browser (immediate flush on visibility change).
  _provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
  _provider.register();

  _tracer = trace.getTracer('costmgr-web');
  _registerWebVitalsHandlers(_tracer);
  return _tracer;
}

/**
 * Return the singleton browser tracer (initializing lazily on first call).
 */
export function getBrowserTracer(): Tracer {
  if (_tracer === null) {
    return initBrowserTracing();
  }
  return _tracer;
}

// ────────────────────────────────────────────────────────────
// 2. Web Vitals auto-collection
// ────────────────────────────────────────────────────────────
function _registerWebVitalsHandlers(tracer: Tracer): void {
  // LCP — Largest Contentful Paint
  onLCP((metric: Metric) => {
    recordWebVital(tracer, 'lcp', metric.value);
  });
  // FID — First Input Delay
  onFID((metric: Metric) => {
    recordWebVital(tracer, 'fid', metric.value);
  });
  // CLS — Cumulative Layout Shift
  onCLS((metric: Metric) => {
    recordWebVital(tracer, 'cls', metric.value);
  });
  // INP — Interaction to Next Paint (replaces FID in web-vitals v3+)
  onINP((metric: Metric) => {
    recordWebVital(tracer, 'inp', metric.value);
  });
  // TTFB — Time to First Byte
  onTTFB((metric: Metric) => {
    recordWebVital(tracer, 'ttfb', metric.value);
  });
}

/**
 * Record a single Web Vital value as a custom span event.
 */
export function recordWebVital(
  tracer: Tracer,
  name: 'lcp' | 'fid' | 'cls' | 'inp' | 'ttfb',
  value: number,
): void {
  const span = tracer.startSpan(`web_vital.${name}`);
  span.setAttribute(`web_vital.${name}`, value);
  span.setAttribute('web_vital.rating', _ratingFor(name, value));
  span.end();
}

function _ratingFor(
  name: 'lcp' | 'fid' | 'cls' | 'inp' | 'ttfb',
  value: number,
): 'good' | 'needs-improvement' | 'poor' {
  // Web Vitals thresholds (https://web.dev/vitals/).
  const thresholds: Record<string, [number, number]> = {
    lcp: [2500, 4000],
    fid: [100, 300],
    cls: [0.1, 0.25],
    inp: [200, 500],
    ttfb: [800, 1800],
  };
  const [good, poor] = thresholds[name] ?? [0, 0];
  if (value <= good) return 'good';
  if (value <= poor) return 'needs-improvement';
  return 'poor';
}

// ────────────────────────────────────────────────────────────
// 3. W3C Trace Context propagation
// ────────────────────────────────────────────────────────────
export interface BrowserTraceContext {
  traceparent: string;
  trace_id: string;
  span_id: string;
}

/**
 * Return the current W3C Trace Context from the active browser span.
 * Used by apps/web/lib/api-fetch.ts to set X-Trace-Id header on outbound
 * fetch (server-side trace_id propagation: server → client → server).
 *
 * Returns null if no active span is recording.
 */
export function getBrowserTraceContext(): BrowserTraceContext | null {
  const span = trace.getActiveSpan();
  if (span === undefined) {
    return null;
  }
  const spanContext = span.spanContext();
  if (!spanContext.traceId || !spanContext.spanId) {
    return null;
  }
  return {
    traceparent: `00-${spanContext.traceId}-${spanContext.spanId}-01`,
    trace_id: spanContext.traceId,
    span_id: spanContext.spanId,
  };
}

// ────────────────────────────────────────────────────────────
// 4. Custom span attribute helpers
// ────────────────────────────────────────────────────────────
export interface UserContext {
  tenant_id: string;
  role: string;
  industry: string;
}

export interface RouteContext {
  path: string;
  locale: string;
}

/**
 * Enrich the current span with user context attributes. Call this from
 * authenticated layout / page components AFTER auth resolution.
 *
 * NOTE: email is NEVER set (NFR4 PII minimization). tenant_id is bound
 * to the authenticated tenant only (cross-tenant span leakage prevention).
 */
export function enrichSpanWithUserContext(user: UserContext): void {
  const span = trace.getActiveSpan();
  if (span === undefined || !span.isRecording()) {
    return;
  }
  span.setAttribute('user.tenant_id', user.tenant_id);
  span.setAttribute('user.role', user.role);
  span.setAttribute('user.industry', user.industry);
}

/**
 * Enrich the current span with route context attributes. Call from
 * server components / client components during route resolution.
 */
export function enrichSpanWithRouteContext(route: RouteContext): void {
  const span = trace.getActiveSpan();
  if (span === undefined || !span.isRecording()) {
    return;
  }
  span.setAttribute('route.path', route.path);
  span.setAttribute('route.locale', route.locale);
}

// ────────────────────────────────────────────────────────────
// 5. No-op tracer fallback (Phase 4 Sentry conditional init mirror)
// ────────────────────────────────────────────────────────────
function _getNoopTracer(): Tracer {
  // The OTEL API `trace.getTracer()` always returns a real Tracer (the
  // no-op tracer provider is the global default when no provider is
  // registered). We just return the global tracer without setting up
  // WebTracerProvider — span.end() becomes a no-op when no exporter is
  // attached.
  return trace.getTracer('costmgr-web-noop');
}

// ────────────────────────────────────────────────────────────
// 6. Error correlation helper
// ────────────────────────────────────────────────────────────
/**
 * Record a browser error as a span event with correlation IDs.
 * Used by the global error boundary to correlate UI errors with traces.
 */
export function recordBrowserError(
  error: Error,
  context_: Record<string, string | number | boolean>,
): void {
  const tracer = getBrowserTracer();
  const span = tracer.startSpan('browser.error');
  span.setAttribute('error.name', error.name);
  span.setAttribute('error.message', error.message);
  span.setAttribute('error.stack', error.stack ?? '');
  for (const [key, value] of Object.entries(context_)) {
    span.setAttribute(`error.context.${key}`, String(value));
  }
  span.recordException(error);
  span.end();
}

export {};
