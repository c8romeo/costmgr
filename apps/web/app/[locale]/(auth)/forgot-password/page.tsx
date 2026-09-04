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
  // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
  // cj-258 패턴. `next build` 강제 type check surface.
  params: Promise<{ locale: string }>;
}

export default async function ForgotPasswordPage({ params }: ForgotPasswordPageProps) {
  const { locale } = await params;
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect(`/${locale}/dashboard`);
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
      <ForgotPasswordForm locale={locale} />
    </main>
  );
}
