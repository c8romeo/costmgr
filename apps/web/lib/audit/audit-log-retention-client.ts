/**
 * apps/web/lib/audit/audit-log-retention-client.ts — Phase 6 T7a (AC #7.1~#7.4)
 *
 * Phase 6 (cj-style 87번째 epic 연속 정직 회복 wire) — AD-33 (a)+(c)+(f).
 *
 * Audit log retention policy + erasure fetch wrapper + TS interface
 * mirrors. Wraps the Phase 6 retention backend endpoints (atomic wire
 * `0040_phase_6_audit_retention` + `apps/api/modules/audit/retention/
 * retention_routes.py`):
 *
 *   - GET    /api/v1/audit-log/retention
 *   - GET    /api/v1/audit-log/retention/{action_class}
 *   - POST   /api/v1/audit-log/retention
 *   - PUT    /api/v1/audit-log/retention/{action_class}
 *   - DELETE /api/v1/audit-log/retention/{action_class}
 *   - POST   /api/v1/audit-log/retention/preview
 *   - POST   /api/v1/audit-log/retention/{action_class}/cold-archive
 *   - POST   /api/v1/audit-log/erase (GDPR Article 17)
 *
 * All callers MUST pass an `accessToken` (read from the
 * `sb-access-token` cookie in the parent component). The wrapper
 * adds `Authorization: Bearer <token>` + `X-Trace-Id` headers, and
 * parses the CR 12-5 D-14 typed exception envelope.
 *
 * TS mirror parity mandatory (CR 11-4 D-004 + CR 12-5 D-PARITY-01):
 * the interface fields MUST stay in sync with the Pydantic models
 * `RetentionPolicy` + `ErasureRequest` + `PurgePreviewRequest` in
 * `apps/api/modules/audit/retention/retention_routes.py` +
 * `retention_dsl.py`. Drift is caught by
 * `apps/web/__tests__/audit/audit-log-retention-client.test.ts`.
 */

// ── TS interface mirrors (CR 12-5 D-PARITY-01 inversion verbatim) ──

export type RetentionClass = "admin" | "auth" | "data" | "security";

export interface RetentionPolicy {
  tenant_id: string;
  action_class: RetentionClass;
  days: number;
  archive: boolean;
  mask_pii: boolean;
}

export interface PurgePreviewResult {
  action_class: RetentionClass;
  days: number;
  would_purge_count: number;
  dry_run: true;
  trace_id: string;
}

export interface ErasureResult {
  erased_count: number;
  trace_id: string;
  scope: "all" | "actor" | "tenant";
  actor_id: string;
  tenant_id: string;
  archived_preserved: boolean;
}

export interface AuditLogRetentionApiErrorEnvelope {
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

class AuditLogRetentionApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  trace_id: string | undefined;
  status: number;
  message_ko: string;

  constructor(
    status: number,
    payload: AuditLogRetentionApiErrorEnvelope | { detail?: string },
  ) {
    const fallbackDetail = "detail" in payload ? payload.detail ?? "오류" : "오류";
    const messageKo =
      "message_ko" in payload && payload.message_ko
        ? payload.message_ko
        : fallbackDetail;
    super(messageKo);
    this.name = "AuditLogRetentionApiError";
    this.code = ("code" in payload && payload.code) || "AUDIT_LOG_RETENTION_UNKNOWN";
    this.details = ("details" in payload && payload.details) || {};
    this.trace_id = ("trace_id" in payload && payload.trace_id) || undefined;
    this.status = status;
    this.message_ko = messageKo;
  }
}

interface FetchOpts {
  accessToken: string;
  traceId?: string;
  signal?: AbortSignal;
}

async function _request<T>(
  path: string,
  init: RequestInit,
  opts: FetchOpts,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${opts.accessToken}`,
    "X-Trace-Id": opts.traceId ?? crypto.randomUUID(),
    ...(init.headers as Record<string, string> | undefined),
  };
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers,
    signal: opts.signal ?? null,
  });
  if (!res.ok) {
    let payload: AuditLogRetentionApiErrorEnvelope | { detail?: string } = {};
    try {
      payload = (await res.json()) as typeof payload;
    } catch {
      // ignore body parse errors; envelope stays {}
    }
    throw new AuditLogRetentionApiError(res.status, payload);
  }
  if (res.status === 204) {
    return undefined as unknown as T;
  }
  return (await res.json()) as T;
}

/* ── Fetch wrappers (CR 12-5 D-14 envelope parse) ── */

export async function listRetentionPolicies(opts: FetchOpts): Promise<{ policies: RetentionPolicy[]; trace_id: string }> {
  return _request("/api/v1/audit-log/retention", { method: "GET" }, opts);
}

export async function getRetentionPolicy(
  action_class: RetentionClass,
  opts: FetchOpts,
): Promise<RetentionPolicy> {
  return _request(
    `/api/v1/audit-log/retention/${action_class}`,
    { method: "GET" },
    opts,
  );
}

export async function createRetentionPolicy(
  payload: Omit<RetentionPolicy, "tenant_id">,
  opts: FetchOpts,
): Promise<RetentionPolicy> {
  return _request(
    "/api/v1/audit-log/retention",
    { method: "POST", body: JSON.stringify(payload) },
    opts,
  );
}

export async function updateRetentionPolicy(
  action_class: RetentionClass,
  payload: Partial<Omit<RetentionPolicy, "tenant_id" | "action_class">>,
  opts: FetchOpts,
): Promise<RetentionPolicy> {
  return _request(
    `/api/v1/audit-log/retention/${action_class}`,
    { method: "PUT", body: JSON.stringify(payload) },
    opts,
  );
}

export async function deleteRetentionPolicy(
  action_class: RetentionClass,
  opts: FetchOpts,
): Promise<void> {
  return _request<void>(
    `/api/v1/audit-log/retention/${action_class}`,
    { method: "DELETE" },
    opts,
  );
}

export async function previewPurge(
  payload: { action_class: RetentionClass },
  opts: FetchOpts,
): Promise<PurgePreviewResult> {
  return _request(
    "/api/v1/audit-log/retention/preview",
    { method: "POST", body: JSON.stringify(payload) },
    opts,
  );
}

export async function triggerColdArchive(
  action_class: RetentionClass,
  opts: FetchOpts,
): Promise<{ action_class: RetentionClass; cold_archive_triggered: boolean; trace_id: string }> {
  return _request(
    `/api/v1/audit-log/retention/${action_class}/cold-archive`,
    { method: "POST" },
    opts,
  );
}

export async function requestAuditLogErasure(
  payload: {
    actor_id: string;
    scope: "all" | "actor" | "tenant";
    reason: string;
  },
  opts: FetchOpts,
): Promise<ErasureResult> {
  return _request(
    "/api/v1/audit-log/erase",
    { method: "POST", body: JSON.stringify(payload) },
    opts,
  );
}

export {
  AuditLogRetentionApiError,
};
