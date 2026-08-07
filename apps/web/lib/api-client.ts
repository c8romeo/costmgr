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

/* eslint-disable @typescript-eslint/no-restricted-types --
 * AD-8 deferred: this file uses `number` for `status` (HTTP code),
 * `settings_version` (monotonic counter), `*_count` (counts), and
 * other non-money fields. AD-8 forbids `number` only on money paths.
 * A per-call-site rule (no-restricted-syntax identifier-aware) is
 * deferred to Story 0.5+ per the 0.4 review. Until then, file-level
 * disable is the pragmatic realization.
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

// ── Story 2.1 / Story 2.3 — Product / Item Master ─────────────
//
// Wire shape mirrors `apps/api/modules/m1_baseline/schemas.py`:
// - ProductType (5 values: product | semi_product | material | goods | service)
// - KRW / USD as TS string (decimal.js for USD; bigint for KRW).
//
// `unit_cost_krw` arrives as a JSON string (the API serializes BIGINT to
// decimal-safe string per AD-15). The list/response layer leaves it as
// string so the formatters in `lib/money.ts` can decode + display.
//
// Story 2.3 (PRD §6.1 — item type change integrity guard):
//   - PATCH `product_type` is CONDITIONAL: allowed iff BOM + ledger
//     references = 0. Otherwise the API returns
//     409 PRODUCT_TYPE_HAS_REFERENCES. `code` remains strictly immutable.
//   - `product_type` is now part of the PATCH body shape (was previously
//     not editable from the client — `code` is still NOT in the request).
//   - 409 envelope `details` carry `bom_count` + `ledger_count` +
//     `total_count` so the matrix UI can guide the user.

export type ProductType =
  | "product"
  | "semi_product"
  | "material"
  | "goods"
  | "service";

export interface ProductResponse {
  id: string;
  tenant_id: string;
  product_type: ProductType;
  code: string;
  name: string;
  unit: string | null;
  unit_cost_krw: string | null;
  unit_cost_usd: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  items: ProductResponse[];
  total: number;
}

export interface ProductCreateRequest {
  product_type: ProductType;
  name: string;
  code?: string | null;
  unit?: string | null;
  unit_cost_krw?: string | null;
  unit_cost_usd?: string | null;
  description?: string | null;
}

export interface ProductUpdateRequest {
  name?: string;
  unit?: string | null;
  unit_cost_krw?: string | null;
  unit_cost_usd?: string | null;
  description?: string | null;
  is_active?: boolean;
  /** Story 2.3 — type change is conditional (refs == 0). Server returns
   *  409 PRODUCT_TYPE_HAS_REFERENCES when BOM/ledger refs > 0.
   *  P5 (post-review): server-side schema treats explicit `null` as
   *  INVALID_PRODUCT_TYPE (422). Omit the field to leave unchanged.
   *  AD-18: identifier is intentionally absent from this shape. */
  product_type?: ProductType;
}

export interface ProductListQuery {
  product_type?: ProductType;
  /** `null` (omitted) means "no filter applied". Pass `true` / `false`
   *  explicitly to scope. */
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

function buildProductListQuery(query: ProductListQuery | undefined): string {
  if (!query) return "";
  const params = new URLSearchParams();
  if (query.product_type) params.set("product_type", query.product_type);
  if (typeof query.is_active === "boolean") {
    params.set("is_active", String(query.is_active));
  }
  if (query.limit != null) params.set("limit", String(query.limit));
  if (query.offset != null) params.set("offset", String(query.offset));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function fetchProducts(
  query?: ProductListQuery,
  accessToken?: string,
): Promise<ProductListResponse> {
  const qs = buildProductListQuery(query);
  const { data } = await request<ProductListResponse>(
    `/api/v1/baseline/products${qs}`,
    { method: "GET" },
    accessToken,
  );
  return data;
}

export async function getProduct(
  id: string,
  accessToken?: string,
): Promise<ProductResponse> {
  const { data } = await request<ProductResponse>(
    `/api/v1/baseline/products/${id}`,
    { method: "GET" },
    accessToken,
  );
  return data;
}

export async function createProduct(
  body: ProductCreateRequest,
  accessToken?: string,
): Promise<ProductResponse> {
  const { data } = await request<ProductResponse>(
    "/api/v1/baseline/products",
    { method: "POST", body: JSON.stringify(body) },
    accessToken,
  );
  return data;
}

export async function updateProduct(
  id: string,
  body: ProductUpdateRequest,
  accessToken?: string,
): Promise<ProductResponse> {
  const { data } = await request<ProductResponse>(
    `/api/v1/baseline/products/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    accessToken,
  );
  return data;
}

// ── Story 2.2 — BOM Matrix (PRD §8.M1(b)) ──────────────────────
//
// Wire shape mirrors `apps/api/modules/m1_baseline/schemas.py`:
// - BOMRowInput: child_product_id + ratio (Decimal as string per AD-15)
// - BOMSetRequest: lines: BOMRowInput[] (max 500, bulk-replace)
// - BOMResponse: parent metadata + lines + derived total_ratio / is_complete
//
// `ratio` is delivered as a JSON string (Pydantic serializes Decimal to
// string). The matrix UI parses it via `decimal.js` for arithmetic.

export interface BOMRowInput {
  child_product_id: string;
  /** Ratio (%). NUMERIC(7,4). Wire format: string. */
  ratio: string;
}

export interface BOMSetRequest {
  lines: BOMRowInput[];
}

export interface BOMLineResponse {
  id: string;
  child_product_id: string;
  child_code: string;
  child_name: string;
  child_product_type: ProductType;
  child_is_active: boolean;
  /** Ratio (%). Wire format: string. */
  ratio: string;
  created_at: string;
  updated_at: string;
}

export interface BOMResponse {
  parent_product_id: string;
  parent_code: string;
  parent_name: string;
  parent_product_type: ProductType;
  parent_is_active: boolean;
  lines: BOMLineResponse[];
  total_ratio: string;
  is_complete: boolean;
  missing_ratio: string;
  updated_at: string | null;
}

// ── Story 5.3 — MonthlyInputStateResponse extension ────────────
//
// Mirrors backend `apps/api/modules/m2_input/services/monthly_input_service.py
// MonthlyInputStateResponse` (5-3 wire spec). 5 NEW closing-guard fields
// projected to page-level state hook:
//
// - closing_guard_blocked          — drives [마감] button disabled gate.
// - closing_guard_audit_trail      — drives [마감 검증 이력] tab render.
// - production_consumption_events  — BOM-aware ledger event preview for [수불부] tab.
// - v3_verdict                     — V3 closing invariant verification status.
// - closing_guard_invariant        — typed ClosingInvariant (code + message_ko + closing_per_product).

export type ClosingInvariantCode =
  | "CLOSING_OK"
  | "NEGATIVE_CLOSING"
  | "EMPTY_PERIOD"
  // P3-3rd-sweep P32: service-only tenant skip path represented as distinct code.
  | "SERVICE_ONLY_TENANT_SKIPPED";

export interface ClosingInvariant {
  code: ClosingInvariantCode;
  negative_products: Record<string, string>;
  closing_per_product: Record<string, string>;
  guard_enabled: boolean;
}

export interface ClosingGuardAuditEntry {
  id: string;
  tenant_id: string;
  period_key: string;
  action: string;
  trace_id: string;
  created_at: string;
  payload: Record<string, unknown>;
}

export interface V3Failure {
  product_id: string;
  closing_qty: string;
  message_ko: string;
}

export interface V3Verdict {
  status: "passed" | "failed" | "skipped";
  code: "V3";
  failures: V3Failure[];
  verified_at: string;
  product_whitelist_size: number;
  skip_reason_ko: string | null;
}

export interface ProductionConsumptionEventWire {
  product_id: string;
  period_key: string;
  event_type: "production_output_inbound" | "production_material_consumption";
  qty: string;
  trace_id: string;
}

export interface MonthlyInputStateResponse {
  period_key: string;
  rows: Array<Record<string, unknown>>;
  completion: CompletionStatus;
  is_complete: boolean;
  missing: string[];
  capability_mask: Record<string, boolean>;
  fte_display: Record<string, number>;
  // 5-1 fields
  opening_inventory: Record<string, string>;
  opening_inventory_locked: boolean;
  opening_inventory_lock_reason_ko: string | null;
  // 5-2 ledger fields
  ledger_events_count: number;
  ledger_period_closing: Record<string, string>;
  inventory_ledger_enabled: boolean;
  reversal_request_enabled: boolean;
  // 5-3 NEW closing-guard fields (T6.4 wire spec)
  closing_guard_blocked: boolean;
  closing_guard_audit_trail: ClosingGuardAuditEntry[];
  production_consumption_events: ProductionConsumptionEventWire[];
  v3_verdict: V3Verdict | null;
  // P3-3rd-sweep P29: closing_guard_invariant nullable to mirror service-only
  // tenant skip path (industry='service' → invariant=null). Page falls back
  // to CLOSING_OK + guard_enabled=false (fail-closed) when null.
  closing_guard_invariant: ClosingInvariant | null;
}

export async function fetchBom(
  productId: string,
  accessToken?: string,
): Promise<BOMResponse> {
  const { data } = await request<BOMResponse>(
    `/api/v1/baseline/products/${productId}/bom`,
    { method: "GET" },
    accessToken,
  );
  return data;
}

export async function setBom(
  productId: string,
  body: BOMSetRequest,
  accessToken?: string,
): Promise<BOMResponse> {
  const { data } = await request<BOMResponse>(
    `/api/v1/baseline/products/${productId}/bom`,
    { method: "PUT", body: JSON.stringify(body) },
    accessToken,
  );
  return data;
}

export async function clearBom(
  productId: string,
  accessToken?: string,
): Promise<void> {
  await request<null>(
    `/api/v1/baseline/products/${productId}/bom`,
    { method: "DELETE" },
    accessToken,
  );
}

// ── Story 5.3 — Closing guard API methods (AC #2 + AC #4 + AC #5) ─

/**
 * POST /api/v1/inventory/closing-guard/evaluate
 * Read-only closing ≥ 0 invariant check.
 * Returns `ClosingGuardEvaluateResponse` (banner + negative products).
 */
export async function evaluateClosingGuard(
  periodKey: string,
  accessToken?: string,
): Promise<import("./closing-guard").ClosingGuardEvaluateResponse> {
  const { data } = await request<
    import("./closing-guard").ClosingGuardEvaluateResponse
  >(
    "/api/v1/inventory/closing-guard/evaluate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ period_key: periodKey }),
    },
    accessToken,
  );
  return data;
}

/**
 * POST /api/v1/inventory/closing-guard/close-attempt
 * Close-time gate wire. On 200 → invariant.code = CLOSING_OK or EMPTY_PERIOD.
 * On 409 → throws ApiError with code='NEGATIVE_CLOSING_INVENTORY'.
 */
export async function requestClosingGuardAttempt(
  periodKey: string,
  accessToken?: string,
): Promise<import("./closing-guard").ClosingGuardCloseAttemptResponse> {
  const { data } = await request<
    import("./closing-guard").ClosingGuardCloseAttemptResponse
  >(
    "/api/v1/inventory/closing-guard/close-attempt",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ period_key: periodKey }),
    },
    accessToken,
  );
  return data;
}
