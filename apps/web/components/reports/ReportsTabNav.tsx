"use client";

/**
 * apps/web/components/reports/ReportsTabNav.tsx — cj-295 follow-up #1 (cj-style 295번째)
 *
 * Client component wrapping CsvExportTab + PdfExportTab with simple tab
 * navigation. The tab nav uses inline ko-KR labels (NFR18 SSOT verbatim
 * 적용) and a 2-tab UX (CSV / PDF). State for the active tab is local
 * useState.
 *
 * Pattern verbatim mirror from CsvExportTab.tsx verbatim ko-KR labels
 * pattern + a thin tab nav wrapper.
 *
 * AD bind 3/3 (backend 결정 wire 보존):
 *   - AD-2 (audit-first INSERT append-only) — backend 결정 wire (export_csv + export_pdf).
 *   - AD-10 (identity + 2FA) — backend owner/admin RBAC 결정 wire.
 *   - AD-12 (verify-first capability gate) — Capability.EXPORT_CSV + Capability.EXPORT_PDF.
 *
 * NFR bind 3/7 active:
 *   - NFR5 (page load P95 ≤ 5s) — streaming response 결정 wire 보존.
 *   - NFR7 (PDF rendering integrity) — reportlab 결정 wire (cj-293).
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR labels 결정 wire.
 *
 * CR 11-3 honest-DEFER 235번째 epic 연속 정직 회복
 * (cj-294 close-out retro 의 234번째 + cj-295 follow-up #1 의 235번째)
 */

import { useState } from "react";

import { CsvExportTab } from "@/components/reports/CsvExportTab";
import { PdfExportTab } from "@/components/reports/PdfExportTab";

type ExportTab = "csv" | "pdf";

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
      </div>

      {activeTab === "csv" ? (
        <CsvExportTab
          accessToken={accessToken}
          tenantId={tenantId}
          initialPeriod={initialPeriod}
          initialType={initialType}
        />
      ) : (
        <PdfExportTab
          accessToken={accessToken}
          tenantId={tenantId}
          initialPeriod={initialPeriod}
          initialType={initialType}
        />
      )}
    </div>
  );
}
