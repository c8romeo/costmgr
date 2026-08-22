/**
 * apps/web/app/api/auth/sso/callback/route.ts — SAML ACS callback handler.
 *
 * Epic 15 — T5.1 (AC #3.5) — F17.3 SSO ACS callback.
 * - Receives the SAML response POST from the backend `/api/v1/auth/sso/acs`.
 * - Sets the `sb-access-token` cookie (Phase 3-1 T1 wire).
 * - Redirects to /dashboard (or 2FA challenge if AAL=aal1).
 * - Sentry breadcrumb added (F4 observability EXTENSION, F16.5 wire 정합).
 */
import { NextRequest, NextResponse } from "next/server";

import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  // Read the SAML response form-encoded payload forwarded by the backend.
  const form = await request.formData();
  const code = form.get("code")?.toString() ?? "";
  const redirectTo = form.get("redirect_to")?.toString() ?? "/dashboard";

  if (!code) {
    return NextResponse.redirect(new URL("/login?error=sso_no_code", request.url));
  }

  // Exchange the code for a Supabase session.
  const supabase = await createSupabaseServerClient();
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) {
    return NextResponse.redirect(
      new URL("/login?error=sso_session_failed", request.url),
    );
  }

  // AAL branch (D-GATE-01 inversion).
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const aal = user?.app_metadata?.aal;
  if (aal === "aal1") {
    return NextResponse.redirect(
      new URL("/auth/2fa?redirect=" + encodeURIComponent(redirectTo), request.url),
    );
  }

  // Sentry breadcrumb (observability EXTENSION).
  if (typeof globalThis.Sentry !== "undefined") {
    try {
      const sentry = (globalThis as { Sentry?: { addBreadcrumb: (b: unknown) => void } }).Sentry;
      sentry?.addBreadcrumb({
        category: "auth.sso",
        message: "SSO ACS callback succeeded",
        level: "info",
      });
    } catch {
      // Sentry not initialized — ignore.
    }
  }

  return NextResponse.redirect(new URL(redirectTo, request.url));
}
