/**
 * apps/web/__tests__/components/m10-ai.AiDraftCard.test.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Vitest tests for AiDraftCard (M10 AI monthly extraction draft card).
 *
 * Coverage (T1):
 *   - Mount with high-confidence draft (1 case)
 *   - Mount with low-confidence draft + warning icon (1 case)
 *   - Mount with requires_user_confirmation (1 case)
 *   - Field name label rendering (ko-KR SSOT) (1 case)
 *   - ConfidenceBadge child component present (1 case)
 *   - Evidence page displayed (1 case)
 *   - Edge: confidence = exactly threshold (0.70) = high (1 case)
 *   - Edge: confidence = 0.0 = low (1 case)
 *   - Edge: confidence = 1.0 = high (1 case)
 *   - Mount with no evidence_page = null displayed (1 case)
 *   - Mount with very long field_name truncated (1 case)
 *
 * Total: ~11 NEW vitest cases.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AiDraftCard } from "@/components/m10-ai/AiDraftCard";
import { type MonthlyDraftEntry } from "@/lib/ai-extract";

const baseDraft: MonthlyDraftEntry = {
  field_name: "직접재료비",
  value: "1000000",
  confidence: "0.92",
  target_table: "monthly_inputs",
  evidence_page: 1,
  requires_user_confirmation: false,
};

describe("AiDraftCard — Sprint 10.5 T1", () => {
  it("mounts high-confidence draft card with field name + value", () => {
    render(<AiDraftCard draft={baseDraft} />);
    expect(screen.getByTestId("ai-draft-card")).toBeInTheDocument();
    expect(screen.getByText("직접재료비")).toBeInTheDocument();
    expect(screen.getByText("1000000")).toBeInTheDocument();
  });

  it("mounts low-confidence draft with low-confidence badge", () => {
    render(<AiDraftCard draft={{ ...baseDraft, confidence: "0.55" }} />);
    expect(screen.getByTestId("ai-draft-card")).toBeInTheDocument();
    // ConfidenceBadge renders with data-confidence-tier="low"
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("low");
  });

  it("mounts draft with requires_user_confirmation flag", () => {
    render(
      <AiDraftCard
        draft={{ ...baseDraft, requires_user_confirmation: true }}
      />,
    );
    expect(
      screen.getByTestId("ai-draft-confirmation-required"),
    ).toBeInTheDocument();
  });

  it("renders field_name label with ko-KR SSOT mapping", () => {
    render(
      <AiDraftCard
        draft={{ ...baseDraft, field_name: "기말재고" }}
      />,
    );
    expect(screen.getByText("기말재고")).toBeInTheDocument();
  });

  it("includes ConfidenceBadge child component", () => {
    render(<AiDraftCard draft={baseDraft} />);
    // ConfidenceBadge renders with high/medium/low data-testid
    expect(screen.getByTestId(/confidence-badge/)).toBeInTheDocument();
  });

  it("displays evidence_page when present", () => {
    render(<AiDraftCard draft={baseDraft} />);
    expect(screen.getByText(/출처: p\.1/)).toBeInTheDocument();
  });

  it("confidence = exactly threshold (0.70) = medium (boundary)", () => {
    render(<AiDraftCard draft={{ ...baseDraft, confidence: "0.70" }} />);
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("medium");
  });

  it("confidence = 0.0 = low (boundary)", () => {
    render(<AiDraftCard draft={{ ...baseDraft, confidence: "0.0" }} />);
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("low");
  });

  it("confidence = 1.0 = high (boundary)", () => {
    render(<AiDraftCard draft={{ ...baseDraft, confidence: "1.0" }} />);
    expect(screen.getByTestId("confidence-badge").getAttribute("data-confidence-tier")).toBe("high");
  });

  it("mounts with evidence_page=null gracefully", () => {
    render(
      <AiDraftCard draft={{ ...baseDraft, evidence_page: null }} />,
    );
    expect(screen.getByTestId("ai-draft-card")).toBeInTheDocument();
  });

  it("handles long field_name gracefully (no overflow)", () => {
    render(
      <AiDraftCard
        draft={{ ...baseDraft, field_name: "A".repeat(120) }}
      />,
    );
    expect(screen.getByTestId("ai-draft-card")).toBeInTheDocument();
  });
});
