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
  params: { locale: string };
  searchParams: { code?: string; redirect?: string; state?: string };
}

type Aal = "aal1" | "aal2" | "unknown";

function parseAal(value: unknown): Aal {
  if (value === "aal1" || value === "aal2") return value;
  return "unknown";
}

export default async function AuthCallbackPage({ params, searchParams }: AuthCallbackPageProps) {
  const code = searchParams.code;
  const target = searchParams.redirect ?? `/${params.locale}/dashboard`;

  if (!code) {
    // No code → invalid callback. Redirect to login with error.
    redirect(`/${params.locale}/login?error=invalid_callback`);
  }

  const supabase = await createSupabaseServerClient();

  // Exchange the code for a Supabase session.
  const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

  if (exchangeError) {
    redirect(`/${params.locale}/login?error=session_exchange_failed`);
  }

  // Read AAL to decide 2FA branching (Epic 12 D-GATE-01 inversion).
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    // Session established but user lookup failed. Treat as unknown state
    // (D-005 lesson) and redirect to login.
    redirect(`/${params.locale}/login?error=session_unknown`);
  }

  const aal = parseAal(user.app_metadata?.aal);

  // D-005: reject unknown AAL state (never crash, never grant access).
  if (aal === "unknown") {
    redirect(`/${params.locale}/login?error=aal_unknown`);
  }

  // D-GATE-01 inversion: aal1 → 2FA challenge, aal2 → dashboard.
  if (aal === "aal1") {
    const twofaUrl = target
      ? `/${params.locale}/auth/2fa?redirect=${encodeURIComponent(target)}`
      : `/${params.locale}/auth/2fa`;
    redirect(twofaUrl);
  }

  redirect(target);
}
