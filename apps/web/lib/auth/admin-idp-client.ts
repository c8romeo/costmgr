/**
 * apps/web/lib/auth/admin-idp-client.ts — Epic 16 T4 (AC #7.2, #7.3)
 *
 * Tenant IdP admin CRUD fetch wrapper.
 *
 * Wraps 4 backend admin endpoints (CRUD API from
 * `apps/api/modules/auth/sso/idp_admin_routes.py`):
 *   - GET    /api/v1/admin/tenant/{slug}/idp
 *   - POST   /api/v1/admin/tenant/{slug}/idp
 *   - PUT    /api/v1/admin/tenant/{slug}/idp
 *   - DELETE /api/v1/admin/tenant/{slug}/idp       (owner only)
 *   - POST   /api/v1/admin/tenant/{slug}/idp/test  (8-step dry-run)
 *
 * All callers MUST pass an `accessToken` (read from the
 * `sb-access-token` cookie in the parent component). The wrapper
 * adds `Authorization: Bearer <token>` + `X-Trace-Id` headers, and
 * parses the CR 12-5 D-14 typed exception envelope:
 *
 *   { code: string, message_ko: string, details?: object, trace_id?: string }
 *
 * TS mirror parity mandatory (CR 11-4 D-004): the interface fields
 * MUST stay in sync with the Pydantic models `IdPConfigResponse`,
 * `IdPConfigCreateRequest`, `IdPTestResultResponse` and
 * `IdPTestResultStep` in `idp_admin_routes.py`.
 */

export interface IdPConfig {
  id: string;
  tenant_id: string;
  idp_entity_id: string;
  idp_sso_url: string;
  idp_slo_url: string | null;
  /** SHA-256 fingerprint only — NFR4 PII minimization. */
  idp_x509_cert_sha256: string;
  acs_url: string;
  name_id_format: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface IdPCreateRequest {
  metadata_xml?: string | null;
  idp_entity_id?: string | null;
  idp_sso_url?: string | null;
  idp_x509_cert_pem?: string | null;
  idp_slo_url?: string | null;
  acs_url?: string | null;
  name_id_format?: string | null;
  enabled?: boolean;
}

export interface IdPTestStep {
  step: number;
  name: string;
  passed: boolean;
  detail: string | null;
}

export interface IdPTestResult {
  passed: boolean;
  steps: IdPTestStep[];
  metadata: {
    entity_id: string;
    sso_url: string;
    slo_url: string | null;
    name_id_format: string | null;
  } | null;
}

export interface IdPApiError {
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

class IdPAdminApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  trace_id: string | undefined;
  status: number;
  /** Korean error message (CR 12-5 D-14 envelope field). */
  message_ko: string;

  constructor(status: number, payload: IdPApiError | { detail?: string }) {
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

async function parseError(res: Response): Promise<IdPAdminApiError> {
  let payload: IdPApiError | { detail?: string } = {};
  try {
    payload = (await res.json()) as IdPApiError;
  } catch {
    // non-JSON body — fall through with empty payload.
  }
  return new IdPAdminApiError(res.status, payload);
}

export interface ListIdPConfigsResult {
  ok: boolean;
  data: IdPConfig[];
  error?: IdPAdminApiError;
}

export async function listIdPConfigs(
  accessToken: string,
  tenantSlug: string,
): Promise<ListIdPConfigsResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/admin/tenant/${encodeURIComponent(tenantSlug)}/idp`,
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
      return { ok: false, data: [], error };
    }
    const data = (await res.json()) as IdPConfig[];
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      data: [],
      error: new IdPAdminApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export interface CreateIdPConfigResult {
  ok: boolean;
  data?: IdPConfig;
  error?: IdPAdminApiError;
}

export async function createIdPConfig(
  accessToken: string,
  tenantSlug: string,
  body: IdPCreateRequest,
): Promise<CreateIdPConfigResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/admin/tenant/${encodeURIComponent(tenantSlug)}/idp`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as IdPConfig;
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: new IdPAdminApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export interface UpdateIdPConfigResult {
  ok: boolean;
  data?: IdPConfig;
  error?: IdPAdminApiError;
}

export async function updateIdPConfig(
  accessToken: string,
  tenantSlug: string,
  body: IdPCreateRequest,
): Promise<UpdateIdPConfigResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/admin/tenant/${encodeURIComponent(tenantSlug)}/idp`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as IdPConfig;
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: new IdPAdminApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export interface DeleteIdPConfigResult {
  ok: boolean;
  error?: IdPAdminApiError;
}

export async function deleteIdPConfig(
  accessToken: string,
  tenantSlug: string,
): Promise<DeleteIdPConfigResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/admin/tenant/${encodeURIComponent(tenantSlug)}/idp`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    return { ok: true };
  } catch (err) {
    return {
      ok: false,
      error: new IdPAdminApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export interface TestIdPConfigResult {
  ok: boolean;
  data?: IdPTestResult;
  error?: IdPAdminApiError;
}

export async function testIdPConfig(
  accessToken: string,
  tenantSlug: string,
  metadata_xml: string,
): Promise<TestIdPConfigResult> {
  const traceId = crypto.randomUUID();
  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/admin/tenant/${encodeURIComponent(tenantSlug)}/idp/test`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
          "X-Trace-Id": traceId,
        },
        body: JSON.stringify({ metadata_xml }),
      },
    );
    if (!res.ok) {
      const error = await parseError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as IdPTestResult;
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: new IdPAdminApiError(0, {
        code: "NETWORK_ERROR",
        message_ko:
          err instanceof Error ? err.message : "네트워크 오류가 발생했습니다",
      }),
    };
  }
}

export { IdPAdminApiError };
