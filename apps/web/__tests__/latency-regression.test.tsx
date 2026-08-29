// apps/web/__tests__/latency-regression.test.tsx — Latency regression PR banner parity.
//
// 2 NEW vitest cases PASS (Phase 8 cj-style 95번째 wire frontend tests).
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LatencyRegressionBanner from "@/components/performance/LatencyRegressionBanner";

describe("LatencyRegressionBanner — Phase 8 F24.4", () => {
  it("renders p99 regression alert when delta exceeds 20% threshold", () => {
    render(
      <LatencyRegressionBanner
        actual_p99_ms={6500}
        baseline_p99_ms={5000}
        threshold_pct={20.0}
        trace_id="trace-abc-123"
      />,
    );
    expect(screen.getByTestId("regression-banner")).toBeInTheDocument();
    expect(screen.getByText(/trace-abc-123/)).toBeInTheDocument();
  });

  it("does not render when regression delta is below threshold", () => {
    const { container } = render(
      <LatencyRegressionBanner
        actual_p99_ms={5400}
        baseline_p99_ms={5000}
        threshold_pct={20.0}
        trace_id="trace-xyz-456"
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
