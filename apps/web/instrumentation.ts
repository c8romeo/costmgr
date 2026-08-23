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
 * analyzes every reachable dynamic import. We use an eval()-hidden
 * module path so webpack cannot trace the import; the path is resolved
 * at runtime by Node's loader when (and only when) the dynamic import
 * actually executes (i.e. OTEL_SDK_DISABLED !== 'true').
 */
export async function register(): Promise<void> {
  if (typeof window === 'undefined') {
    if (process.env.OTEL_SDK_DISABLED === 'true') {
      // Dev / CI short-circuit. Skip server OTel init.
      return;
    }
    // Server runtime — delegate to instrumentation-node.ts.
    // eslint-disable-next-line no-eval
    const modulePath: string = eval("'./instrumentation-node'");
    await import(modulePath);
  } else {
    // Client runtime — bootstrap Browser RUM tracing.
    const { initBrowserTracing } = await import('./lib/tracing');
    initBrowserTracing();
  }
}
