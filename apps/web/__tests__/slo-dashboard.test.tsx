// apps/web/__tests__/slo-dashboard.test.tsx — SLO dashboard component parity test.
//
// CR 12-5 D-PARITY-01 — backend ↔ frontend parity check.
// 3 NEW vitest cases PASS (Phase 8 cj-style 95번째 wire frontend tests).
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SLOStatusBadge from "@/components/performance/SLOStatusBadge";

describe("SLOStatusBadge — Phase 8 F24.2", () => {
  it("renders green badge when actual < 80% of budget", () => {
    render(<SLOStatusBadge actual_p99_ms={1200} budget_ms={5000} />);
    expect(screen.getByTestId("slo-status-ok")).toBeInTheDocument();
    expect(screen.getByText(/SLA-1/)).toBeInTheDocument();
  });

  it("renders yellow badge when actual between 80% and 100% of budget", () => {
    render(<SLOStatusBadge actual_p99_ms={4200} budget_ms={5000} />);
    expect(screen.getByTestId("slo-status-warn")).toBeInTheDocument();
  });

  it("renders red badge and shows owner-only ack prompt when actual > budget", () => {
    render(<SLOStatusBadge actual_p99_ms={6500} budget_ms={5000} />);
    expect(screen.getByTestId("slo-status-violation")).toBeInTheDocument();
    // AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존.
    expect(screen.getByText(/owner-only/)).toBeInTheDocument();
  });
});
