/**
 * apps/web/instrumentation.ts — Next.js instrumentation hook.
 *
 * Phase 7 (cj-style 91번째 wire) — Observability Stack 강화 territory.
 * PRD §F23.4 + AD-34 (d) sub-decision.
 *
 * **RSC boundary:** This file is auto-discovered by Next.js and runs in
 * BOTH server and client contexts. The CLIENT-side initialization is
 * deferred to apps/web/lib/tracing.ts:initBrowserTracing() — this file
 * delegates to register() only when running on the server runtime.
 *
 * Server-side bootstrap uses apps/web/instrumentation-node.ts (CR 1-1
 * RSC boundary verbatim).
 */
export async function register(): Promise<void> {
  if (typeof window === 'undefined') {
    // Server runtime — delegate to instrumentation-node.ts.
    await import('./instrumentation-node');
  } else {
    // Client runtime — bootstrap Browser RUM tracing.
    const { initBrowserTracing } = await import('./lib/tracing');
    initBrowserTracing();
  }
}
