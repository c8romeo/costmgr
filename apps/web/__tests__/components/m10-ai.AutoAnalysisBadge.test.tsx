/**
 * apps/web/__tests__/components/m10-ai.AutoAnalysisBadge.test.tsx — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * F10.2-(a) verbatim: source_kind='auto_analysis' → 파란 배지 '📊 자동 분석'
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AutoAnalysisBadge } from "@/components/m10-ai/AutoAnalysisBadge";

describe("AutoAnalysisBadge — Sprint 10.5 T3", () => {
  it("renders 파란 배지 when sourceKind='auto_analysis'", () => {
    render(<AutoAnalysisBadge sourceKind="auto_analysis" />);
    const badge = screen.getByTestId("auto-analysis-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.getAttribute("data-source-kind")).toBe("auto_analysis");
    expect(badge.textContent).toContain("자동 분석");
  });

  it("renders emoji marker 📊 + tooltip", () => {
    render(<AutoAnalysisBadge sourceKind="auto_analysis" />);
    const badge = screen.getByTestId("auto-analysis-badge");
    expect(badge.textContent).toContain("📊");
    expect(badge.getAttribute("title")).toBe(
      "AI는 비권위적입니다 — 확정 책임은 사용자에게",
    );
  });

  it("returns null when sourceKind='ai_reference' (CR 11-4 D-005 reject)", () => {
    const { container } = render(<AutoAnalysisBadge sourceKind="ai_reference" />);
    expect(container.firstChild).toBeNull();
  });
});
