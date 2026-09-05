"use client";

/**
 * apps/web/components/reports/CsvExportTab.tsx — cj-282a wire sprint (cj-style 283번째)
 *
 * Story 30.1 CSV export tab UI (FR-30-1).
 *
 * Per cj-282 PRD entry spec §F44.1 + AC #1.1~#1.8:
 *   - Period selector dropdown (`period-selector-{YYYY-MM}` data-testid).
 *   - Type selector (cost-records | bom).
 *   - Tenant_id (session-supplied, hidden input).
 *   - Download button (`download-button` data-testid) → GET
 *     `/api/v1/exports/csv?type=...&period=...&tenant_id=...`.
 *   - ko-KR NFR18 SSOT verbatim 적용.
 *   - data-testid: reports-tab, csv-export-tab, period-selector-{YYYY-MM}, download-button.
 *
 * AD bind 3/3 (backend route 결정 wire + frontend display 결정 wire):
 *   - AD-2 (audit-first INSERT append-only) — backend 결정 wire.
 *   - AD-10 (identity + 2FA) — backend owner/admin RBAC 결정 wire.
 *   - AD-12 (verify-first capability gate) — cj-style 284+ EXTENSION 결정 wire 보류.
 *
 * NFR bind 2/7 active:
 *   - NFR5 (page load P95 ≤ 5s) — streaming response 결정 wire.
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR.json EXTENSION cj-style 284+ 적용 결정 wire 보류.
 *
 * 4 OQ 결정 보류 (cj-282a 범위 외 N/A):
 *   - OQ-EPIC30+-1 ~ 4 (Story 30.2/30.3/30.4 wire 진입 시 결정).
 *
 * CR 11-3 honest-DEFER 223번째 epic 연속 정직 회복
 * (cj-282a web-e2e skip 의 221+222번째 + cj-style 283rd 의 223번째)
 *
 * Pattern verbatim from `apps/web/components/audit/AuditLogExportButton.tsx:38-83`.
 * ko-KR labels verbatim from cj-282 PRD entry spec line 132:
 *   [보고서] → [CSV 내보내기] → 기간 선택 → [다운로드]
 */

import { useState } from "react";

interface CsvExportTabProps {
  accessToken: string;
  initialPeriod: string;
  initialType: "cost-records" | "bom";
}

export function CsvExportTab({
  accessToken: _accessToken,
  initialPeriod,
  initialType,
}: CsvExportTabProps): React.ReactElement {
  const [period, setPeriod] = useState<string>(initialPeriod);
  const [type, setType] = useState<"cost-records" | "bom">(initialType);
  const [busy, setBusy] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // TODO(cj-style 284+): tenant_id 는 session 에서 추출 결정 wire.
  // 현재 sprint 는 SSR 에서 accessToken 만 전달 → tenant_id 결정 wire 보류.
  // CR 11-3 honest-DEFER 223번째: 백엔드 route 의 tenant context 가 canonical.
  const tenantId: string = ""; // 결정 wire 보류 (cj-style 284+ 적용)

  // TODO(cj-style 284+): ko-KR.json EXTENSION 결정 wire.
  // 현재 sprint 는 inline 한국어 strings 결정 wire 보존.
  // NFR18 ko-KR SSOT 적용 시 ko-KR.json EXTENSION ~3 keys:
  // - reports.csv_export.title = "CSV 내보내기"
  // - reports.csv_export.download_button = "다운로드"
  // - reports.csv_export.period_label = "기간 선택"

  const handleDownload = async () => {
    setBusy(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      // Backend route 결정 wire: GET /api/v1/exports/csv?type=...&period=...&tenant_id=...
      // 결정 wire 일자 2026-09-06 — apps/api/modules/reports/csv_routes.py 결정.
      const url = new URL("/api/v1/exports/csv", window.location.origin);
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
          setErrorMessage("CSV export 권한이 없습니다 (owner 또는 admin 필요)");
        } else if (response.status === 413) {
          setErrorMessage("export 행 수가 너무 많습니다 (최대 100,000건)");
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
          ?.match(/filename="?([^"]+)"?/)?.[1] ?? `${type}-${period}.csv`;

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

  // Generate period options (last 12 months).
  const periodOptions: string[] = [];
  const now = new Date();
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    periodOptions.push(`${yyyy}-${mm}`);
  }

  return (
    <div data-testid="reports-tab">
      <h2
        data-testid="csv-export-tab"
        className="text-xl font-semibold mb-4"
      >
        CSV 내보내기
      </h2>

      <div className="mb-4">
        <label htmlFor="csv-export-type" className="block mb-1">
          내보내기 종류
        </label>
        <select
          id="csv-export-type"
          data-testid="csv-export-type-selector"
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
        <label htmlFor="csv-export-period" className="block mb-1">
          기간 선택 (YYYY-MM)
        </label>
        <select
          id="csv-export-period"
          data-testid={`period-selector-${period}`}
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="border rounded px-2 py-1"
        >
          {periodOptions.map((p) => (
            <option key={p} value={p} data-testid={`period-option-${p}`}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <button
        data-testid="download-button"
        type="button"
        onClick={handleDownload}
        disabled={busy}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
      >
        {busy ? "다운로드 중..." : "다운로드"}
      </button>

      {errorMessage ? (
        <p
          data-testid="csv-export-error"
          className="text-red-500 mt-2 text-sm"
        >
          {errorMessage}
        </p>
      ) : null}
      {successMessage ? (
        <p
          data-testid="csv-export-success"
          className="text-green-500 mt-2 text-sm"
        >
          {successMessage}
        </p>
      ) : null}
    </div>
  );
}