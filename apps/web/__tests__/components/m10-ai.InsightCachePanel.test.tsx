/**
 * apps/web/__tests__/components/m10-ai.InsightCachePanel.test.tsx — Sprint 10.5 T2 wire (D-10-2-DEFER-4 해소)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, beforeEach } from "vitest";

import { InsightCachePanel } from "@/components/m10-ai/InsightCachePanel";
import { server } from "@/mocks/server";

beforeEach(() => {
  server.resetHandlers();
});

describe("InsightCachePanel — Sprint 10.5 T2", () => {
  it("mounts with idle state when no initial keys", () => {
    render(<InsightCachePanel />);
    expect(screen.getByTestId("insight-cache-panel")).toBeInTheDocument();
    expect(screen.getByTestId("insight-idle")).toBeInTheDocument();
  });

  it("auto-loads when initialPeriodKey + initialCalculationHash provided", async () => {
    server.use(
      http.get("/api/v1/ai/insights", () =>
        HttpResponse.json({
          status: "success",
          insights: [],
          period_key: "2026-07",
          calculation_result_hash: "abc123",
          hit_count: 0,
          miss_count: 0,
        }),
      ),
    );
    render(
      <InsightCachePanel
        initialPeriodKey="2026-07"
        initialCalculationHash="abc123"
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("insight-empty")).toBeInTheDocument();
    });
  });

  it("renders success entries on success envelope", async () => {
    server.use(
      http.get("/api/v1/ai/insights", () =>
        HttpResponse.json({
          status: "success",
          insights: [
            {
              insight_kind: "cost_reduction_candidate",
              question: "Q1?",
              answer: "A1",
              source_kind: "auto_analysis",
              evidence_ref: null,
              generated_at: "2026-08-19T00:00:00Z",
            },
          ],
          period_key: "2026-07",
          calculation_result_hash: "abc123",
          hit_count: 1,
          miss_count: 0,
        }),
      ),
    );
    render(
      <InsightCachePanel
        initialPeriodKey="2026-07"
        initialCalculationHash="abc123"
      />,
    );
    await waitFor(() => {
      const entries = screen.getAllByTestId("insight-entry");
      expect(entries.length).toBe(1);
      expect(entries[0].getAttribute("data-insight-kind")).toBe(
        "cost_reduction_candidate",
      );
    });
  });

  it("shows error alert on error envelope", async () => {
    server.use(
      http.get("/api/v1/ai/insights", () =>
        HttpResponse.json(
          {
            code: "AI_PIPA_CONSENT_MISSING",
            message_ko: "동의 필요",
            details: {},
            trace_id: "tr-1",
          },
          { status: 403 },
        ),
      ),
    );
    render(
      <InsightCachePanel
        initialPeriodKey="2026-07"
        initialCalculationHash="abc123"
      />,
    );
    const errorAlert = await screen.findByTestId("insight-error");
    expect(errorAlert.getAttribute("role")).toBe("alert");
    expect(errorAlert.textContent).toContain("AI_PIPA_CONSENT_MISSING");
  });

  it("cache key = tenantId::periodKey::hash (AD-25 verbatim)", () => {
    render(
      <InsightCachePanel
        tenantId="tenant-1"
        initialPeriodKey="2026-07"
        initialCalculationHash="abc123"
      />,
    );
    expect(screen.getByTestId("insight-cache-panel").getAttribute("data-cache-key")).toBe(
      "tenant-1::2026-07::abc123",
    );
  });

  it("manual load button click triggers fetch", async () => {
    server.use(
      http.get("/api/v1/ai/insights", () =>
        HttpResponse.json({
          status: "success",
          insights: [],
          period_key: "2026-08",
          calculation_result_hash: "xyz",
          hit_count: 0,
          miss_count: 0,
        }),
      ),
    );
    render(<InsightCachePanel />);
    fireEvent.change(screen.getByTestId("insight-period-input"), {
      target: { value: "2026-08" },
    });
    fireEvent.change(screen.getByTestId("insight-hash-input"), {
      target: { value: "xyz" },
    });
    fireEvent.click(screen.getByTestId("insight-load-button"));
    await waitFor(() => {
      expect(screen.getByTestId("insight-empty")).toBeInTheDocument();
    });
  });
});
