// apps/web/__tests__/components/m9-abc.AbcValidationStatus.test.tsx — Story 9.1
//
// Component test for AbcValidationStatus — single-layer status display
// (PRD §F9.1 verbatim Korean SSOT message format).

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AbcValidationStatus } from "../../components/m9-abc/AbcValidationStatus";

import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("AbcValidationStatus component (Story 9.1)", () => {
  it("renders cost_pool layer with valid badge", () => {
    render(
      <AbcValidationStatus
        layer={{
          target: "cost_pool",
          sum_pct: "100",
          count: 4,
          is_valid: true,
          hash: "a".repeat(64),
          message_ko: null,
        }}
      />,
    );
    const node = screen.getByTestId("abc-validation-status-cost_pool");
    expect(node.getAttribute("data-valid")).toBe("true");
    expect(screen.getByText("100% 가드 통과")).toBeInTheDocument();
  });

  it("renders activity layer with invalid badge + Korean message", () => {
    render(
      <AbcValidationStatus
        layer={{
          target: "activity",
          sum_pct: "92",
          count: 3,
          is_valid: false,
          hash: "b".repeat(64),
          message_ko: "활동 열 합이 100%가 아닙니다 (현재 92%)",
        }}
      />,
    );
    const node = screen.getByTestId("abc-validation-status-activity");
    expect(node.getAttribute("data-valid")).toBe("false");
    expect(screen.getByText("100% 가드 실패")).toBeInTheDocument();
    expect(
      screen.getByTestId("abc-validation-message-activity"),
    ).toBeInTheDocument();
  });

  it("renders driver layer with V8 hash badge", () => {
    render(
      <AbcValidationStatus
        layer={{
          target: "driver",
          sum_pct: "100",
          count: 2,
          is_valid: true,
          hash: "c".repeat(64),
          message_ko: null,
        }}
      />,
    );
    const node = screen.getByTestId("abc-validation-status-driver");
    expect(node.getAttribute("data-valid")).toBe("true");
    expect(screen.getByText(/c{16}…/)).toBeInTheDocument();
  });

  it("shows full hash when not valid V8 format (defensive fallback)", () => {
    render(
      <AbcValidationStatus
        layer={{
          target: "cost_pool",
          sum_pct: "100",
          count: 4,
          is_valid: true,
          hash: "not-a-hash",
          message_ko: null,
        }}
      />,
    );
    expect(screen.getByText("not-a-hash")).toBeInTheDocument();
  });
});