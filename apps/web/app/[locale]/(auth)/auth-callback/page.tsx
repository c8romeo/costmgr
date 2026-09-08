/**
 * apps/web/app/[locale]/(auth)/auth-callback/page.tsx — OAuth + Magic link callback.
 *
 * Epic 15 — T2.4 (AC #1.7, #2.4) — F17.1+F17.2 callback handler.
 * - Exchanges the auth code for a Supabase session (magic link or OAuth).
 * - Sets the sb-access-token cookie via SSR client (Phase 3-1 T1 wire).
 * - Branches to /auth/2fa for users with AAL='aal1' (Epic 12 wire).
 * - D-001 actual mount: page.tsx MUST render real JSX (CR 11-4 D-001).
 * - D-005 unknown state reject: render fallback UI on state='unknown'.
 */
import { redirect } from "next/navigation";

import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

interface AuthCallbackPageProps {
  // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
  // cj-258 패턴. `next build` 강제 type check surface.
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ code?: string; redirect?: string; state?: string }>;
}

type Aal = "aal1" | "aal2" | "unknown";

function parseAal(value: unknown): Aal {
  if (value === "aal1" || value === "aal2") return value;
  return "unknown";
}

export default async function AuthCallbackPage({ params, searchParams }: AuthCallbackPageProps) {
  const { locale } = await params;
  const { code, redirect: redirectParam } = await searchParams;
  const target = redirectParam ?? `/${locale}/dashboard`;

  if (!code) {
    // No code → invalid callback. Redirect to login with error.
    redirect(`/${locale}/login?error=invalid_callback`);
  }

  const supabase = await createSupabaseServerClient();

  // Exchange the code for a Supabase session.
  const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

  if (exchangeError) {
    redirect(`/${locale}/login?error=session_exchange_failed`);
  }

  // Read AAL to decide 2FA branching (Epic 12 D-GATE-01 inversion).
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    // Session established but user lookup failed. Treat as unknown state
    // (D-005 lesson) and redirect to login.
    redirect(`/${locale}/login?error=session_unknown`);
  }

  const aal = parseAal(user.app_metadata?.aal);

  // D-005: reject unknown AAL state (never crash, never grant access).
  if (aal === "unknown") {
    redirect(`/${locale}/login?error=aal_unknown`);
  }

  // D-GATE-01 inversion: aal1 → 2FA challenge, aal2 → dashboard.
  // cj-307 wire (CR 11-3 honest-DEFER 261번째) — Pilot W1 최소 수정.
  // 진짜 blocker: /auth/2fa page 부재 (cj-306 audit). 신규 사용자는 모두
  // aal1 (no MFA enrolled) → 기존 로직은 404 로 stuck. MFA factors 가
  // verified 인 경우에만 /auth/2fa 로 redirect 하고, 그렇지 않으면
  // dashboard 로 직접 진행. 정식 2FA flow 는 post-W1 hardening 으로 defer.
  if (aal === "aal1") {
    const { data: factorsData } = await supabase.auth.mfa.listFactors();
    const hasVerifiedFactor =
      factorsData?.all?.some((f) => f.status === "verified") ?? false;
    if (hasVerifiedFactor) {
      const twofaUrl = target
        ? `/${locale}/auth/2fa?redirect=${encodeURIComponent(target)}`
        : `/${locale}/auth/2fa`;
      redirect(twofaUrl);
    }
    // else: MFA 미등록 사용자 → dashboard 로 직접 (cj-307 결정 wire)
  }

  redirect(target);
}
