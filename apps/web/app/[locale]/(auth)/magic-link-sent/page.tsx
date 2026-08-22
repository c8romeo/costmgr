/**
 * apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx — Magic link sent confirmation.
 *
 * Epic 15 — T2.3 (AC #1.4) — F17.1 Magic link confirmation.
 * - SECURITY INVARIANT: always display the same generic message
 *   regardless of whether the email is registered (AC #1.4 verbatim).
 * - No email-existence check, no provider-specific hint, no rate limit
 *   state reveal.
 */
import Link from "next/link";

export const dynamic = "force-dynamic";

interface MagicLinkSentPageProps {
  params: { locale: string };
}

export default function MagicLinkSentPage({ params }: MagicLinkSentPageProps) {
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
      <div
        style={{
          maxWidth: 420,
          width: "100%",
          padding: "1.5rem",
          borderRadius: 12,
          background: "#ffffff",
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
        }}
        aria-labelledby="magic-link-sent-heading"
      >
        <h1
          id="magic-link-sent-heading"
          style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
        >
          메일함을 확인해 주세요
        </h1>
        <p
          style={{
            color: "#475569",
            marginBottom: "1.5rem",
            fontSize: "0.875rem",
            lineHeight: 1.6,
          }}
        >
          로그인 링크가 전송되었습니다. 이메일을 확인하고 링크를 클릭해 로그인을 완료해 주세요.
        </p>
        <p
          style={{
            color: "#94a3b8",
            marginBottom: "1.5rem",
            fontSize: "0.75rem",
            lineHeight: 1.6,
          }}
        >
          이메일이 도착하지 않았다면 스팸 메일함을 확인하거나 잠시 후 다시 시도해 주세요.
        </p>
        <div
          style={{
            textAlign: "center",
            fontSize: "0.875rem",
            color: "#475569",
          }}
        >
          <Link
            href={`/${params.locale}/login`}
            style={{ color: "#0f172a", textDecoration: "underline" }}
          >
            로그인으로 돌아가기
          </Link>
        </div>
      </div>
    </main>
  );
}
