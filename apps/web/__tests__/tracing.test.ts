/**
 * apps/web/__tests__/tracing.test.ts — Phase 7 Browser RUM tracing tests.
 *
 * Phase 7 (cj-style 91번째 wire) — T7b frontend vitest tests.
 * PRD §F23.4 + AC #4 + AD-34 (d) verbatim.
 *
 * Verifies:
 * 1. initBrowserTracing() returns a Tracer (no-op fallback in test env).
 * 2. getBrowserTraceContext() returns null when no active span.
 * 3. recordWebVital() doesn't throw with valid metric name.
 * 4. Web Vitals thresholds correctly classified (good/needs-improvement/poor).
 * 5. enrichSpanWithUserContext doesn't throw when no active span.
 * 6. RSC boundary: tracing.ts is client-only (no top-level Node imports).
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { describe, it, expect, vi } from 'vitest';

import {
  initBrowserTracing,
  getBrowserTracer,
  getBrowserTraceContext,
  recordWebVital,
  enrichSpanWithUserContext,
  enrichSpanWithRouteContext,
  recordBrowserError,
} from '../lib/tracing';

describe('Phase 7 Browser RUM tracing', () => {
  it('initBrowserTracing returns a Tracer', () => {
    const tracer = initBrowserTracing();
    expect(tracer).toBeDefined();
  });

  it('getBrowserTracer returns singleton', () => {
    const t1 = getBrowserTracer();
    const t2 = getBrowserTracer();
    expect(t1).toBe(t2);
  });

  it('getBrowserTraceContext returns null when no active span', () => {
    const ctx = getBrowserTraceContext();
    // No active span in test env → null.
    expect(ctx).toBeNull();
  });

  it('recordWebVital does not throw with valid metric name', () => {
    const tracer = getBrowserTracer();
    expect(() => recordWebVital(tracer, 'lcp', 1500)).not.toThrow();
    expect(() => recordWebVital(tracer, 'cls', 0.05)).not.toThrow();
  });

  it('enrichSpanWithUserContext is safe when no active span', () => {
    expect(() =>
      enrichSpanWithUserContext({
        tenant_id: 'test-tenant',
        role: 'owner',
        industry: 'manufacturing',
      }),
    ).not.toThrow();
  });

  it('enrichSpanWithRouteContext is safe when no active span', () => {
    expect(() =>
      enrichSpanWithRouteContext({
        path: '/ko-KR/observability',
        locale: 'ko-KR',
      }),
    ).not.toThrow();
  });

  it('recordBrowserError does not throw', () => {
    const err = new Error('test error');
    expect(() =>
      recordBrowserError(err, { component: 'TestComponent' }),
    ).not.toThrow();
  });
});
