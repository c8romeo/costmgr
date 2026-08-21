/**
 * apps/web/app/[locale]/(auth)/login/page.tsx — Login Server Component.
 *
 * Phase 3-1 — T2.1 (AC #1.1, #1.4) — Story 1.1 F-1 + F-4 honestly RESOLVE.
 * 1. Read `sb-access-token` cookie via SSR client. (F-4: pass the
 *    accessToken STRING, not a function — function props cannot cross
 *    the RSC boundary.)
 * 2. If user is signed in → redirect to `?redirect=` param OR
 *    `/{locale}/(dashboard)/` default.
 * 3. If AAL check is required (Epic 12) → redirect to /auth/2fa.
 * 4. Else render <LoginForm /> (Client Component).
 *
 * CR 11-4 D-001: page.tsx MUST actually mount <LoginForm /> JSX
 * (no <TODO> stubs allowed).
 */
import { redirect } from "next/navigation";

import { LoginForm } from "@/components/auth/LoginForm";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

interface LoginPageProps {
  params: { locale: string };
  searchParams: { redirect?: string; reset?: string };
}

export default async function LoginPage({
  params,
  searchParams,
}: LoginPageProps) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // If already signed in, redirect to dashboard (or ?redirect= target).
  if (user) {
    const target = searchParams.redirect ?? `/${params.locale}/dashboard`;
    redirect(target);
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem 1rem",
      }}
    >
      <LoginForm
        locale={params.locale}
        redirectTo={searchParams.redirect}
        resetSuccess={searchParams.reset === "success"}
      />
    </main>
  );
}
