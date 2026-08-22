/**
 * apps/web/lib/observability/sentry.ts — Sentry browser integration (Phase 4 T5 wire).
 *
 * Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AD-27 verbatim +
 * PRD §F16.5 + AC #5.3.
 *
 * Provides Sentry browser initialization for the Next.js frontend deployed on
 * Vercel. Pairs with `apps/api/core/observability.py` (server-side Sentry)
 * for full-stack observability.
 *
 * Architecture patterns (CR 11-3 honest-DEFER discipline):
 * - SSR-safe initialization: guards on `typeof window !== "undefined"` to
 *   avoid breaking Next.js Server Components / Edge Runtime.
 * - Optional integration: if `NEXT_PUBLIC_SENTRY_DSN` is not set, the
 *   module is a no-op (returns early). No hard dependency on Sentry.
 * - No PII leakage: `sendDefaultPii=false`, request bodies scrubbed.
 * - `tracesSampleRate=0.1` (10% of transactions).
 */

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN ?? "";
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT ?? "development";

/**
 * Whether Sentry DSN is configured. Returns false in test/dev without DSN.
 */
export function isSentryEnabled(): boolean {
  return Boolean(SENTRY_DSN.trim());
}

/**
 * Initialize Sentry for the browser. Must be called once on app startup.
 *
 * Behavior:
 * - SSR-safe: returns early if `typeof window === "undefined"`.
 * - No-op if `NEXT_PUBLIC_SENTRY_DSN` is unset.
 * - Lazy-loads `@sentry/nextjs` to avoid increasing the bundle size
 *   for tenants who do NOT configure Sentry.
 * - `tracesSampleRate=0.1` (10% of transactions).
 * - `replaysSessionSampleRate=0` (opt-in only — no session replay
 *   unless explicitly enabled via env var).
 */
export async function initSentry(): Promise<boolean> {
  if (typeof window === "undefined") {
    // Server-side rendering guard — Sentry browser init is not
    // applicable to Next.js Server Components.
    return false;
  }
  if (!isSentryEnabled()) {
    return false;
  }
  try {
    const Sentry = await import("@sentry/nextjs");
    Sentry.init({
      dsn: SENTRY_DSN,
      environment: ENVIRONMENT,
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0,
      replaysOnErrorSampleRate: 0,
      sendDefaultPii: false,
      integrations: [
        // Default browser integrations (Breadcrumbs, GlobalHandlers,
        // LinkedErrors, HttpContext, UserAgent) are auto-included.
      ],
    });
    return true;
  } catch (err) {
    // Observability is opt-in — never break the app if Sentry fails.
    console.warn("[sentry] init failed:", err);
    return false;
  }
}

/**
 * Capture a browser exception in Sentry (no-op if not initialized).
 */
export async function captureException(
  err: Error,
  context?: Record<string, unknown>,
): Promise<void> {
  if (typeof window === "undefined" || !isSentryEnabled()) {
    return;
  }
  try {
    const Sentry = await import("@sentry/nextjs");
    Sentry.captureException(err, { extra: context });
  } catch {
    // Never raise from observability.
  }
}

/**
 * Capture a browser message in Sentry (no-op if not initialized).
 */
export async function captureMessage(
  message: string,
  level: "info" | "warning" | "error" = "info",
): Promise<void> {
  if (typeof window === "undefined" || !isSentryEnabled()) {
    return;
  }
  try {
    const Sentry = await import("@sentry/nextjs");
    Sentry.captureMessage(message, level);
  } catch {
    // Never raise from observability.
  }
}