"use client";

/**
 * apps/web/components/reports/ReportsTabNav.tsx — cj-299 wire sprint (cj-style 299번째)
 * + cj-300 wire sprint (cj-style 302번째) — Scheduled reports tab EXTENSION.
 *
 * Client component wrapping CsvExportTab + PdfExportTab + EmailExportTab +
 * ScheduledJobsList with simple tab navigation. The tab nav uses inline ko-KR
 * labels (NFR18 SSOT verbatim 적용) and a 4-tab UX (CSV / PDF / Email /
 * Scheduled). State for the active tab is local useState.
 *
 * cj-300 wire sprint 결정 wire 진입 (cj-299 의 3-tab UX → 4-tab UX 확장).
 * Story 30.4 Scheduled reports 진입.
 *
 * Pattern verbatim mirror from CsvExportTab.tsx verbatim ko-KR labels pattern
 * + a thin tab nav wrapper.
 *
 * AD bind 3/3 + 1 신규 (cj-300 결정 wire 보존):
 *   - AD-2 (audit-first INSERT append-only) — backend 결정 wire (export_csv + export_pdf + export_email + export_scheduled).
 *   - AD-10 (identity + 2FA) — backend owner/admin RBAC 결정 wire.
 *   - AD-12 (verify-first capability gate) — Capability.EXPORT_CSV + Capability.EXPORT_PDF + Capability.EXPORT_EMAIL + Capability.EXPORT_SCHEDULED (cj-285 EXTENSION).
 *
 * NFR bind 4/7 active + 1 신규:
 *   - NFR5 (page load P95 ≤ 5s) — streaming response 결정 wire 보존.
 *   - NFR7 (PDF rendering integrity) — reportlab 결정 wire (cj-293).
 *   - NFR8 (background job 99.9% uptime) — APScheduler restart resilience (신규).
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR labels 결정 wire.
 *
 * CR 11-3 honest-DEFER 244번째 epic 연속 정직 회복
 * (cj-300 entry 의 243번째 + cj-300 wire 의 244번째).
 */

import { useState } from "react";

import { CsvExportTab } from "@/components/reports/CsvExportTab";
import { EmailExportTab } from "@/components/reports/EmailExportTab";
import { PdfExportTab } from "@/components/reports/PdfExportTab";
import { ScheduledJobsList } from "@/components/reports/ScheduledJobsList";

type ExportTab = "csv" | "pdf" | "email" | "scheduled";

interface ReportsTabNavProps {
  accessToken: string;
  tenantId: string;
  initialPeriod: string;
  initialType: "cost-records" | "bom";
}

export function ReportsTabNav({
  accessToken,
  tenantId,
  initialPeriod,
  initialType,
}: ReportsTabNavProps): React.ReactElement {
  const [activeTab, setActiveTab] = useState<ExportTab>("csv");

  return (
    <div data-testid="reports-tab-nav">
      <div
        role="tablist"
        className="border-b border-gray-200 mb-4 flex gap-2"
        data-testid="reports-tab-list"
      >
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "csv"}
          data-testid="reports-tab-csv"
          onClick={() => setActiveTab("csv")}
          className={`px-4 py-2 -mb-px border-b-2 ${
            activeTab === "csv"
              ? "border-blue-500 text-blue-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          CSV 내보내기
        </button>
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "pdf"}
          data-testid="reports-tab-pdf"
          onClick={() => setActiveTab("pdf")}
          className={`px-4 py-2 -mb-px border-b-2 ${
            activeTab === "pdf"
              ? "border-red-500 text-red-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          PDF 내보내기
        </button>
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "email"}
          data-testid="reports-tab-email"
          onClick={() => setActiveTab("email")}
          className={`px-4 py-2 -mb-px border-b-2 ${
            activeTab === "email"
              ? "border-green-500 text-green-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          이메일 발송
        </button>
        <button
          role="tab"
          type="button"
          aria-selected={activeTab === "scheduled"}
          data-testid="reports-tab-scheduled"
          onClick={() => setActiveTab("scheduled")}
          className={`px-4 py-2 -mb-px border-b-2 ${
            activeTab === "scheduled"
              ? "border-purple-500 text-purple-600 font-semibold"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          예약 리포트
        </button>
      </div>

      {activeTab === "csv" ? (
        <CsvExportTab
          accessToken={accessToken}
          tenantId={tenantId}
          initialPeriod={initialPeriod}
          initialType={initialType}
        />
      ) : activeTab === "pdf" ? (
        <PdfExportTab
          accessToken={accessToken}
          tenantId={tenantId}
          initialPeriod={initialPeriod}
          initialType={initialType}
        />
      ) : activeTab === "email" ? (
        <EmailExportTab
          accessToken={accessToken}
          tenantId={tenantId}
          initialPeriod={initialPeriod}
          initialType={initialType}
        />
      ) : (
        <ScheduledJobsList
          accessToken={accessToken}
          tenantId={tenantId}
          initialStatus={null}
        />
      )}
    </div>
  );
}
