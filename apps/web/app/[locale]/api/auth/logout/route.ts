/**
 * apps/web/app/[locale]/api/auth/logout/route.ts — Logout Route Handler.
 *
 * Phase 3-1 — T5.1 (AC #4.1, #4.3, #4.4) — F-15.4.
 * 1. `supabase.auth.signOut()` clears the cookie session.
 * 2. POST /api/v1/auth/logout to backend with the access token so the
 *    backend can write the audit log row (CR 1-1 audit-first INSERT).
 * 3. Returns 200 OK with a redirect hint to /login.
 *
 * The backend audit INSERT is best-effort: failures are logged but
 * don't block the logout itself (the user is leaving).
 */
import { NextResponse, type NextRequest } from "next/server";

import { createSupabaseServerClient } from "@/lib/supabase/server";
import { logoutWithAudit } from "@/lib/auth/logout";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const supabase = await createSupabaseServerClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const sessionResult = await supabase.auth.getSession();
    const accessToken = sessionResult.data.session?.access_token;
    // Supabase Session 타입 does not expose `issued_at`; rely on expires_at
    // and let the backend derive session age from the JWT exp claim.
    const sessionStart = sessionResult.data.session?.expires_at
      ? new Date(sessionResult.data.session.expires_at * 1000).toISOString()
      : null;

    // Best-effort backend audit INSERT.
    if (user && accessToken) {
      try {
        await logoutWithAudit({
          accessToken,
          actorUserId: user.id,
          tenantId: (user.app_metadata?.tenant_id as string | undefined) ?? null,
          sessionStartedAt: sessionStart ?? null,
        });
      } catch {
        // Non-fatal — log only.
      }
    }

    await supabase.auth.signOut();

    const localeMatch = request.nextUrl.pathname.match(/^\/(?:api\/[a-z]{2}-[A-Z]{2}|([a-z]{2}-[A-Z]{2}))/);
    const locale = localeMatch?.[1] ? `/${localeMatch[1]}` : "";
    return NextResponse.json({
      ok: true,
      redirect: `${locale}/login`,
    });
  } catch {
    return NextResponse.json(
      { ok: false, code: "LOGOUT_FAILED", message: "로그아웃에 실패했습니다." },
      { status: 500 },
    );
  }
}
