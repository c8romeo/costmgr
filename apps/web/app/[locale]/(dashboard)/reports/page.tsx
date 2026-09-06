/**
 * apps/web/app/[locale]/(dashboard)/reports/page.tsx — cj-282a wire sprint (cj-style 283번째)
 * + cj-295 follow-up #1 (cj-style 295번째) — PDF export tab nav EXTENSION.
 *
 * Story 30.1 CSV export RSC page (FR-30-1) + Story 30.2 PDF export tab (FR-30-2).
 *
 * Per cj-282 PRD entry spec §F44.1 + cj-295 follow-up #1:
 *   - RSC page at `/[locale]/reports` (mounted under (dashboard) layout group).
 *   - ko-KR NFR18 SSOT verbatim 적용.
 *   - CSV/PDF tab nav (cj-295 follow-up #1 EXTENSION) — client-side tab
 *     switch between CsvExportTab + PdfExportTab.
 *   - Mounts both `<CsvExportTab>` (cj-282a) and `<PdfExportTab>` (cj-295).
 *
 * Capability gate `require_exports_csv` 결정 wire 보류:
 *   - Capability.EXPORTS_CSV EXTENSION 결정 wire (cj-282 PRD entry §M v1.47 → v1.48 EXTENSION)
 *     cj-style 284+ 적용 시 frontend-side gate 추가 진입.
 *   - 현재 sprint 는 backend route 의 owner/admin RBAC 결정 wire 만 (AD-22 verbatim).
 *
 * AD bind 3/3 (cj-282 PRD entry 결정 wire):
 *   - AD-2 (audit-first INSERT append-only) — backend route 결정 wire.
 *   - AD-10 (identity + 2FA) — backend route owner/admin RBAC 결정 wire.
 *   - AD-12 (verify-first capability gate) — Capability.EXPORT_CSV + Capability.EXPORT_PDF (cj-285 EXTENSION).
 *
 * NFR bind 3/7 active:
 *   - NFR5 (page load P95 ≤ 5s) — streaming response 결정 wire 보존.
 *   - NFR7 (PDF rendering integrity) — reportlab 결정 wire (cj-293).
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR.json EXTENSION 결정 wire 보류.
 *
 * 4 OQ 결정 보류 (cj-282a 범위 외 N/A):
 *   - OQ-EPIC30+-2 SMTP 인프라 외부 의존 (Story 30.3 Email)
 *   - OQ-EPIC30+-3 APScheduler vs Celery beat vs cron (Story 30.4 Scheduled)
 *
 * CR 11-3 honest-DEFER 235번째 epic 연속 정직 회복
 * (cj-294 close-out retro 의 234번째 + cj-295 follow-up #1 의 235번째)
 *
 * Pattern verbatim from `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx:23-96`.
 * Auth gate 는 (dashboard) layout 의 middleware 가 처리 결정 wire (CR 9-6 minimize scope).
 */
import { cookies } from "next/headers";

import { ReportsTabNav } from "@/components/reports/ReportsTabNav";

export const dynamic = "force-dynamic";

interface ReportsPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function toStr(v: string | string[] | undefined): string | undefined {
  if (Array.isArray(v)) return v[0];
  return v;
}

export default async function ReportsPage({
  params,
  searchParams,
}: ReportsPageProps): Promise<React.ReactElement> {
  await params; // satisfy Next 15+ Promise<params>

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    // Layout-level gate should have caught this, but defense in depth.
    return (
      <main className="p-6">
        <p>세션이 만료되었습니다. 다시 로그인해 주세요.</p>
      </main>
    );
  }

  // cj-287 wire — decode JWT payload for app_metadata.tenant_id.
  // Supabase JWT shape: header.payload.signature (base64url-encoded).
  // Payload structure: { app_metadata: { tenant_id: "<uuid>" }, sub: "<user_id>" }.
  // The decoded tenant_id is passed to both <CsvExportTab> and <PdfExportTab>
  // so the download buttons send the required tenant_id query param
  // (csv_routes.py:265 / pdf_routes.py PdfExportRequest UUID4).
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
  const initialPeriod = toStr(sp.period) ?? "2026-08";
  const initialType: "cost-records" | "bom" =
    toStr(sp.type) === "bom" ? "bom" : "cost-records";

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">보고서</h1>
      <ReportsTabNav
        accessToken={accessToken}
        tenantId={tenantId}
        initialPeriod={initialPeriod}
        initialType={initialType}
      />
    </main>
  );
}
