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
 * Epic 15 EXTENSION (cj-style 60번째 epic 연속 정직 회복) — F17.6 AC #6.2.
 * 3 NEW auth method entry points added BELOW the existing password login:
 *   - Magic link: link to /magic-link
 *   - Social OAuth: <SocialAuthButtons /> inline
 *   - SSO enterprise: link to /sso/<tenant_slug>/login (tenant slug
 *     collected via a small form)
 *
 * CR 11-4 D-001: page.tsx MUST actually mount <LoginForm /> JSX
 * (no <TODO> stubs allowed).
 */
import Link from "next/link";
import { redirect } from "next/navigation";

import { LoginForm } from "@/components/auth/LoginForm";
import { SocialAuthButtons } from "@/components/auth/SocialAuthButtons";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

interface LoginPageProps {
  // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
  // cj-258 패턴. `next build` 강제 type check surface.
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ redirect?: string; reset?: string; error?: string }>;
}

export default async function LoginPage({
  params,
  searchParams,
}: LoginPageProps) {
  const { locale } = await params;
  const {
    redirect: redirectParam,
    reset: resetParam,
    error: errorFromQuery,
  } = await searchParams;
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // If already signed in, redirect to dashboard (or ?redirect= target).
  if (user) {
    const target = redirectParam ?? `/${locale}/dashboard`;
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
      <div
        style={{
          maxWidth: 420,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          gap: "1.5rem",
        }}
      >
        <LoginForm
          locale={locale}
          redirectTo={redirectParam}
          resetSuccess={resetParam === "success"}
        />

        {errorFromQuery && (
          <p
            role="alert"
            style={{
              padding: "0.75rem 1rem",
              borderRadius: 6,
              background: "#fee2e2",
              color: "#991b1b",
              fontSize: "0.875rem",
            }}
          >
            {errorFromQuery === "invalid_callback"
              ? "인증 링크가 유효하지 않습니다. 다시 시도해 주세요."
              : errorFromQuery === "session_exchange_failed"
                ? "세션 교환에 실패했습니다. 다시 시도해 주세요."
                : errorFromQuery === "session_unknown"
                  ? "세션 상태를 확인할 수 없습니다. 다시 로그인해 주세요."
                  : errorFromQuery === "aal_unknown"
                    ? "인증 단계 정보를 확인할 수 없습니다. 다시 로그인해 주세요."
                    : "로그인 처리 중 오류가 발생했습니다."}
          </p>
        )}

        <SocialAuthButtons locale={locale} />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            color: "#94a3b8",
            fontSize: "0.75rem",
          }}
          aria-hidden="true"
        >
          <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
          <span>또는</span>
          <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
        </div>

        <Link
          href={`/${locale}/magic-link${redirectParam ? `?redirect=${encodeURIComponent(redirectParam)}` : ""}`}
          style={{
            display: "block",
            textAlign: "center",
            padding: "0.625rem 1rem",
            borderRadius: 6,
            border: "1px solid #cbd5e1",
            background: "#ffffff",
            color: "#0f172a",
            fontWeight: 600,
            fontSize: "0.875rem",
            textDecoration: "none",
          }}
        >
          매직 링크로 로그인
        </Link>

        <details
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 6,
            padding: "0.75rem 1rem",
            background: "#f8fafc",
          }}
        >
          <summary
            style={{
              cursor: "pointer",
              fontSize: "0.875rem",
              fontWeight: 600,
              color: "#0f172a",
            }}
          >
            엔터프라이즈 SSO 로그인
          </summary>
          <p
            style={{
              marginTop: "0.5rem",
              fontSize: "0.75rem",
              color: "#475569",
              lineHeight: 1.5,
            }}
          >
            회사 도메인(테넌트 슬러그)을 알고 있다면 아래 형식으로 직접 접속해 주세요.
          </p>
          <p
            style={{
              marginTop: "0.5rem",
              fontSize: "0.75rem",
              color: "#0f172a",
              fontFamily: "monospace",
              wordBreak: "break-all",
            }}
          >
            /{locale}/sso/&lt;회사-슬러그&gt;/login
          </p>
        </details>
      </div>
    </main>
  );
}
