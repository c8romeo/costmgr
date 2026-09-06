"use client";

/**
 * apps/web/components/reports/PdfExportTab.tsx — cj-293 follow-up #1 (cj-style 295번째)
 *
 * Story 30.2 PDF export tab UI (FR-30-2, cj-282 PRD entry §F30.2-1).
 *
 * Companion component for `apps/api/modules/reports/pdf_routes.py` (cj-293 wire sprint).
 *
 * Per cj-293 wire 결정 wire + cj-282 PRD entry §F30.2-1:
 *   - Period selector dropdown (`period-selector-{YYYY-MM}` data-testid).
 *   - Type selector (cost-records | bom).
 *   - Tenant_id (session-supplied, hidden input).
 *   - Download button (`pdf-download-button` data-testid) → GET
 *     `/api/v1/exports/pdf?type=...&period=...&tenant_id=...`.
 *   - ko-KR NFR18 SSOT verbatim 적용.
 *   - data-testid: pdf-export-tab, period-selector-{YYYY-MM}, pdf-download-button.
 *
 * Pattern verbatim from `apps/web/components/reports/CsvExportTab.tsx:46-216`
 * (cj-282a wire sprint 결정 wire).
 *
 * AD bind 3/3 (backend 결정 wire 보존, frontend display 결정 wire):
 *   - AD-2 (audit-first INSERT append-only) — backend 결정 wire (cj-293 export_pdf).
 *   - AD-10 (identity + 2FA) — backend owner/admin RBAC 결정 wire.
 *   - AD-12 (verify-first capability gate) — Capability.EXPORT_PDF (cj-285 EXTENSION).
 *
 * NFR bind 3/7 active:
 *   - NFR5 (page load P95 ≤ 5s) — streaming response 결정 wire 보존.
 *   - NFR7 (PDF rendering integrity) — backend reportlab 결정 wire.
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR labels 결정 wire (cj-style 296+ ko-KR.json EXTENSION 결정 wire 보류).
 *
 * OQ 결정 wire 보류 (cj-282 PRD entry 범위 외):
 *   - OQ-EPIC30+-2 SMTP 인프라 외부 의존 (Story 30.3 Email, cj-style 295+ 결정 wire 진입 시 결정)
 *   - OQ-EPIC30+-3 APScheduler vs Celery beat vs cron (Story 30.4 Scheduled, cj-style 296+ 결정 wire 진입 시 결정)
 *
 * CR 11-3 honest-DEFER 235번째 epic 연속 정직 회복
 * (cj-294 close-out retro 의 234번째 + cj-295 follow-up #1 의 235번째)
 */

import { useState } from "react";

interface PdfExportTabProps {
  accessToken: string;
  tenantId: string; // supplied by reports/page.tsx JWT decode (cj-287 wire 결정 wire 보존)
  initialPeriod: string;
  initialType: "cost-records" | "bom";
}

export function PdfExportTab({
  accessToken: _accessToken,
  tenantId,
  initialPeriod,
  initialType,
}: PdfExportTabProps): React.ReactElement {
  const [period, setPeriod] = useState<string>(initialPeriod);
  const [type, setType] = useState<"cost-records" | "bom">(initialType);
  const [busy, setBusy] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // tenantId is supplied by reports/page.tsx via JWT decode of
  // app_metadata.tenant_id. AD-56(c) route-level guard
  // (Capability.EXPORT_PDF) + CR 0-2 RLS cross-tenant check enforced on
  // backend (pdf_routes.py). The query param is required
  // (pdf_routes.py PdfExportRequest Pydantic schema tenant_id UUID4) —
  // empty value would trigger 422 validation error.

  // TODO(cj-style 296+): ko-KR.json EXTENSION 결정 wire.
  // 현재 sprint 는 inline 한국어 strings 결정 wire 보존.
  // NFR18 ko-KR SSOT 적용 시 ko-KR.json EXTENSION ~3 keys:
  // - reports.pdf_export.title = "PDF 내보내기"
  // - reports.pdf_export.download_button = "PDF 다운로드"
  // - reports.pdf_export.period_label = "기간 선택"

  const handleDownload = async () => {
    setBusy(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      // Backend route 결정 wire: GET /api/v1/exports/pdf?type=...&period=...&tenant_id=...
      // 결정 wire 일자 2026-09-06 — apps/api/modules/reports/pdf_routes.py 결정.
      const url = new URL("/api/v1/exports/pdf", window.location.origin);
      url.searchParams.set("type", type);
      url.searchParams.set("period", period);
      if (tenantId) {
        url.searchParams.set("tenant_id", tenantId);
      }

      const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${_accessToken}`,
        },
      });

      if (!response.ok) {
        if (response.status === 403) {
          setErrorMessage("PDF export 권한이 없습니다 (owner 또는 admin 필요)");
        } else if (response.status === 413) {
          setErrorMessage("export 행 수가 너무 많습니다 (최대 100,000건)");
        } else if (response.status === 500 && errorMessage?.includes("font")) {
          setErrorMessage("PDF 폰트 등록 실패 — Korean 폰트 미설치 환경");
        } else {
          setErrorMessage(`내보내기 실패 (HTTP ${response.status})`);
        }
        setBusy(false);
        return;
      }

      // StreamingResponse → blob 변환 → download trigger.
      // NFR5 streaming P95 ≤ 5s 결정 wire 보존.
      const blob = await response.blob();
      const filename =
        response.headers
          .get("Content-Disposition")
          ?.match(/filename="?([^"]+)"?/)?.[1] ?? `${type}-${period}.pdf`;

      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(blobUrl);

      setSuccessMessage(`${filename} 다운로드 완료`);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      );
    } finally {
      setBusy(false);
    }
  };

  // Generate period options (last 12 months) — cj-282a CsvExportTab verbatim mirror pattern.
  const periodOptions: string[] = [];
  const now = new Date();
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    periodOptions.push(`${yyyy}-${mm}`);
  }

  return (
    <div data-testid="pdf-export-tab-panel">
      <h2
        data-testid="pdf-export-tab"
        className="text-xl font-semibold mb-4"
      >
        PDF 내보내기
      </h2>

      <div className="mb-4">
        <label htmlFor="pdf-export-type" className="block mb-1">
          내보내기 종류
        </label>
        <select
          id="pdf-export-type"
          data-testid="pdf-export-type-selector"
          value={type}
          onChange={(e) =>
            setType(e.target.value as "cost-records" | "bom")
          }
          className="border rounded px-2 py-1"
        >
          <option value="cost-records">원가 기록 (cost-records)</option>
          <option value="bom">BOM level 1</option>
        </select>
      </div>

      <div className="mb-4">
        <label htmlFor="pdf-export-period" className="block mb-1">
          기간 선택 (YYYY-MM)
        </label>
        <select
          id="pdf-export-period"
          data-testid={`pdf-period-selector-${period}`}
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="border rounded px-2 py-1"
        >
          {periodOptions.map((p) => (
            <option key={p} value={p} data-testid={`pdf-period-option-${p}`}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <button
        data-testid="pdf-download-button"
        type="button"
        onClick={handleDownload}
        disabled={busy}
        className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:bg-gray-400"
      >
        {busy ? "PDF 생성 중..." : "PDF 다운로드"}
      </button>

      {errorMessage ? (
        <p
          data-testid="pdf-export-error"
          className="text-red-500 mt-2 text-sm"
        >
          {errorMessage}
        </p>
      ) : null}
      {successMessage ? (
        <p
          data-testid="pdf-export-success"
          className="text-green-500 mt-2 text-sm"
        >
          {successMessage}
        </p>
      ) : null}
    </div>
  );
}
