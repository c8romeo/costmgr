/**
 * apps/web/__tests__/components/m10-ai.AiCommentSection.test.tsx — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * Story 10.3 (AI Reference vs Auto Analysis Badge Separation) test.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { AiCommentSection } from "@/components/m10-ai/AiCommentSection";
import { server } from "@/mocks/server";

beforeEach(() => {
  server.resetHandlers();
});

const sampleComments = [
  {
    comment_id: "c1",
    comment_kind: "cost_reduction_candidate" as const,
    body_text: "auto_analysis 의견",
    source_kind: "auto_analysis" as const,
    evidence_ref: null,
    generated_at: "2026-08-19T00:00:00Z",
  },
  {
    comment_id: "c2",
    comment_kind: "anomaly_pattern" as const,
    body_text: "ai_reference 의견",
    source_kind: "ai_reference" as const,
    evidence_ref: "page 1",
    generated_at: "2026-08-19T00:00:00Z",
  },
];

const defaultCommentsHandler = http.get("/api/v1/ai/comments", () =>
  HttpResponse.json({
    status: "success",
    comments: sampleComments,
    period_key: "2026-07",
    calculation_result_hash: "abc",
    hit_count: 1,
    miss_count: 0,
    counter_total: 42,
  }),
);

describe("AiCommentSection — Sprint 10.5 T3", () => {
  it("mounts with idle state when no initial params", () => {
    render(<AiCommentSection />);
    expect(screen.getByTestId("ai-comment-section")).toBeInTheDocument();
  });

  it("loads and renders comments with correct badge split", async () => {
    server.use(defaultCommentsHandler);
    render(
      <AiCommentSection
        initialPeriodKey="2026-07"
        initialCalculationHash="abc"
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("ai-comment-entries")).toBeInTheDocument();
    });
    const entries = screen.getAllByTestId("ai-comment-entry");
    expect(entries.length).toBe(2);
    expect(entries[0].getAttribute("data-source-kind")).toBe("auto_analysis");
    expect(entries[1].getAttribute("data-source-kind")).toBe("ai_reference");
  });

  it("renders auto_analysis badge (blue) correctly", async () => {
    server.use(
      http.get("/api/v1/ai/comments", () =>
        HttpResponse.json({
          status: "success",
          comments: [sampleComments[0]],
          period_key: "2026-07",
          calculation_result_hash: "abc",
          hit_count: 0,
          miss_count: 0,
          counter_total: 0,
        }),
      ),
    );
    render(
      <AiCommentSection
        initialPeriodKey="2026-07"
        initialCalculationHash="abc"
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("auto-analysis-badge")).toBeInTheDocument();
    });
  });

  it("renders ai_reference badge (purple) correctly", async () => {
    server.use(
      http.get("/api/v1/ai/comments", () =>
        HttpResponse.json({
          status: "success",
          comments: [sampleComments[1]],
          period_key: "2026-07",
          calculation_result_hash: "abc",
          hit_count: 0,
          miss_count: 0,
          counter_total: 0,
        }),
      ),
    );
    render(
      <AiCommentSection
        initialPeriodKey="2026-07"
        initialCalculationHash="abc"
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("ai-reference-badge")).toBeInTheDocument();
    });
  });

  it("shows empty state when 0 comments", async () => {
    server.use(
      http.get("/api/v1/ai/comments", () =>
        HttpResponse.json({
          status: "success",
          comments: [],
          period_key: "2026-07",
          calculation_result_hash: "abc",
          hit_count: 0,
          miss_count: 0,
          counter_total: 0,
        }),
      ),
    );
    render(
      <AiCommentSection
        initialPeriodKey="2026-07"
        initialCalculationHash="abc"
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/표시할 AI 의견이 없습니다/)).toBeInTheDocument();
    });
  });

  it("shows warning banner on unknown source_kind (F10.2-(d))", async () => {
    server.use(
      http.get("/api/v1/ai/comments", () =>
        HttpResponse.json({
          status: "success",
          comments: [
            {
              ...sampleComments[0],
              source_kind: "unknown_source",
            },
          ],
          period_key: "2026-07",
          calculation_result_hash: "abc",
          hit_count: 0,
          miss_count: 0,
          counter_total: 0,
        }),
      ),
    );
    render(
      <AiCommentSection
        initialPeriodKey="2026-07"
        initialCalculationHash="abc"
      />,
    );
    const warning = await screen.findByTestId("ai-comment-warning");
    expect(warning.textContent).toContain("출처가 불분명");
  });

  it("shows error alert on error envelope", async () => {
    server.use(
      http.get("/api/v1/ai/comments", () =>
        HttpResponse.json(
          {
            code: "AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS",
            message_ko: "수정 불가",
            details: {},
            trace_id: "tr-1",
          },
          { status: 422 },
        ),
      ),
    );
    render(
      <AiCommentSection
        initialPeriodKey="2026-07"
        initialCalculationHash="abc"
      />,
    );
    const err = await screen.findByTestId("ai-comment-error");
    expect(err.getAttribute("role")).toBe("alert");
    expect(err.textContent).toContain("AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS");
  });

  it("counter_total propagated via onCounterTotal callback", async () => {
    const onCounterTotal = vi.fn();
    server.use(
      http.get("/api/v1/ai/comments", () =>
        HttpResponse.json({
          status: "success",
          comments: [sampleComments[0]],
          period_key: "2026-07",
          calculation_result_hash: "abc",
          hit_count: 0,
          miss_count: 0,
          counter_total: 7,
        }),
      ),
    );
    render(
      <AiCommentSection
        initialPeriodKey="2026-07"
        initialCalculationHash="abc"
        onCounterTotal={onCounterTotal}
      />,
    );
    await waitFor(() => {
      expect(onCounterTotal).toHaveBeenCalledWith(7);
    });
  });
});
