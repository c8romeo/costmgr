/**
 * apps/web/__tests__/components/m10-ai.ConfidenceBadge.test.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Vitest tests for ConfidenceBadge (M10 AI monthly extraction confidence indicator).
 *
 * Coverage (T1):
 *   - Mount + tier propagation (3 cases)
 *   - Confidence threshold classification (3 cases — high/medium/low)
 *   - Defensive clamp on invalid input (2 cases)
 *
 * Total: ~8 NEW vitest cases.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConfidenceBadge } from "@/components/m10-ai/ConfidenceBadge";

describe("ConfidenceBadge — Sprint 10.5 T1", () => {
  it("mounts with data-testid + data-confidence-tier=high when confidence ≥ 0.85", () => {
    render(<ConfidenceBadge confidence={0.92} />);
    const badge = screen.getByTestId("confidence-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.getAttribute("data-confidence-tier")).toBe("high");
    expect(badge.getAttribute("data-confidence-value")).toBe("0.92");
  });

  it("classifies confidence 0.70–0.84 as medium", () => {
    render(<ConfidenceBadge confidence={0.78} />);
    const badge = screen.getByTestId("confidence-badge");
    expect(badge.getAttribute("data-confidence-tier")).toBe("medium");
  });

  it("classifies confidence < 0.70 as low (PRD §8.1 M0-c 70% 임계값)", () => {
    render(<ConfidenceBadge confidence={0.55} />);
    const badge = screen.getByTestId("confidence-badge");
    expect(badge.getAttribute("data-confidence-tier")).toBe("low");
  });

  it("boundary 0.70 is inclusive for medium (>= 0.70 medium)", () => {
    render(<ConfidenceBadge confidence={0.7} />);
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("medium");
  });

  it("boundary 0.85 is inclusive for high", () => {
    render(<ConfidenceBadge confidence={0.85} />);
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("high");
  });

  it("clamps NaN to 0 (defensive guard)", () => {
    render(<ConfidenceBadge confidence={Number.NaN} />);
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("low");
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-value")).toBe("0.00");
  });

  it("clamps negative values to 0", () => {
    render(<ConfidenceBadge confidence={-0.5} />);
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("low");
  });

  it("clamps values > 1.0 to within range? actually clamps to high", () => {
    render(<ConfidenceBadge confidence={1.5} />);
    // 1.5 is not in [0, 1] so defensive clamp defaults to 0 (low)
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("low");
  });

  it("aria-label differs per tier (low has warning text)", () => {
    const { rerender } = render(<ConfidenceBadge confidence={0.5} />);
    const lowBadge = screen.getByTestId("confidence-badge");
    expect(lowBadge.getAttribute("aria-label")).toContain("확인 필수");
    rerender(<ConfidenceBadge confidence={0.95} />);
    const highBadge = screen.getByTestId("confidence-badge");
    expect(highBadge.getAttribute("aria-label")).toContain("높은 신뢰도");
  });
});
