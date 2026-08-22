/**
 * apps/web/lib/server-api.ts — server-only API fetcher.
 *
 * F-20: used by Server Components to make race-free initial fetches.
 * Server Components cannot use relative URLs (they run in a different
 * runtime than Client Components), so this module wraps `fetch` with an
 * absolute base URL derived from `COSTMGR_API_URL` (or the localhost
 * fallback used during local development).
 *
 * Every fetch returns `null` on failure — the calling RSC should treat
 * `null` as "initial data unavailable" and pass that through to the
 * Client Component so it can fall back to polling/refetching. We
 * intentionally do NOT throw from server-side initial fetches to keep
 * the user-facing error budget intact (errors surface downstream).
 */

import "server-only";

import type {
  BOMResponse,
  CompletionStatus,
  MonthlyInputStateResponse,
  ProductListResponse,
  TenantSettingsResponse,
} from "./api-client";
import type { IdPConfig } from "./auth/admin-idp-client";
import type {
  MonthlyClosingReportResponse,
  MonthlyClosingReportAuditTrailResponse,
  MonthlyClosingReportV4VerdictResponse,
} from "./monthly-closing-report";
import type { BackupListResponse } from "./m12-account-backup";
import type {
  ActivityStreamGroup,
  AuditLogPage,
  AuditLogQueryFilters,
} from "./audit/audit-log-client";

const DEFAULT_API_BASE_URL = "http://localhost:8765";

// M6b: server-side fetches get a 5s timeout. RSC fetches block the
// streaming render — a wedged backend must not stall the page
// indefinitely. On timeout we return null (the existing "initial data
// unavailable" path) so the Client Component's polling kicks in.
const SERVER_FETCH_TIMEOUT_MS = 5_000;

function apiBaseUrl(): string {
  return process.env.COSTMGR_API_URL ?? DEFAULT_API_BASE_URL;
}

export async function fetchCompletionServerSide(
  accessToken: string | undefined,
  traceId: string,
): Promise<CompletionStatus | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  try {
    const controller = new AbortController();
    const timer = setTimeout(
      () =>
        controller.abort(
          new DOMException("Server fetch timeout", "TimeoutError"),
        ),
      SERVER_FETCH_TIMEOUT_MS,
    );
    let res: Response;
    try {
      res = await fetch(`${apiBaseUrl()}/api/v1/tenant-settings/completion`, {
        method: "GET",
        headers,
        cache: "no-store",
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }
    if (!res.ok) return null;
    const data = (await res.json()) as CompletionStatus;
    return data;
  } catch {
    // Network / decode / timeout errors are non-fatal at RSC render time
    // — let the Client Component's polling take over.
    return null;
  }
}

// ── Story 2.1 — Product list server-side initial fetch ───────
//
// Mirrors fetchCompletionServerSide: returns null on failure, never
// throws. The calling RSC threads that into the Client Component as
// the seed value for its hook.
export async function fetchProductsServerSide(
  accessToken: string | undefined,
  traceId: string,
  query?: { product_type?: string; is_active?: boolean; limit?: number; offset?: number },
): Promise<ProductListResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const params = new URLSearchParams();
  if (query?.product_type) params.set("product_type", query.product_type);
  if (typeof query?.is_active === "boolean") {
    params.set("is_active", String(query.is_active));
  }
  if (query?.limit != null) params.set("limit", String(query.limit));
  if (query?.offset != null) params.set("offset", String(query.offset));
  const qs = params.toString();
  const path = `/api/v1/baseline/products${qs ? `?${qs}` : ""}`;

  try {
    const res = await fetch(`${apiBaseUrl()}${path}`, {
      method: "GET",
      headers,
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data = (await res.json()) as ProductListResponse;
    return data;
  } catch {
    return null;
  }
}

// ── Story 2.2 — BOM server-side initial fetch ─────────────────
//
// Mirrors fetchProductsServerSide. Returns null on any failure so the
// RSC page can pass the seed through to BOMEditorClient without
// breaking the render path.
export async function fetchBomServerSide(
  productId: string,
  accessToken: string | undefined,
  traceId: string,
): Promise<BOMResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/baseline/products/${productId}/bom`,
      {
        method: "GET",
        headers,
        cache: "no-store",
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as BOMResponse;
    return data;
  } catch {
    return null;
  }
}

/**
 * fetchMonthlyInputStateServerSide — Story 5.3 T15.1 (page.tsx wire).
 *
 * RSC fetch for `GET /api/v2/monthly-input/{period_key}/state` to seed
 * the [월 입력] page with 5-3 NEW closing-guard fields (closing_guard_blocked,
 * closing_guard_audit_trail, production_consumption_events, v3_verdict,
 * closing_guard_invariant). Returns null on failure so the Client Component
 * can fall back to polling (existing pattern from F-20).
 *
 * P3-3rd-sweep P22: AbortSignal timeout (5s) prevents RSC render hang on
 * backend stall. P23: encodeURIComponent(periodKey) for safe path interpolation.
 */
export async function fetchMonthlyInputStateServerSide(
  periodKey: string,
  accessToken: string | undefined,
  traceId: string,
): Promise<MonthlyInputStateResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  // P3-3rd-sweep P22: 5s AbortController timeout prevents indefinite RSC stall.
  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v2/monthly-input/${encodeURIComponent(periodKey)}/state`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as MonthlyInputStateResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * fetchM2EntryGateServerSide — Story 12.4 review P-02.
 *
 * RSC fetch for `GET /api/v1/m2-entry-gate` to seed the TwoFactorGuard
 * component with actual session-derived props (role, totp_enabled,
 * locked_out, lockout_until). Replaces the placeholder hardcoded values
 * that were broken per CR 11-4 D-001 lesson.
 *
 * Fail-closed: when fetch fails or token missing, returns null which the
 * page treats as `role="viewer"` (no M2 entry). Returns null on failure
 * so the page can fail closed (gate denies M2 entry).
 */
export interface M2EntryGateServerSideResponse {
  role: string;
  totp_enabled: boolean;
  locked_out: boolean;
  lockout_until: string | null;
}

export async function fetchM2EntryGateServerSide(
  accessToken: string | undefined,
  traceId: string,
): Promise<M2EntryGateServerSideResponse | null> {
  if (!accessToken) {
    // No session → viewer (no M2 entry)
    return {
      role: "viewer",
      totp_enabled: false,
      locked_out: false,
      lockout_until: null,
    };
  }
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(`${apiBaseUrl()}/api/v1/m2-entry-gate`, {
      method: "GET",
      headers,
      cache: "no-store",
      signal: abortCtl.signal,
    });
    if (!res.ok) return null;
    const data = (await res.json()) as {
      role?: string;
      totp_enabled?: boolean;
      locked_out?: boolean;
      lockout_until?: string | null;
    };
    return {
      role: data.role ?? "viewer",
      totp_enabled: data.totp_enabled ?? false,
      locked_out: data.locked_out ?? false,
      lockout_until: data.lockout_until ?? null,
    };
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * fetchTotpStatusServerSide — Story 12.5 (AC #4 RSC page wire).
 *
 * RSC fetch for `GET /api/v1/account/2fa/status` to seed the
 * /account/security page with the user's current TOTP enrollment
 * state. Returns null on failure so the page can fail closed (the
 * status badge defaults to "disabled" + setup CTA).
 */
export interface TotpStatusServerSideResponse {
  totp_enabled: boolean;
  totp_enabled_at: string | null;
  recovery_codes_remaining: number | null;
  failed_attempts: number;
  locked_out: boolean;
  lockout_until: string | null;
  last_login_at: string | null;
  role: string;
}

export async function fetchTotpStatusServerSide(
  accessToken: string | undefined,
  traceId: string,
): Promise<TotpStatusServerSideResponse | null> {
  if (!accessToken) {
    return null;
  }
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${accessToken}`);
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(`${apiBaseUrl()}/api/v1/account/2fa/status`, {
      method: "GET",
      headers,
      cache: "no-store",
      signal: abortCtl.signal,
    });
    if (!res.ok) return null;
    const data = (await res.json()) as {
      totp_enabled?: boolean;
      totp_enabled_at?: string | null;
      recovery_codes_remaining?: number | null;
      failed_attempts?: number;
      locked_out?: boolean;
      lockout_until?: string | null;
      role?: string;
    };
    return {
      totp_enabled: data.totp_enabled ?? false,
      totp_enabled_at: data.totp_enabled_at ?? null,
      recovery_codes_remaining: data.recovery_codes_remaining ?? null,
      failed_attempts: data.failed_attempts ?? 0,
      locked_out: data.locked_out ?? false,
      lockout_until: data.lockout_until ?? null,
      last_login_at: data.totp_enabled_at ?? null,
      role: data.role ?? "viewer",
    };
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Story 6.2 — Monthly closing report server-side fetcher ──────
//
// RSC fetch for `GET /api/v1/inventory/monthly-closing-report?period_key=...`
// to seed the [월 마감 보고서] page with the 4-source read-only aggregate.
// Returns null on failure so the Client Component can fall back to polling.
export async function fetchMonthlyClosingReportServerSide(
  periodKey: string,
  accessToken: string | undefined,
  traceId: string,
): Promise<MonthlyClosingReportResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/inventory/monthly-closing-report?period_key=${encodeURIComponent(periodKey)}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as MonthlyClosingReportResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Story 6.2 — Monthly closing report audit trail fetcher ─────
export async function fetchMonthlyClosingReportAuditTrailServerSide(
  periodKey: string,
  accessToken: string | undefined,
  traceId: string,
): Promise<MonthlyClosingReportAuditTrailResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/inventory/monthly-closing-report/audit-trail?period_key=${encodeURIComponent(periodKey)}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as MonthlyClosingReportAuditTrailResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Story 6.2 — V4 verdict fetcher ──────────────────────────────
export async function fetchMonthlyClosingReportV4VerdictServerSide(
  periodKey: string,
  accessToken: string | undefined,
  traceId: string,
): Promise<MonthlyClosingReportV4VerdictResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/inventory/monthly-closing-report/v4-verdict?period_key=${encodeURIComponent(periodKey)}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as MonthlyClosingReportV4VerdictResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Story 6.3 — Tenant settings fetcher (for W5 industry guard) ──
//
// RSC fetch for `GET /api/v1/tenant-settings` to seed the
// monthly-closing-report page with the tenant's industry code (W5 deferral
// guard for PDF export — must be one of 4 canonical industries).
export async function fetchTenantSettingsServerSide(
  accessToken: string | undefined,
  traceId: string,
): Promise<TenantSettingsResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(`${apiBaseUrl()}/api/v1/tenant-settings`, {
      method: "GET",
      headers,
      cache: "no-store",
      signal: abortCtl.signal,
    });
    if (!res.ok) return null;
    const data = (await res.json()) as TenantSettingsResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Story 12.2 — Backup list fetcher (RSC for /account/backups) ──
//
// RSC fetch for `GET /api/v1/account/backups/recent` to seed the
// BackupDownloadPanel with the initial list of recent backups. Returns
// null on any failure so the page falls back to the empty-state UI
// (client component will retry via its own refresh button).
export async function fetchBackupsRecentServerSide(
  accessToken: string | undefined,
  traceId: string,
  days: number = 7,
): Promise<BackupListResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/account/backups/recent?days=${days}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as BackupListResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Story 12.3 — Deletion status fetcher (RSC for /account/settings) ──
//
// RSC fetch for `GET /api/v1/account/deletion/status` to seed the
// DeletionStatusPanel with the initial FSM snapshot. Returns null on
// any failure (network / auth / 410 deleted) so the panel can render
// the terminal "deleted" state.
//
// Note: 410 Gone is a "successful" terminal state for deletion — the
// panel shows "삭제 완료" when initial is null AND the tenant has been
// hard-deleted. We DO NOT differentiate 410 from network errors here
// (the panel's client-side refresh handles 410 explicitly).
import type { DeletionStatusResponse } from "./m12-account-deletion";

export async function fetchDeletionStatusServerSide(
  accessToken: string | undefined,
): Promise<DeletionStatusResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/account/deletion/status`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as DeletionStatusResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Story 8.1 — Budget scenario server-side fetcher ─────────────
//
// RSC fetch for `GET /api/v1/budget/scenarios` to seed the
// /budget/scenarios page with the tenant's current scenarios.
// Returns null on failure so the Client Component can fall back to polling.
import type { BudgetScenarioListResponse } from "./m8-budget-scenario";

export async function fetchBudgetScenariosServerSide(
  accessToken: string | undefined,
  traceId: string,
): Promise<BudgetScenarioListResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(`${apiBaseUrl()}/api/v1/budget/scenarios`, {
      method: "GET",
      headers,
      cache: "no-store",
      signal: abortCtl.signal,
    });
    if (!res.ok) return null;
    const data = (await res.json()) as BudgetScenarioListResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}


// Story 8.2 (Epic 8) — M8 budget-actual variance server-side fetch
// (PRD §F8.2 + AD-15 SSOT parity with apps/api/modules/m8_budget/handlers.py).
// Returns null on failure so the Client Component can fall back to polling.
import type { VarianceTableResponse } from "./m8-budget-variance";

export async function fetchBudgetVarianceServerSide(
  accessToken: string | undefined,
  periodKey: string,
  traceId: string,
): Promise<VarianceTableResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/budget/variance/${encodeURIComponent(periodKey)}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as VarianceTableResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Story 8.2 — M8 budget-actual variance PDF envelope fetch (8-3 honestly DEFER).
// 8-2 atomic wire: returns envelope shape with empty pdf_bytes_b64 (placeholder).
export async function fetchBudgetVariancePdfServerSide(
  accessToken: string | undefined,
  periodKey: string,
  traceId: string,
): Promise<unknown | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/budget/variance/${encodeURIComponent(periodKey)}/pdf`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as unknown;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Story 8.3 (Epic 8) — M8 budget pre-standard cost preview server-side fetch.
// RSC fetch for `GET /api/v1/budget/pre-standard?period_key=...` to seed
// the /budget/pre-standard page with the tenant's existing pre-standard
// snapshot (PRD §F8.3 + AD-15 SSOT parity with
// apps/api/modules/m8_budget/handlers.py::get_budget_pre_standard).
//
// 404 (no snapshot yet) → returns null. Returns null on any failure so the
// page falls back to "no snapshot yet" rendering.
import type { BudgetPreStandardResponse } from "./m8-budget-pre-standard";

export async function fetchBudgetPreStandardServerSide(
  accessToken: string | undefined,
  periodKey: string,
  traceId: string,
): Promise<BudgetPreStandardResponse | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/budget/pre-standard?period_key=${encodeURIComponent(periodKey)}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (res.status === 404) return null;
    if (!res.ok) return null;
    const data = (await res.json()) as BudgetPreStandardResponse;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Epic 16 T4 (AC #7.1) — Tenant IdP admin list server-side fetch.
// RSC fetch for `GET /api/v1/admin/tenant/{slug}/idp` to seed the
// /settings/sso page with the tenant's current IdP config list (PRD
// §F19.4 + AD-30 (d)). Mirrors `apps/api/modules/auth/sso/idp_admin_routes.py`
// `list_tenant_idp` route. TS mirror parity mandatory (CR 11-4 D-004).
//
// 403 (no TENANT_IDP_MANAGEMENT capability or wrong role) → returns
// null. The page Client Component surfaces a typed error envelope.
// Returns null on any failure so the page falls back to its empty
// state rendering.
export async function fetchIdPConfigServerSide(
  accessToken: string | undefined,
  tenantSlug: string,
  traceId: string,
): Promise<IdPConfig[] | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/admin/tenant/${encodeURIComponent(tenantSlug)}/idp`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (res.status === 404) return null;
    if (!res.ok) return null;
    const data = (await res.json()) as IdPConfig[];
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Epic 17 T2 (AC #2.1) — Audit Log Viewer initial server-side fetch.
// RSC fetch for `GET /api/v1/audit-log` to seed the /audit-log page
// with the first page of audit entries (PRD §F21.2 + AD-32 (b)).
// Mirrors `apps/api/modules/audit/audit_log_routes.py`
// `list_audit_log` route (capability gate AUDIT_LOG_VIEW, owner/admin
// only). TS mirror parity mandatory (CR 11-4 D-004).
//
// Per F-20 race-free pattern: races inside this fetch are unlikely
// (no parallel inputs), but the 5s AbortController prevents a wedged
// backend from stalling the initial render — on timeout / error we
// return null and let the Client Component's `useEffect` mount fetch
// surface a typed CR 12-5 D-14 envelope to the user.
//
// All filters are sent as query params. RLS auto-isolation is enforced
// at the backend (CR 0-2 verbatim) — the cookie Bearer token is
// forwarded verbatim and the route handlers attach the tenant context
// automatically.
export async function fetchAuditLogServerSide(
  accessToken: string | undefined,
  filters: AuditLogQueryFilters,
  page: number,
  pageSize: number,
  traceId: string,
): Promise<AuditLogPage | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const qs = new URLSearchParams();
  qs.set("page", String(page));
  qs.set("page_size", String(pageSize));
  if (filters.actor_id) qs.set("actor_id", filters.actor_id);
  if (filters.action) qs.set("action", filters.action);
  if (filters.action_class) qs.set("action_class", filters.action_class);
  if (filters.resource_type) qs.set("resource_type", filters.resource_type);
  if (filters.resource_id) qs.set("resource_id", filters.resource_id);
  if (filters.start_date) qs.set("start_date", filters.start_date);
  if (filters.end_date) qs.set("end_date", filters.end_date);
  if (filters.trace_id) qs.set("trace_id", filters.trace_id);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(`${apiBaseUrl()}/api/v1/audit-log?${qs.toString()}`, {
      method: "GET",
      headers,
      cache: "no-store",
      signal: abortCtl.signal,
    });
    if (res.status === 404) return null;
    if (!res.ok) return null;
    const data = (await res.json()) as AuditLogPage;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Epic 17 T3 (AC #3.1) — Activity Stream initial server-side fetch.
// RSC fetch for `GET /api/v1/activity?window_days=...` to seed the
// /activity page with the first activity groups (PRD §F21.3 + AD-32
// (c)). Mirrors `apps/api/modules/audit/audit_log_routes.py`
// `get_activity_stream` route (no capability gate; all tenant
// members can view activity). TS mirror parity mandatory (CR 11-4
// D-004).
//
// windowDays is a typed literal (1 | 7 | 30 | 90) — the page-level
// ALLOWED_WINDOWS guard already filters invalid values, but we
// forward the request as-is and let the backend reject malformed
// ranges (returning null → empty timeline in the Client Component).
export async function fetchActivityStreamServerSide(
  accessToken: string | undefined,
  windowDays: 1 | 7 | 30 | 90,
  traceId: string,
): Promise<ActivityStreamGroup[] | null> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("X-Trace-Id", traceId);

  const abortCtl = new AbortController();
  const timeoutId = setTimeout(() => abortCtl.abort(), 5000);

  try {
    const res = await fetch(
      `${apiBaseUrl()}/api/v1/activity?window_days=${windowDays}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
        signal: abortCtl.signal,
      },
    );
    if (res.status === 404) return null;
    if (!res.ok) return null;
    const data = (await res.json()) as ActivityStreamGroup[];
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}
