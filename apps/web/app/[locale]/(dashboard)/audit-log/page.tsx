/**
 * apps/web/app/[locale]/(dashboard)/audit-log/page.tsx — Epic 17 T2 (AC #2.1)
 *
 * RSC page for /audit-log (audit log viewer).
 *
 * Per PRD §F21.2 + AD-32 (b):
 *   - Server-side fetch initial audit log page via `fetchAuditLogServerSide`
 *     (F-20 race-free initial fetch pattern).
 *   - Hand the response (or fail-closed null) to `<AuditLogPanel>`
 *     which orchestrates AuditLogFilterPanel / AuditLogTable /
 *     AuditLogPagination / AuditLogExportButton / AuditLogDetailModal.
 *
 * Fail-closed pattern: when the backend fetch fails (network, 401,
 * 403, 5xx) we pass `null` through and the Client Component renders
 * a "감사 로그를 불러오지 못했습니다" error envelope. The Client
 * Component retries via `useEffect` on mount and surfaces typed
 * CR 12-5 D-14 error envelopes to the user.
 *
 * The path resolves under `/[locale]/(dashboard)/audit-log`. It is
 * the frontend half of Epic 17 territory (the backend was wired in
 * commit `2ada2ec`).
 */
import { cookies } from "next/headers";

import { AuditLogPanel } from "@/components/audit/AuditLogPanel";
import type { AuditLogQueryFilters } from "@/lib/audit/audit-log-client";
import { fetchAuditLogServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface AuditLogPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function toStr(v: string | string[] | undefined): string | undefined {
  if (Array.isArray(v)) return v[0];
  return v;
}

export default async function AuditLogPage({
  params,
  searchParams,
}: AuditLogPageProps): Promise<React.ReactElement> {
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

  const traceId = crypto.randomUUID();

  const sp = await searchParams;
  const filters: AuditLogQueryFilters = {
    actor_id: toStr(sp.actor_id) ?? null,
    action: toStr(sp.action) ?? null,
    action_class: toStr(sp.action_class) ?? null,
    resource_type: toStr(sp.resource_type) ?? null,
    resource_id: toStr(sp.resource_id) ?? null,
    start_date: toStr(sp.start_date) ?? null,
    end_date: toStr(sp.end_date) ?? null,
    trace_id: toStr(sp.trace_id) ?? null,
  };
  const page = Math.max(1, parseInt(toStr(sp.page) ?? "1", 10) || 1);
  const pageSize = Math.min(
    200,
    Math.max(10, parseInt(toStr(sp.page_size) ?? "50", 10) || 50),
  );

  const initialPage = await fetchAuditLogServerSide(
    accessToken,
    filters,
    page,
    pageSize,
    traceId,
  );

  return (
    <main className="p-6">
      <AuditLogPanel
        accessToken={accessToken}
        initialPage={initialPage}
        initialFilters={filters}
        initialPageNumber={page}
        initialPageSize={pageSize}
      />
    </main>
  );
}
