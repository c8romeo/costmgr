// apps/web/mocks/handlers.ts — MSW request handlers
// Story 0.5 — T4.4 (AC #4)
//
// Initial handlers cover Story 1.1 IndustrySelector flow:
//   - GET /api/v1/tenants/me → tenant settings (industry + menu + version)
//   - POST /api/v1/tenants/me/industry → industry update
// Components that need different fixtures should override handlers per-test
// via `server.use(...)` from "mocks/server".

import { http, HttpResponse } from "msw";

const API = "/api/v1/tenants/me";
const API_INDUSTRY = "/api/v1/tenants/me/industry";

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
];
