// apps/web/mocks/handlers.ts — MSW request handlers
// Story 0.5 — T4.4 (AC #4)
//
// Initial handlers cover Story 1.1 IndustrySelector flow:
//   - GET /api/v1/tenants/me → tenant settings (industry + menu + version)
//   - POST /api/v1/tenants/me/industry → industry update
//
// Story 5.3 — P31 patch — closing-guard endpoints:
//   - GET /api/v1/inventory/closing-guard/evaluate → mock ClosingGuardEvaluateResponse
//   - POST /api/v1/inventory/closing-guard/close-attempt → 200 OK | 409 NEGATIVE_CLOSING_INVENTORY
//   - GET /api/v1/inventory/closing-guard/audit-trail → empty array
//
// Story 9.7 — T3 A35 wire — AbcValidationForm:
//   - POST /api/v1/abc/validate → default 200 ValidationResponse envelope.
//     Tests override via `server.use(http.post(...))` for 422 / 404 envelopes.
//
// Components that need different fixtures should override handlers per-test
// via `server.use(...)` from "mocks/server".

import { http, HttpResponse } from "msw";

const API = "/api/v1/tenants/me";
const API_INDUSTRY = "/api/v1/tenants/me/industry";

// Story 5.3 — closing-guard endpoints
const API_CLOSING_GUARD_EVALUATE = "/api/v1/inventory/closing-guard/evaluate";
const API_CLOSING_GUARD_CLOSE_ATTEMPT =
  "/api/v1/inventory/closing-guard/close-attempt";
const API_CLOSING_GUARD_AUDIT_TRAIL =
  "/api/v1/inventory/closing-guard/audit-trail";

// Story 9.7 — AbcValidationForm
const API_ABC_VALIDATE = "/api/v1/abc/validate";

export const handlers = [
  http.get(API, () => {
    return HttpResponse.json({
      industry: null,
      menu: [],
      settings_version: 1,
      is_initial: true,
      selected_at: null,
    });
  }),

  http.post(API_INDUSTRY, async ({ request }) => {
    const body = (await request.json()) as { industry?: string };
    const industry = body.industry ?? "manufacturing";

    const menuByIndustry: Record<string, string[]> = {
      manufacturing: ["BOM", "기초재고", "수불부"],
      service: ["원가풀", "활동", "동인"],
      manufacturing_service: ["BOM", "기초재고", "수불부", "원가풀", "활동", "동인", "카브아웃 분할"],
      manufacturing_service_other: [
        "BOM", "기초재고", "수불부", "원가풀", "활동", "동인", "카브아웃 분할",
      ],
    };

    return HttpResponse.json({
      industry,
      menu: menuByIndustry[industry] ?? [],
      settings_version: 2,
      is_initial: false,
      selected_at: new Date().toISOString(),
    });
  }),

  // ── Story 5.3 — Closing Guard (P31) ──────────────────────────
  // GET /api/v1/inventory/closing-guard/evaluate
  http.get(API_CLOSING_GUARD_EVALUATE, async ({ request }) => {
    const url = new URL(request.url);
    const periodKey = url.searchParams.get("period_key") ?? "2026-07";
    return HttpResponse.json({
      period_key: periodKey,
      code: "CLOSING_OK",
      closing_per_product: {},
      negative_products: [],
      guard_enabled: true,
      banner_ko: "기말재고 음수: 마감 불가",
      trace_id: "trace-mock-evaluate",
    });
  }),

  // POST /api/v1/inventory/closing-guard/evaluate (api-client uses POST)
  http.post(API_CLOSING_GUARD_EVALUATE, async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as {
      period_key?: string;
    };
    const periodKey = body.period_key ?? "2026-07";
    return HttpResponse.json({
      period_key: periodKey,
      code: "CLOSING_OK",
      closing_per_product: {},
      negative_products: [],
      guard_enabled: true,
      banner_ko: "기말재고 음수: 마감 불가",
      trace_id: "trace-mock-evaluate",
    });
  }),

  // POST /api/v1/inventory/closing-guard/close-attempt
  // Default: 200 OK with CLOSING_OK. Tests can override via server.use()
  // to return 409 NEGATIVE_CLOSING_INVENTORY.
  http.post(API_CLOSING_GUARD_CLOSE_ATTEMPT, async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as {
      period_key?: string;
    };
    const periodKey = body.period_key ?? "2026-07";
    return HttpResponse.json({
      allowed: true,
      period_key: periodKey,
      closing_per_product: {},
      invariant_code: "CLOSING_OK",
      trace_id: "trace-mock-close-attempt",
    });
  }),

  // GET /api/v1/inventory/closing-guard/audit-trail
  http.get(API_CLOSING_GUARD_AUDIT_TRAIL, () => {
    return HttpResponse.json([]);
  }),

  // ── Story 9.7 — AbcValidationForm ──────────────────────────
  // POST /api/v1/abc/validate
  // Default: 200 OK with all_valid=true ValidationResponse (3-layer guard).
  // Tests override via `server.use(http.post(API_ABC_VALIDATE, ...))`
  // for 422 ABC_COST_POOL_INVALID_SUM / 404 ABC_VALIDATION_NOT_FOUND envelopes.
  http.post(API_ABC_VALIDATE, async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as {
      cost_pool_id?: string;
      activity_id?: string;
    };
    const costPoolId = body.cost_pool_id ?? "cp-mock";
    const activityId = body.activity_id ?? "act-mock";
    return HttpResponse.json({
      cost_pool_id: costPoolId,
      activity_id: activityId,
      cost_pool: [
        {
          department_id: "dept-mock-A",
          sum_pct: "100",
          department_count: 1,
          is_valid: true,
          hash: "sha256:" + "0".repeat(64),
        },
      ],
      activities: [
        {
          activity_id: activityId,
          sum_pct: "100",
          product_count: 2,
          is_valid: true,
          hash: "sha256:" + "1".repeat(64),
        },
      ],
      drivers: [
        {
          driver_id: "drv-mock-001",
          sum_pct: "100",
          activity_count: 2,
          is_valid: true,
          hash: "sha256:" + "2".repeat(64),
        },
      ],
      all_valid: true,
      trace_id: "trace-mock-abc-validate",
    });
  }),
];