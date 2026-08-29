/**
 * apps/web/mocks/m10-ai-handlers.ts — Sprint 10.5 T5 wire (A38 AC #5)
 *
 * Shared MSW (Mock Service Worker) handlers for m10-ai 8 endpoints.
 * Used by vitest component tests to fake the backend.
 *
 * 8 endpoints:
 *   - POST /api/v1/ai/extract-monthly
 *   - GET  /api/v1/ai/insights
 *   - GET  /api/v1/ai/comments
 *   - POST /api/v1/ai/promote
 *   (+ 4 GET variants — handled by same path with different status codes
 *    for error envelope testing)
 *
 * AD-7 verbatim: M10 NEVER writes confirmed_inputs. The promote handler
 * is the canonical path for AD-7 strict invariant.
 */

import { http, HttpResponse } from "msw";

import type { AICommentListResponse } from "@/lib/ai-comments";
import type { MonthlyExtractResponseSuccess } from "@/lib/ai-extract";
import type { PromoteResponseSuccess } from "@/lib/ai-promote";
import type { InsightListResponse } from "@/lib/insight-cache";

// Local re-alias for backwards compat with T5 mock callers
type PromoteResponse = PromoteResponseSuccess;

const extractMonthlyMockBody = (): MonthlyExtractResponseSuccess => ({
  status: "success",
  extraction_id: "00000000-0000-0000-0000-000000000001",
  period_key: "2026-07",
  drafts: [
    {
      field_name: "직접재료비",
      value: "1000000",
      confidence: "0.92",
      target_table: "monthly_inputs",
      evidence_page: 1,
      requires_user_confirmation: false,
    },
    {
      field_name: "기말재고",
      value: "500000",
      confidence: "0.55",
      target_table: "monthly_inputs",
      evidence_page: 3,
      requires_user_confirmation: true,
    },
  ],
  low_confidence_count: 1,
});

const insightsMockBody = (periodKey: string): InsightListResponse => ({
  status: "success",
  insights: [
    {
      insight_kind: "cost_reduction_candidate",
      question: "비용 절감 후보가 있나요?",
      answer: "제조간접비 12% 절감 가능 — 외주 검증 권장",
      source_kind: "auto_analysis",
      evidence_ref: "page 1",
      generated_at: "2026-08-19T00:00:00Z",
    },
    {
      insight_kind: "anomaly_pattern",
      question: "이상 패턴이 있나요?",
      answer: "7월 제조간접비 표준편차 3σ 초과",
      source_kind: "auto_analysis",
      evidence_ref: null,
      generated_at: "2026-08-19T00:00:00Z",
    },
    {
      insight_kind: "forecast",
      question: "8월 예측은?",
      answer: "제조간접비 +5% 예상 (P95 ±2%)",
      source_kind: "auto_analysis",
      evidence_ref: null,
      generated_at: "2026-08-19T00:00:00Z",
    },
  ],
  period_key: periodKey,
  calculation_result_hash: "abc123def456",
  hit_count: 1,
  miss_count: 0,
});

const commentsMockBody = (periodKey: string): AICommentListResponse => ({
  status: "success",
  comments: [
    {
      comment_id: "00000000-0000-0000-0000-000000000001",
      comment_kind: "cost_reduction_candidate",
      body_text: "외주 검증으로 제조간접비 12% 절감 가능",
      source_kind: "auto_analysis",
      evidence_ref: null,
      generated_at: "2026-08-19T00:00:00Z",
    },
    {
      comment_id: "00000000-0000-0000-0000-000000000002",
      comment_kind: "anomaly_pattern",
      body_text: "7월 표준편차 3σ 초과 — 추가 검증 권장",
      source_kind: "ai_reference",
      evidence_ref: "page 2",
      generated_at: "2026-08-19T00:00:00Z",
    },
  ],
  period_key: periodKey,
  calculation_result_hash: "abc123def456",
  hit_count: 1,
  miss_count: 0,
  counter_total: 7,
});

const promoteMockBody = (
  sourceDraftId: string,
): PromoteResponseSuccess => ({
  status: "success",
  tenant_id: "11111111-1111-1111-1111-111111111111",
  period_key: "2026-07",
  source_draft_id: sourceDraftId,
  promotion_id: "22222222-2222-2222-2222-222222222222",
  idempotency_key: "33333333-3333-3333-3333-333333333333",
  confirmed_input_row_id: "44444444-4444-4444-4444-444444444444",
  promoted_at: "2026-08-19T00:00:00Z",
  draft_hash: "deadbeef",
  idempotent_replay: false,
  audit_log_ids: ["55555555-5555-5555-5555-555555555555", "66666666-6666-6666-6666-666666666666"],
});

export const m10AiHandlers = [
  http.post("/api/v1/ai/extract-monthly", () => {
    return HttpResponse.json(extractMonthlyMockBody());
  }),
  http.get("/api/v1/ai/insights", ({ request }) => {
    const url = new URL(request.url);
    const periodKey = url.searchParams.get("period_key") ?? "2026-07";
    return HttpResponse.json(insightsMockBody(periodKey));
  }),
  http.get("/api/v1/ai/comments", ({ request }) => {
    const url = new URL(request.url);
    const periodKey = url.searchParams.get("period_key") ?? "2026-07";
    return HttpResponse.json(commentsMockBody(periodKey));
  }),
  http.post("/api/v1/ai/promote", async ({ request }) => {
    const body = (await request.json()) as {
      source_draft_id?: string;
    };
    return HttpResponse.json(promoteMockBody(body.source_draft_id ?? "draft-1"));
  }),
];

// Error variant factories (used by selective tests)
export const m10AiErrorHandlers = {
  pipaConsentMissing: () =>
    new HttpResponse(
      JSON.stringify({
        status: "error",
        error_code: "AI_PIPA_CONSENT_MISSING",
        message_ko: "개인정보 처리 동의가 필요합니다",
        trace_id: "test-tr-1",
      }),
      { status: 403, headers: { "content-type": "application/json" } },
    ),
  m2Only: () =>
    new HttpResponse(
      JSON.stringify({
        status: "m2_only",
        code: "INPUT_PROMOTION_M2_ONLY",
        message_ko: "M2만 가능",
        details: {},
        trace_id: "test-tr-2",
      }),
      { status: 403, headers: { "content-type": "application/json" } },
    ),
  draftImmutable: () =>
    new HttpResponse(
      JSON.stringify({
        status: "draft_immutable",
        code: "PROMOTE_DRAFT_IMMUTABLE",
        message_ko: "이미 승격됨",
        details: {},
        trace_id: "test-tr-3",
      }),
      { status: 409, headers: { "content-type": "application/json" } },
    ),
};
