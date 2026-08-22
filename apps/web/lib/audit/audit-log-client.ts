/**
 * apps/web/lib/audit/audit-log-client.ts — Epic 17 T2 (AC #2.8, #2.12)
 *
 * Audit log viewer fetch wrapper + TS interface mirrors.
 *
 * Wraps the audit log backend endpoints (wired in commit `2ada2ec`,
 * `apps/api/modules/audit/audit_log_routes.py`):
 *   - GET    /api/v1/audit-log
 *   - GET    /api/v1/audit-log/{entry_id}
 *   - GET    /api/v1/audit-log/count
 *   - GET    /api/v1/audit-log/export  (CSV stream)
 *
 * All callers MUST pass an `accessToken` (read from the
 * `sb-access-token` cookie in the parent component). The wrapper
 * adds `Authorization: Bearer <token>` + `X-Trace-Id` headers, and
 * parses the CR 12-5 D-14 typed exception envelope:
 *
 *   { code: string, message_ko: string, details?: object, trace_id?: string }
 *
 * TS mirror parity mandatory (CR 11-4 D-004 + CR 12-5 D-PARITY-01):
 * the interface fields MUST stay in sync with the Pydantic models
 * `AuditLogQueryFilters` + `AuditLogEntry` + `AuditLogPage` in
 * `apps/api/modules/audit/audit_log_query.py`. Drift is caught by
 * `apps/web/__tests__/audit-log/audit-log-client.test.ts`.
 */

// ── TS interface mirrors (CR 12-5 D-PARITY-01 inversion verbatim) ──

export interface AuditLogQueryFilters {
  actor_id: string | null;
  action: string | null;
  action_class: string | null;
  resource_type: string | null;
  resource_id: string | null;
  start_date: string | null;
  end_date: string | null;
  trace_id: string | null;
}

export interface AuditLogEntry {
  id: number;
  tenant_id: string;
  actor_id: string;
  action: string;
  action_class: string;
  resource_type: string | null;
  resource_id: string | null;
  payload: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  trace_id: string;
  created_at: string;
}

export interface AuditLogPage {
  entries: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface ActivityStreamGroup {
  timestamp_bucket: string;
  entry_count: number;
  top_actions: string[];
  top_actors: string[];
}

export interface AuditLogApiErrorEnvelope {
  code: string;
  message_ko: string;
  details?: Record<string, unknown>;
  trace_id?: string;
}

const DEFAULT_API_BASE_URL =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "http://localhost:8765";

function apiBaseUrl(): string {
  return DEFAULT_API_BASE_URL;
}

class AuditLogApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  trace_id: string | undefined;
  status: number;
  /** Korean error message (CR 12-5 D-14 envelope field). */
  message_ko: string;

  constructor(
    status: number,
    payload: AuditLogApiErrorEnvelope | { detail?: string },
  ) {
    const fallbackDetail = "detail" in payload ? payload.detail ?? "오류" : "오류";
    const messageKo =
      "message_ko" in payload && payload.message_ko
        ? payload.message_ko
        : fallbackDetail;
    super(messageKo);
    this.status = status;
    this.code = "code" in payload ? payload.code : `HTTP_${status}`;
    this.details = ("details" in payload && payload.details) || {};
    this.trace_id = "trace_id" in payload ? payload.trace_id : undefined;
    this.message_ko = messageKo;
  }
}

async function parseError(res: Response): Promise<AuditLogApiError> {
  let payload: AuditLogApiErrorEnvelope | { detail?: string } = {};
  try {
    payload = (await res.json()) as AuditLogApiErrorEnvelope;
  } catch {
    // non-JSON body — fall through with empty payload.
  }
  return new AuditLogApiError(res.status, payload);
}

function buildQuery(
  filters: AuditLogQueryFilters,
  page: number,
  pageSize: number,
): string {
  const params = new URLSearchParams();
  if (filters.actor_id) params.set("actor_id", filters.actor_id);
  if (filters.action) params.set("action", filters.action);
  if (filters.action_class) params.set("action_class", filters.action_class);
  if (filters.resource_type) params.set("resource_type", filters.resource_type);
  if (filters.resource_id) params.set("resource_id", filters.resource_id);
  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  if (filters.trace_id) params.set("trace_id", filters.trace_id);
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  return params.toString();
}

export interface FetchAuditLogResult {
  ok: boolean;
  data?: AuditLogPage;
  error?: AuditLogApiError;
}

export async function fetchAuditLog(
  accessToken: string,
  filters: AuditLogQueryFilters,
  page: number,
  pageSize: number,
): Promise<FetchAuditLogResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/audit-log?${buildQuery(filters, page, pageSize)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        cache: "no-store",
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as AuditLogPage;
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: new AuditLogApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export interface FetchAuditLogEntryResult {
  ok: boolean;
  data?: AuditLogEntry;
  error?: AuditLogApiError;
}

export async function fetchAuditLogEntry(
  accessToken: string,
  entryId: number,
): Promise<FetchAuditLogEntryResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/audit-log/${entryId}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        cache: "no-store",
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as AuditLogEntry;
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: new AuditLogApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export interface FetchAuditLogCountResult {
  ok: boolean;
  data?: number;
  error?: AuditLogApiError;
}

export async function fetchAuditLogCount(
  accessToken: string,
  filters: AuditLogQueryFilters,
): Promise<FetchAuditLogCountResult> {
  const traceId = crypto.randomUUID();
  try {
    const params = new URLSearchParams();
    if (filters.actor_id) params.set("actor_id", filters.actor_id);
    if (filters.action) params.set("action", filters.action);
    if (filters.action_class) params.set("action_class", filters.action_class);
    if (filters.resource_type) params.set("resource_type", filters.resource_type);
    if (filters.resource_id) params.set("resource_id", filters.resource_id);
    if (filters.start_date) params.set("start_date", filters.start_date);
    if (filters.end_date) params.set("end_date", filters.end_date);
    if (filters.trace_id) params.set("trace_id", filters.trace_id);
    const qs = params.toString();
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/audit-log/count${qs ? `?${qs}` : ""}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        cache: "no-store",
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as number;
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: new AuditLogApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export interface ExportAuditLogCsvResult {
  ok: boolean;
  blob?: Blob;
  filename?: string;
  error?: AuditLogApiError;
}

export async function exportAuditLogCsv(
  accessToken: string,
  filters: AuditLogQueryFilters,
): Promise<ExportAuditLogCsvResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/audit-log/export?${buildQuery(filters, 1, 100_000)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        cache: "no-store",
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") ?? "";
    const filenameMatch = /filename="([^"]+)"/.exec(disposition);
    const filename = filenameMatch?.[1] ?? `audit-log-${Date.now()}.csv`;
    return { ok: true, blob, filename };
  } catch (err) {
    return {
      ok: false,
      error: new AuditLogApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export { AuditLogApiError };

// ── Activity stream fetcher (Epic 17 T3 /activity) ────────────────

export interface FetchActivityStreamResult {
  ok: boolean;
  data?: ActivityStreamGroup[];
  error?: AuditLogApiError;
}

export async function fetchActivityStream(
  accessToken: string,
  windowDays: 1 | 7 | 30 | 90,
): Promise<FetchActivityStreamResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/activity?window_days=${windowDays}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        cache: "no-store",
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as ActivityStreamGroup[];
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: new AuditLogApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}
