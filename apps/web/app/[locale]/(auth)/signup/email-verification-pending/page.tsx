/**
 * apps/web/app/[locale]/(auth)/email-verification-pending/page.tsx —
 *   Email verification pending page.
 *
 * Phase 3-1 — T3.4 (AC #2.4) — F-15.2.
 * When Supabase signUp is called with email-confirmation enabled, the
 * session is null and the user must click the verification link. This
 * page shows the canonical Korean guidance and a resend button.
 *
 * The page is placed under the (auth) group so unauthenticated users
 * can see it. The resend button calls `supabase.auth.resend()`.
 */
import { redirect } from "next/navigation";

import { ResendVerificationButton } from "@/components/auth/ResendVerificationButton";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

interface PageProps {
  params: { locale: string };
  searchParams: { email?: string };
}

export default async function EmailVerificationPendingPage({
  params,
  searchParams,
}: PageProps) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Already verified + signed in → skip ahead.
  if (user) {
    redirect(`/${params.locale}/onboarding/industry`);
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
      <section
        style={{
          maxWidth: 480,
          width: "100%",
          padding: "1.5rem",
          borderRadius: 12,
          background: "#ffffff",
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
        }}
      >
        <h1
          style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
        >
          이메일 인증을 완료해 주세요
        </h1>
        <p style={{ color: "#475569", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
          인증 메일을 보냈습니다. 메일의 링크를 클릭해 가입을 완료해 주세요.
          {searchParams.email ? ` (${searchParams.email})` : null}
        </p>
        <ResendVerificationButton
          email={searchParams.email ?? ""}
          locale={params.locale}
        />
      </section>
    </main>
  );
}
