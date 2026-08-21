/**
 * apps/web/app/[locale]/(auth)/signup/page.tsx — Signup Server Component.
 *
 * Phase 3-1 — T3.1 (AC #2.1, #2.2) — Story 1.1 F-1 + F-4 honestly RESOLVE.
 * 1. Read session via SSR client.
 * 2. If signed in → redirect to dashboard.
 * 3. Else render <SignupForm /> Client Component.
 *
 * CR 11-4 D-001: page.tsx MUST actually mount <SignupForm /> JSX.
 */
import { redirect } from "next/navigation";

import { SignupForm } from "@/components/auth/SignupForm";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

interface SignupPageProps {
  params: { locale: string };
}

export default async function SignupPage({ params }: SignupPageProps) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect(`/${params.locale}/dashboard`);
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
      <SignupForm locale={params.locale} />
    </main>
  );
}
