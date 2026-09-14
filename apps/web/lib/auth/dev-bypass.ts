/**
 * apps/web/lib/auth/dev-bypass.ts — cj-style N+16 (D-Day MVP demo, 2026-09-14 KST).
 *
 * Single source of truth for "is the frontend MVP local-dev bypass active?"
 * Mirrors the backend's `MVP_DEV_BYPASS` env. When true, frontend
 * layout/page-level auth gates skip the cookie check and let the request
 * through — backend dev bypass (first tenant_memberships owner auto-login)
 * handles actual authentication for downstream API calls.
 *
 * Production safety: `NEXT_PUBLIC_MVP_DEV_BYPASS` is unset/false in any
 * non-local environment (.env.local is git-ignored, .env.example does not
 * include it). Even if accidentally set in prod, the backend's
 * `APP_ENV=production` check disables its own bypass independently.
 */
export function isDevBypassActive(): boolean {
  return process.env.NEXT_PUBLIC_MVP_DEV_BYPASS === "true";
}
