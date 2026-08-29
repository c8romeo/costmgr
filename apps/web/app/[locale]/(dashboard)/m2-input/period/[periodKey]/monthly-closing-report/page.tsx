/**
 * apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/monthly-closing-report/page.tsx
 *
 * Story 6.2 T7.5 — Server Component page-level wire for [월 마감 보고서].
 *
 * Reads access token, awaits the monthly-closing-report state server-side
 * (3-source read-only join: closing_snapshot + ledger events +
 * fiscal_period_snapshots + V4 verdict envelope + audit-trail), then
 * delegates the panel UI to MonthlyClosingReportPanel.
 *
 * Story 6.3 T2 — Adds tenant-settings fetch for `industry` (W5 deferral
 * guard for PDF export endpoint). Threads industry + accessToken to the
 * panel so the ClosingPdfExportButton can render when industry is valid.
 *
 * UX-locked: ko-KR labels, WCAG AA contrast, Professional 톤.
 *
 * Capability gate (A10) — when `monthly_closing_report_capability_granted=false`,
 * the panel is hidden entirely (service-only tenant → INDUSTRY_NOT_SUPPORTED).
 */

import { cookies } from "next/headers";

import { MonthlyClosingReportPanel } from "@/components/m2-input/MonthlyClosingReportPanel";
import { isValidClosingPdfIndustry } from "@/lib/closing-pdf-export";
import { buildMonthlyClosingReportAggregate } from "@/lib/monthly-closing-report";
import {
  fetchMonthlyClosingReportServerSide,
  fetchMonthlyClosingReportAuditTrailServerSide,
  fetchMonthlyClosingReportV4VerdictServerSide,
  fetchTenantSettingsServerSide,
} from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function MonthlyClosingReportPage({
  params,
}: {
  params: Promise<{ periodKey: string }>;
}) {
  const { periodKey } = await params;
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  // ── 4 read-only fetches (closing report + audit trail + V4 verdict + tenant settings) ──
  // Best-effort error boundary — returns null on any failure.
  let reportResponse = null;
  let auditTrailResponse = null;
  let v4VerdictResponse = null;
  let tenantSettings = null;
  try {
    [reportResponse, auditTrailResponse, v4VerdictResponse, tenantSettings] =
      await Promise.all([
        fetchMonthlyClosingReportServerSide(periodKey, accessToken, traceId),
        fetchMonthlyClosingReportAuditTrailServerSide(periodKey, accessToken, traceId),
        fetchMonthlyClosingReportV4VerdictServerSide(periodKey, accessToken, traceId),
        fetchTenantSettingsServerSide(accessToken, traceId),
      ]);
  } catch {
    // best-effort — fall through to null → empty fallback
  }

  // Fail-closed fallback — when all 3 fetches return null, fall back to
  // EMPTY view mode (consistent with period/page.tsx fail-closed pattern).
  const aggregate = reportResponse
    ? buildMonthlyClosingReportAggregate(reportResponse)
    : {
        period_key: periodKey,
        view_mode: "EMPTY" as const,
        closing_snapshot_count: 0,
        ledger_event_count: 0,
        fiscal_period_snapshot_count: 0,
        opening_inventory_count: 0,
        closing_per_product: [],
        audit_emitted: false,
        currency_pair: null,
        trace_id: traceId,
        report_generated_at: new Date().toISOString(),
      };

  const v4_verdict = v4VerdictResponse?.verdict ?? null;
  const audit_trail = auditTrailResponse?.entries ?? [];
  const capability_granted = reportResponse != null;

  // 6-3 wire: industry code from tenant settings (W5 deferral guard).
  // Filter to one of 4 canonical industries — non-canonical (e.g. 'trad')
  // → no PDF export (button hidden).
  const raw_industry = tenantSettings?.industry ?? null;
  const industry = isValidClosingPdfIndustry(raw_industry) ? raw_industry : null;

  return (
    <section style={{ maxWidth: 1100, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          월 마감 보고서 — {periodKey}
        </h1>
        <p style={{ color: "#475569" }}>
          PRD §F5 — 마감 보고서 + §F5.2 KRW/USD dual display + §V4 closing snapshot 일관성.
        </p>
      </header>
      <MonthlyClosingReportPanel
        aggregate={aggregate}
        v4_verdict={v4_verdict}
        audit_trail={audit_trail}
        capability_granted={capability_granted}
        industry={industry}
        accessToken={accessToken}
      />
    </section>
  );
}