/**
 * apps/web/app/[locale]/(auth)/reset-password/page.tsx — Reset password page.
 *
 * Phase 3-1 — T6.3 (AC #5.3) — F-15.5.
 * The `code` query param is the Supabase recovery session token. The Server
 * Component itself does not validate the token (that happens implicitly via
 * `supabase.auth.updateUser` in the client form). We just render the form
 * with the code passed through.
 *
 * If no `code` param is present, show a Korean dead-end explaining how to
 * restart the flow.
 */
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";

export const dynamic = "force-dynamic";

interface ResetPasswordPageProps {
  params: { locale: string };
  searchParams: { code?: string };
}

export default async function ResetPasswordPage({
  params,
  searchParams,
}: ResetPasswordPageProps) {
  if (!searchParams.code) {
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
          <h1 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem" }}>
            비밀번호 재설정
          </h1>
          <p style={{ color: "#475569", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
            재설정 링크가 유효하지 않거나 만료되었습니다. 비밀번호 찾기에서 다시 요청해 주세요.
          </p>
          <a
            href={`/${params.locale}/forgot-password`}
            style={{
              display: "inline-block",
              padding: "0.5rem 1rem",
              borderRadius: 6,
              background: "#0f172a",
              color: "#ffffff",
              fontWeight: 600,
              fontSize: "0.875rem",
              textDecoration: "none",
            }}
          >
            비밀번호 찾기로 이동
          </a>
        </section>
      </main>
    );
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
      <ResetPasswordForm locale={params.locale} code={searchParams.code} />
    </main>
  );
}
