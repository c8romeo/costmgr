/**
 * apps/web/app/[locale]/(auth)/forgot-password/page.tsx —
 *   Forgot password Server Component.
 *
 * Phase 3-1 — T6.1 (AC #5.1, #5.2) — F-15.5.
 * 1. If signed in → redirect to dashboard.
 * 2. Else render <ForgotPasswordForm /> Client Component.
 */
import { redirect } from "next/navigation";

import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

interface ForgotPasswordPageProps {
  params: { locale: string };
}

export default async function ForgotPasswordPage({ params }: ForgotPasswordPageProps) {
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
      <ForgotPasswordForm locale={params.locale} />
    </main>
  );
}
