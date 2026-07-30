/**
 * apps/web/app/[locale]/(dashboard)/settings/wizard/page.tsx
 *
 * Story 1.2 — Task 5.1. Settings Wizard landing page.
 *
 * Server Component — reads the access token (F-1: pass the STRING, not a
 * function reference) and delegates the wizard UI to a Client Component.
 *
 * F-20: Server-side initial fetch (race-free). The RSC awaits the
 * completion endpoint server-side and passes the result as
 * `initialCompletion` prop. The Client Component seeds its hook from this
 * prop, so even fast clicks before the first poll cannot clobber existing
 * tenant settings (F-20 silent data-loss path).
 *
 * F-32: still forwards the literal access-token string to Client Components
 * — hardening deferred per the review triage.
 *
 * The wizard renders 4 sections in PRD §8.M0(b) order:
 *   1. 회계연도 시작월
 *   2. 통화
 *   3. 언어
 *   4. 배부기준 3종
 *
 * UX-locked: ko-KR labels, WCAG AA contrast, Professional 톤.
 */

import { cookies } from "next/headers";

import { SettingsWizardClient } from "@/components/settings/wizard/SettingsWizardClient";
import { WizardErrorBoundary } from "@/components/settings/wizard/WizardErrorBoundary";
import { fetchCompletionServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function SettingsWizardPage() {
  const accessToken = cookies().get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  // F-20: server-side initial completion fetch. On any failure (network,
  // 401, 5xx, JSON decode), we return `null` and let the Client Component
  // fall back to its polling loop.
  const initialCompletion = await fetchCompletionServerSide(accessToken, traceId);

  return (
    <section style={{ maxWidth: 960, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          설정 마법사
        </h1>
        <p style={{ color: "#475569" }}>
          [계산] 버튼을 사용하려면 아래 4개 항목을 모두 완료하세요. (PRD §8.M0(b))
        </p>
      </header>
      {/* F-24: client-side error boundary. Catches render-phase
          exceptions in the wizard tree so the user sees a recoverable
          fallback instead of a blank screen. */}
      <WizardErrorBoundary>
        <SettingsWizardClient
          accessToken={accessToken}
          initialCompletion={initialCompletion}
        />
      </WizardErrorBoundary>
    </section>
  );
}
