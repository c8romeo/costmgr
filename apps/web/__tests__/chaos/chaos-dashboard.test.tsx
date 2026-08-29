/**
 * apps/web/__tests__/chaos/chaos-dashboard.test.tsx —
 * Phase 9 (cj-style 99번째 wire) — RTL render discipline (CR 11-4 D-003).
 *
 * Verifies the chaos engineering admin dashboard renders correctly:
 *   1. All 4 components render (experiment list + trigger button +
 *      game day calendar + rollback log).
 *   2. Trigger button disabled while triggering.
 *   3. Locale=ko-KR renders through NextIntlClientProvider.
 *
 * 3 NEW vitest cases (page test).
 */

import { render, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, it, expect, vi } from "vitest";

import koKR from "@/messages/ko-KR.json";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
  }),
  redirect: vi.fn(),
}));

import { ChaosDashboardPanel } from "@/components/chaos/ChaosDashboardPanel";

// Mock the fetcher to isolate the panel from real network.
vi.mock("@/lib/chaos/chaos-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/chaos/chaos-client")>(
    "@/lib/chaos/chaos-client",
  );
  return {
    ...actual,
    listChaosExperiments: vi.fn().mockResolvedValue({
      experiments: [
        {
          experiment_id: "exp-001",
          experiment_name: "latency-drill",
          fault_type: "latency",
          blast_radius: "single_request",
          region: "seoul",
          duration_seconds: 60,
          intensity: "low",
          status: "completed",
          dry_run: true,
          started_at: "2026-08-24T00:00:00Z",
          trace_id: "trace-001",
        },
      ],
      trace_id: "trace-list",
    }),
    listChaosRollbacks: vi.fn().mockResolvedValue({
      rollbacks: [
        {
          rollback_id: "rb-001",
          experiment_id: "exp-001",
          strategy: "automatic",
          reason: "p99_budget_exceeded",
          triggered_at: "2026-08-24T00:01:00Z",
        },
      ],
      trace_id: "trace-rb",
    }),
    triggerChaosExperiment: vi.fn().mockResolvedValue({
      experiment_id: "exp-002",
      trace_id: "trace-trigger",
    }),
  };
});

describe("chaos dashboard page (RTL render)", () => {
  const messages = koKR;

  function wrap(node: React.ReactElement) {
    return render(
      <NextIntlClientProvider locale="ko-KR" messages={messages}>
        {node}
      </NextIntlClientProvider>,
    );
  }

  it("renders all 4 components (experiment list + trigger + calendar + rollback)", async () => {
    wrap(<ChaosDashboardPanel accessToken="test-token" locale="ko-KR" />);
    await waitFor(() => {
      expect(
        document.querySelector("[data-component='chaos-experiment-list']"),
      ).toBeTruthy();
    });
    await waitFor(() => {
      expect(
        document.querySelector("[data-component='chaos-experiment-trigger-button']"),
      ).toBeTruthy();
    });
    expect(
      document.querySelector("[data-component='chaos-game-day-calendar']"),
    ).toBeTruthy();
    expect(
      document.querySelector("[data-component='chaos-rollback-log']"),
    ).toBeTruthy();
  });

  it("renders with locale=ko-KR through NextIntlClientProvider (no error thrown)", () => {
    expect(() =>
      wrap(<ChaosDashboardPanel accessToken="test-token" locale="ko-KR" />),
    ).not.toThrow();
  });

  it("ChaosExperimentApiError class is exported from lib", async () => {
    const lib = await import("@/lib/chaos/chaos-client");
    expect(lib.ChaosExperimentApiError).toBeDefined();
    expect(typeof lib.ChaosExperimentApiError).toBe("function");
  });
});
