/**
 * apps/web/__tests__/components/m10-ai.AiReferenceBadge.test.tsx — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * F10.2-(a) verbatim: source_kind='ai_reference' → 보라 배지 '🤖 AI 참고(검증 필요)'
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AiReferenceBadge } from "@/components/m10-ai/AiReferenceBadge";

describe("AiReferenceBadge — Sprint 10.5 T3", () => {
  it("renders 보라 배지 when sourceKind='ai_reference'", () => {
    render(<AiReferenceBadge sourceKind="ai_reference" />);
    const badge = screen.getByTestId("ai-reference-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.getAttribute("data-source-kind")).toBe("ai_reference");
    expect(badge.textContent).toContain("AI 참고");
    expect(badge.textContent).toContain("검증 필요");
  });

  it("renders emoji marker 🤖 + tooltip", () => {
    render(<AiReferenceBadge sourceKind="ai_reference" />);
    const badge = screen.getByTestId("ai-reference-badge");
    expect(badge.textContent).toContain("🤖");
    expect(badge.getAttribute("title")).toBe(
      "AI는 비권위적입니다 — 확정 책임은 사용자에게",
    );
  });

  it("returns null when sourceKind='auto_analysis' (CR 11-4 D-005 reject)", () => {
    const { container } = render(<AiReferenceBadge sourceKind="auto_analysis" />);
    expect(container.firstChild).toBeNull();
  });
});
