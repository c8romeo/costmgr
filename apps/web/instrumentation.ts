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
 *
 * **Edge-bundle hardening:** instrumentation-node.ts imports the
 * @opentelemetry/sdk-node package which transitively pulls in
 * @grpc/proto-loader + @grpc/grpc-js (requires Node `fs`). The Next.js
 * edge runtime bundle cannot include these — even when the runtime init
 * is short-circuited by OTEL_SDK_DISABLED=true, webpack statically
 * analyzes every reachable dynamic import. We guard the dynamic import
 * with `process.env.NEXT_RUNTIME === 'nodejs'` — Next.js replaces this
 * constant at build time per target, so the edge build tree-shakes the
 * import entirely and OTel packages never enter the edge bundle. (cj-250
 * fix: prior eval()-hidden path also hid the module from webpack's lazy
 * context, yielding MODULE_NOT_FOUND at dev-server boot.)
 */
export async function register(): Promise<void> {
  if (typeof window === 'undefined') {
    // Server runtime — gate dynamic import by Next.js build-time constant.
    // NEXT_RUNTIME === 'nodejs' (replaced at build time, tree-shaken for edge).
    if (process.env.NEXT_RUNTIME === 'nodejs') {
      if (process.env.OTEL_SDK_DISABLED === 'true') {
        // Dev / CI short-circuit. Skip server OTel init.
        return;
      }
      await import('./instrumentation-node');
    }
    return;
  }
  // Client runtime — bootstrap Browser RUM tracing.
  const { initBrowserTracing } = await import('./lib/tracing');
  initBrowserTracing();
}
