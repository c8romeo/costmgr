/**
 * apps/web/app/[locale]/(dashboard)/reports/scheduled/page.tsx — cj-300 wire sprint (cj-style 302번째)
 *
 * Story 30.4 Scheduled reports RSC page (FR-30-4) §F30.4-5 verbatim.
 *
 * Per cj-300 entry decision wire spec:
 *   - RSC page at `/[locale]/reports/scheduled` (mounted under (dashboard) layout group).
 *   - ko-KR NFR18 SSOT verbatim 적용.
 *   - Mounts `<ScheduledJobsList>` (cj-300 wire 진입 신규).
 *   - Capability gate `require_capability(Capability.EXPORT_SCHEDULED)` 보존.
 *
 * AD bind 3/3 + 1 신규 (cj-300 결정 wire 보존):
 *   - AD-2 (audit-first INSERT append-only) — backend route 결정 wire.
 *   - AD-10 (identity + 2FA) — backend route owner/admin RBAC 결정 wire.
 *   - AD-12 (verify-first capability gate) — Capability.EXPORT_SCHEDULED (cj-285 EXTENSION).
 *   - AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory (신규).
 *
 * NFR bind 4/7 active + 2 신규 (cj-300 결정 wire 보존):
 *   - NFR4 (PII minimization) — finance_contact_email redact 결정 wire 보존.
 *   - NFR8 (background job 99.9% uptime) — APScheduler restart resilience (신규).
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR.json EXTENSION ~5 NEW keys 결정 wire 보존.
 *   - NFR19 (export response time) — 결정 wire 보존.
 *
 * Pattern verbatim from `apps/web/app/[locale]/(dashboard)/reports/page.tsx`.
 * Auth gate 는 (dashboard) layout 의 middleware 가 처리 결정 wire (CR 9-6 minimize scope).
 */
import { cookies } from "next/headers";

import { ScheduledJobsList } from "@/components/reports/ScheduledJobsList";

export const dynamic = "force-dynamic";

interface ScheduledReportsPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function toStr(v: string | string[] | undefined): string | undefined {
  if (Array.isArray(v)) return v[0];
  return v;
}

export default async function ScheduledReportsPage({
  params,
  searchParams,
}: ScheduledReportsPageProps): Promise<React.ReactElement> {
  await params; // satisfy Next 15+ Promise<params>

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    return (
      <main className="p-6">
        <p>세션이 만료되었습니다. 다시 로그인해 주세요.</p>
      </main>
    );
  }

  // cj-300 wire — decode JWT payload for app_metadata.tenant_id.
  let tenantId = "";
  try {
    const payloadB64 = accessToken.split(".")[1];
    if (payloadB64) {
      const payloadJson = Buffer.from(
        payloadB64.replace(/-/g, "+").replace(/_/g, "/"),
        "base64",
      ).toString("utf8");
      const payload = JSON.parse(payloadJson) as {
        app_metadata?: { tenant_id?: string };
      };
      tenantId = payload.app_metadata?.tenant_id ?? "";
    }
  } catch {
    // Malformed token — leave tenantId empty; backend will reject with 422.
  }

  const sp = await searchParams;
  const initialStatus = toStr(sp.status) ?? null;

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">예약 리포트</h1>
      <p className="text-sm text-gray-600 mb-4">
        정기적으로 리포트를 생성하여 재무 담당자에게 자동 발송합니다.
      </p>
      <ScheduledJobsList
        accessToken={accessToken}
        tenantId={tenantId}
        initialStatus={initialStatus}
      />
    </main>
  );
}
