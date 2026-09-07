"use client";

/**
 * apps/web/components/reports/ScheduledJobsList.tsx — cj-300 wire sprint (cj-style 302번째)
 *
 * Story 30.4 Scheduled reports UI table component.
 *
 * Pattern verbatim mirror of CsvExportTab.tsx + EmailExportTab.tsx:
 *   - useState hooks for status filter / busy / errorMessage / jobs list
 *   - useEffect fetch initial jobs on mount
 *   - handleCancel with fetch POST + JSON envelope decode
 *   - Inline ko-KR labels (NFR18 SSOT 적용)
 *   - data-testids: scheduled-jobs-list-table, scheduled-job-row,
 *     scheduled-job-cancel-button, scheduled-jobs-refresh-button,
 *     scheduled-status-filter-{value}
 *
 * AD bind 3/3 + 1 신규 (cj-300 결정 wire 보존):
 *   - AD-2 (audit-first INSERT append-only)
 *   - AD-10 (identity + 2FA via owner-only RBAC, AD-22 owner-only)
 *   - AD-12 (verify-first capability gate, Capability.EXPORT_SCHEDULED)
 *
 * NFR bind 4/7 active + 2 신규:
 *   - NFR4 (PII minimization) — finance_contact_email redact 결정 wire 보존.
 *   - NFR8 (background job 99.9% uptime) — APScheduler restart resilience.
 *   - NFR18 (ko-KR vocabulary SSOT) — ko-KR labels 결정 wire 적용.
 *   - NFR19 (export response time) — 결정 wire 보존.
 *
 * CR 11-3 honest-DEFER 243번째 epic 연속 정직 회복
 * (cj-299retro close-out retro 의 242번째 + cj-300 entry 의 243번째).
 */

import { useEffect, useState } from "react";

type ScheduledJobStatus =
  | "scheduled"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "expired";

type DispatchSchedule = "weekly" | "monthly" | "quarterly" | "annual";

type RecipientStrategy =
  | "finance_only"
  | "finance_and_admin"
  | "admin_fallback";

interface ScheduledJob {
  job_id: string;
  tenant_id: string;
  dispatch_schedule: DispatchSchedule;
  cron_expression: string;
  recipient_strategy: RecipientStrategy;
  recipients: {
    strategy: RecipientStrategy;
    recipients: string[];
    admin_fallback_dispatched: boolean;
  };
  report_type: "cost-records" | "bom";
  period_key: string;
  status: ScheduledJobStatus;
  scheduled_at: string;
  trace_id: string | null;
}

interface ScheduledJobsListProps {
  accessToken: string;
  tenantId: string;
  initialStatus: string | null;
}

const STATUS_LABEL_KO: Record<ScheduledJobStatus, string> = {
  scheduled: "예약됨",
  running: "실행 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
  expired: "만료됨",
};

const SCHEDULE_LABEL_KO: Record<DispatchSchedule, string> = {
  weekly: "주간",
  monthly: "월간",
  quarterly: "분기",
  annual: "연간",
};

const STATUS_FILTER_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "전체" },
  { value: "scheduled", label: "예약됨" },
  { value: "running", label: "실행 중" },
  { value: "completed", label: "완료" },
  { value: "failed", label: "실패" },
  { value: "cancelled", label: "취소됨" },
];

export function ScheduledJobsList({
  accessToken,
  tenantId,
  initialStatus,
}: ScheduledJobsListProps): React.ReactElement {
  const [statusFilter, setStatusFilter] = useState<string>(initialStatus ?? "");
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [busy, setBusy] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchJobs = async (status: string) => {
    setBusy(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      params.set("page", "1");
      params.set("page_size", "20");
      const url = `/api/v1/exports/scheduled/jobs?${params.toString()}`;
      const resp = await fetch(url, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Tenant-Id": tenantId,
        },
      });
      if (!resp.ok) {
        const body = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${body}`);
      }
      const data = (await resp.json()) as { jobs: ScheduledJob[]; total: number };
      setJobs(data.jobs);
      setTotal(data.total);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "예약 리포트 목록 조회 실패",
      );
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    void fetchJobs(statusFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const handleCancel = async (jobId: string) => {
    setBusy(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const resp = await fetch(`/api/v1/exports/scheduled/${jobId}/cancel`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Tenant-Id": tenantId,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reason: "사용자 취소" }),
      });
      if (!resp.ok) {
        const body = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${body}`);
      }
      setSuccessMessage(`예약 리포트(${jobId.slice(0, 8)})가 취소되었습니다`);
      // Refresh list.
      await fetchJobs(statusFilter);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "예약 리포트 취소 실패",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="scheduled-jobs-list">
      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="status-filter" className="text-sm font-medium">
          상태:
        </label>
        <select
          id="status-filter"
          data-testid="scheduled-status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-2 py-1 border border-gray-300 rounded"
          disabled={busy}
        >
          {STATUS_FILTER_OPTIONS.map((opt) => (
            <option
              key={opt.value}
              value={opt.value}
              data-testid={`scheduled-status-filter-${opt.value || "all"}`}
            >
              {opt.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          data-testid="scheduled-jobs-refresh-button"
          onClick={() => void fetchJobs(statusFilter)}
          disabled={busy}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {busy ? "조회 중..." : "새로고침"}
        </button>
        <span className="text-sm text-gray-600" data-testid="scheduled-jobs-total">
          총 {total}건
        </span>
      </div>

      {errorMessage && (
        <div
          role="alert"
          className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm"
          data-testid="scheduled-jobs-error"
        >
          {errorMessage}
        </div>
      )}
      {successMessage && (
        <div
          role="status"
          className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-800 text-sm"
          data-testid="scheduled-jobs-success"
        >
          {successMessage}
        </div>
      )}

      {jobs.length === 0 ? (
        <p
          className="text-gray-500 text-sm"
          data-testid="scheduled-jobs-empty"
        >
          예약된 리포트가 없습니다.
        </p>
      ) : (
        <table
          className="w-full border-collapse border border-gray-300 text-sm"
          data-testid="scheduled-jobs-list-table"
        >
          <thead className="bg-gray-100">
            <tr>
              <th className="border border-gray-300 px-3 py-2 text-left">작업 ID</th>
              <th className="border border-gray-300 px-3 py-2 text-left">주기</th>
              <th className="border border-gray-300 px-3 py-2 text-left">기간</th>
              <th className="border border-gray-300 px-3 py-2 text-left">상태</th>
              <th className="border border-gray-300 px-3 py-2 text-left">수신자</th>
              <th className="border border-gray-300 px-3 py-2 text-left">액션</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr
                key={job.job_id}
                className="hover:bg-gray-50"
                data-testid="scheduled-job-row"
              >
                <td className="border border-gray-300 px-3 py-2 font-mono text-xs">
                  {job.job_id.slice(0, 8)}
                </td>
                <td className="border border-gray-300 px-3 py-2">
                  {SCHEDULE_LABEL_KO[job.dispatch_schedule]}
                </td>
                <td className="border border-gray-300 px-3 py-2">
                  {job.period_key}
                </td>
                <td className="border border-gray-300 px-3 py-2">
                  {STATUS_LABEL_KO[job.status]}
                </td>
                <td className="border border-gray-300 px-3 py-2 text-xs">
                  {job.recipients.admin_fallback_dispatched
                    ? "admin fallback"
                    : `${job.recipients.recipients.length}명`}
                </td>
                <td className="border border-gray-300 px-3 py-2">
                  {job.status === "scheduled" || job.status === "running" ? (
                    <button
                      type="button"
                      data-testid="scheduled-job-cancel-button"
                      onClick={() => void handleCancel(job.job_id)}
                      disabled={busy}
                      className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                    >
                      취소
                    </button>
                  ) : (
                    <span className="text-gray-400 text-xs">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
