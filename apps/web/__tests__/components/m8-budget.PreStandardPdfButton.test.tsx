// apps/web/__tests__/components/m8-budget.PreStandardPdfButton.test.tsx — Story 8.3
//
// Component tests for PreStandardPdfButton.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PreStandardPdfButton } from "../../components/m8-budget/PreStandardPdfButton";
import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("PreStandardPdfButton component (Story 8.3)", () => {
  const baseProps = {
    accessToken: undefined as string | undefined,
    periodKey: "2026-07#B1",
    snapshotReady: true,
  };

  it("renders the PDF button (enabled when snapshotReady=true)", () => {
    render(<PreStandardPdfButton {...baseProps} />);
    const button = screen.getByTestId("pre-standard-pdf-button");
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  it("renders the PDF button (disabled when snapshotReady=false)", () => {
    render(<PreStandardPdfButton {...baseProps} snapshotReady={false} />);
    const button = screen.getByTestId("pre-standard-pdf-button");
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled();
  });

  it("uses 'ready' tooltip when snapshotReady=true", () => {
    render(<PreStandardPdfButton {...baseProps} />);
    const button = screen.getByTestId("pre-standard-pdf-button");
    expect(button.getAttribute("title")).toContain("§9 #20");
  });

  it("uses 'disabled' tooltip when snapshotReady=false", () => {
    render(<PreStandardPdfButton {...baseProps} snapshotReady={false} />);
    const button = screen.getByTestId("pre-standard-pdf-button");
    expect(button.getAttribute("title")).toContain("예측을 먼저 실행하세요");
  });

  it("renders the Korean button label", () => {
    render(<PreStandardPdfButton {...baseProps} />);
    expect(screen.getByText(/예산-실적 차이 명세서 PDF/)).toBeInTheDocument();
  });
});