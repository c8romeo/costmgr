/**
 * apps/web/lib/api-client.ts — typed fetch wrapper for the costmgr API.
 *
 * Story 1.1 — Task 3.5 (lightweight wrapper). The wrapper:
 *   - Adds `Authorization: Bearer <jwt>` from a session token when provided.
 *   - Falls back to `credentials: "same-origin"` when no token is
 *     supplied so the backend's cookie-based session is forwarded.
 *   - Parses JSON safely — falls back to a typed ApiError on
 *     non-JSON / empty responses (HTML proxy 502, empty 204, etc.).
 *   - Throws typed `ApiError` with `{ code, message_ko, details, trace_id }`
 *     matching the AD-15 error contract.
 *   - Exposes `getTenantSettings()` + `updateIndustry()` typed methods.
 *
 * Per AD-15: snake_case JSON keys throughout. Per Story 1.1 — the
 * `X-Onboarding-Warning` response header is surfaced via the
 * `warningHeader` field on the success envelope. The `X-Trace-Id` header
 * is forwarded as `traceId`.
 *
 * Review patches applied (Story 1.2 Chunk-A code review):
 *   F-13 — on 401 (token expired) the wrapper attempts ONE retry with the
 *          cookie session before bubbling up. This saves the user a
 *          forced reload when the access token expired but the cookie
 *          session is still valid.
 *   F-14 — every request has a 10-second timeout via AbortController so
 *          a hung backend does not freeze the wizard forever.
 *   F-18 — `save*` functions also expose `X-Onboarding-Warning` via an
 *          optional `onWarningHeader` callback so the wizard can surface
 *          "value locked due to existing calculations" (A7).
 *   F-25 — `ApiError` sets `name = "ApiError"` so `error.name === "ApiError"`
 *          discriminates cleanly in call sites.
 */

import type { Industry } from "./menu-config";

export interface ApiErrorPayload {
  code: string;
  message_ko: string;
  details: Record<string, unknown>;
  trace_id: string;
}

export class ApiError extends Error {
  // F-25: explicit `.name` so `e.name === "ApiError"` works for
  // discrimination without `instanceof` (the latter fails across realms
  // such as SSR/edge runtimes).
  override readonly name = "ApiError";
  readonly status: number;
  readonly payload: ApiErrorPayload;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message_ko);
    this.status = status;
    this.payload = payload;
  }
}

export interface TenantSettingsResponse {
  tenant_id: string;
  industry: Industry | null;
  settings_version: number;
  onboarding: Record<string, unknown>;
  baseline: Record<string, unknown>;
  abc: Record<string, unknown>;
  ai: Record<string, unknown>;
}

export interface IndustryUpdateResponse {
  industry: Industry;
  menu: string[];
  settings_version: number;
  is_initial: boolean;
  selected_at: string;
  trace_id: string;
}

export interface IndustryUpdateOptions {
  industry: Industry;
  /** Optional callback fired when the within-grace warning header arrives. */
  onWarningHeader?: (value: string) => void;
}

// F-14: default request timeout. Keep generous enough for slow LLM-bound
// routes (later stories) without leaving the user hanging on a wedged
// backend.
const DEFAULT_TIMEOUT_MS = 10_000;

async function parseJsonSafe(res: Response): Promise<unknown> {
  // Defensive JSON parse. Empty 204, HTML proxy 502, or any
  // non-JSON body must produce a typed fallback rather than throw.
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { __non_json__: true, body: text };
  }
}

function isApiErrorPayload(value: unknown): value is ApiErrorPayload {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.code === "string" &&
    typeof v.message_ko === "string" &&
    typeof v.trace_id === "string" &&
    typeof v.details === "object" &&
    v.details !== null
  );
}

/** F-13: retry once on 401 with cookie session. Returns the same shape
 *  as `request`. */
async function request<T>(
  path: string,
  init: RequestInit,
  accessToken?: string,
  onWarningHeader?: (value: string) => void,
): Promise<{ data: T; headers: Headers }> {
  const doFetch = async (tokenOverride?: string): Promise<Response> => {
    const headers = new Headers(init.headers);
    const token = tokenOverride ?? accessToken;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    // Include cookie credentials when no bearer token is provided so
    // the backend's cookie session can authenticate the request.
    const credentials: RequestCredentials = token
      ? init.credentials ?? "omit"
      : init.credentials ?? "same-origin";

    // F-14: per-request AbortController timeout. We do NOT reuse a
    // shared controller (caller might cancel mid-retry).
    const controller = new AbortController();
    const timer = setTimeout(
      () => controller.abort(new DOMException("Request timeout", "TimeoutError")),
      DEFAULT_TIMEOUT_MS,
    );
    try {
      return await fetch(path, {
        ...init,
        headers,
        credentials,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }
  };

  let res = await doFetch();

  // F-13: one-shot 401 retry with no bearer (lets the cookie session
  // take over). Only attempted when the caller originally supplied a
  // token — without a token, the first attempt already used cookies
  // and a 401 is a true auth failure.
  if (
    res.status === 401 &&
    accessToken &&
    init.credentials !== "include"
  ) {
    res = await doFetch(undefined);
  }

  if (!res.ok) {
    const payload = (await parseJsonSafe(res)) as unknown;
    if (isApiErrorPayload(payload)) {
      throw new ApiError(res.status, payload);
    }
    const fallbackMessage =
      typeof payload === "object" &&
      payload !== null &&
      "__non_json__" in payload
        ? `서버 응답을 해석할 수 없습니다 (HTTP ${res.status})`
        : `요청 실패 (HTTP ${res.status})`;
    throw new ApiError(res.status, {
      code: "UNPARSEABLE_RESPONSE",
      message_ko: fallbackMessage,
      details: { raw: String(payload) },
      trace_id: res.headers.get("X-Trace-Id") ?? "",
    });
  }

  const dataRaw = (await parseJsonSafe(res)) as unknown;
  if (dataRaw === null) {
    throw new ApiError(res.status, {
      code: "EMPTY_RESPONSE",
      message_ko: "서버 응답이 비어 있습니다",
      details: {},
      trace_id: res.headers.get("X-Trace-Id") ?? "",
    });
  }

  // F-18: surface `X-Onboarding-Warning` for ANY endpoint that includes
  // it, not just industry update.
  const warning = res.headers.get("X-Onboarding-Warning");
  if (warning && onWarningHeader) onWarningHeader(warning);

  return { data: dataRaw as T, headers: res.headers };
}

export async function getTenantSettings(
  accessToken?: string,
): Promise<TenantSettingsResponse> {
  const { data } = await request<TenantSettingsResponse>(
    "/api/v1/tenant-settings",
    { method: "GET" },
    accessToken,
  );
  return data;
}

export async function updateIndustry(
  opts: IndustryUpdateOptions,
  accessToken?: string,
): Promise<IndustryUpdateResponse> {
  const { data, headers } = await request<IndustryUpdateResponse>(
    "/api/v1/tenant-settings/onboarding/industry",
    {
      method: "POST",
      body: JSON.stringify({ industry: opts.industry }),
    },
    accessToken,
    opts.onWarningHeader,
  );
  // The header is also surfaced via the callback inside `request`; we
  // keep this no-op assignment so the return shape stays unchanged
  // when the caller did not pass an `onWarningHeader`.
  void headers;
  return data;
}

// ── Story 1.2 — Settings Wizard types + endpoints ────────────
export type OnboardingField =
  | "fiscal_year_start"
  | "currency"
  | "language"
  | "allocation_criteria";

export type AllocationCriterion =
  | "direct_indirect"
  | "fixed_variable"
  | "drivers";

export interface OnboardingFieldSavedResponse {
  field: OnboardingField;
  value: unknown;
  settings_version: number;
  is_complete: boolean;
  missing: string[];
  trace_id: string;
}

export interface CompletionStatus {
  fiscal_year_start_completed: boolean;
  currency_completed: boolean;
  language_completed: boolean;
  allocation_criteria_completed: boolean;
  direct_indirect_count: number;
  fixed_variable_count: number;
  drivers_count: number;
  drivers_required: boolean;
  is_complete: boolean;
  missing: string[];
  trace_id: string;
  fiscal_year_start_value: string | null;
  currency_value: "KRW" | "USD" | null;
  industry: Industry | null;
  last_calc_date: string | null;
}

/** F-18: shared shape for save endpoints — every wizard save can surface
 *  the `X-Onboarding-Warning` header (e.g. A7 lock). */
export interface OnboardingSaveOptions {
  onWarningHeader?: (value: string) => void;
}

async function postOnboardingField<T extends OnboardingFieldSavedResponse>(
  path: string,
  body: unknown,
  accessToken?: string,
  opts?: OnboardingSaveOptions,
): Promise<T> {
  const { data } = await request<T>(
    path,
    { method: "POST", body: JSON.stringify(body) },
    accessToken,
    opts?.onWarningHeader,
  );
  return data;
}

export async function saveFiscalYearStart(
  fiscalYearStart: string,
  accessToken?: string,
  opts?: OnboardingSaveOptions,
): Promise<OnboardingFieldSavedResponse> {
  return postOnboardingField<OnboardingFieldSavedResponse>(
    "/api/v1/tenant-settings/onboarding/fiscal-year-start",
    { fiscal_year_start: fiscalYearStart },
    accessToken,
    opts,
  );
}

export async function saveCurrency(
  currency: "KRW" | "USD",
  accessToken?: string,
  opts?: OnboardingSaveOptions,
): Promise<OnboardingFieldSavedResponse> {
  return postOnboardingField<OnboardingFieldSavedResponse>(
    "/api/v1/tenant-settings/onboarding/currency",
    { currency },
    accessToken,
    opts,
  );
}

export async function saveLanguage(
  language: "ko-KR",
  accessToken?: string,
  opts?: OnboardingSaveOptions,
): Promise<OnboardingFieldSavedResponse> {
  return postOnboardingField<OnboardingFieldSavedResponse>(
    "/api/v1/tenant-settings/onboarding/language",
    { language },
    accessToken,
    opts,
  );
}

export async function saveAllocationCriterion(
  criterion: AllocationCriterion,
  count: number,
  accessToken?: string,
  opts?: OnboardingSaveOptions,
): Promise<OnboardingFieldSavedResponse> {
  return postOnboardingField<OnboardingFieldSavedResponse>(
    "/api/v1/tenant-settings/onboarding/allocation-criteria",
    { criterion, count },
    accessToken,
    opts,
  );
}

export async function fetchCompletionStatus(
  accessToken?: string,
): Promise<CompletionStatus> {
  const { data } = await request<CompletionStatus>(
    "/api/v1/tenant-settings/completion",
    { method: "GET" },
    accessToken,
  );
  return data;
}