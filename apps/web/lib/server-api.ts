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
} from "./api-client";
import type {
  MonthlyClosingReportResponse,
  MonthlyClosingReportAuditTrailResponse,
  MonthlyClosingReportV4VerdictResponse,
} from "./monthly-closing-report";

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
