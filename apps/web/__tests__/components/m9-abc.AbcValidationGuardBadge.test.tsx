// apps/web/__tests__/components/m9-abc.AbcValidationGuardBadge.test.tsx — Story 9.1
//
// Component test for AbcValidationGuardBadge — 3-layer 100% guard badge
// (PRD §F9.1 verbatim "[계산]이 잠기는 것" 메커니즘).

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AbcValidationGuardBadge } from "../../components/m9-abc/AbcValidationGuardBadge";
import type { ValidationResponse } from "../../lib/m9-abc-validation";

import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

function buildResponse(
  layers: ValidationResponse["layers"],
  allValid: boolean,
): ValidationResponse {
  return {
    cost_pool_id: "cp-001",
    activity_id: "act-001",
    all_valid: allValid,
    layers,
  };
}

const VALID_LAYERS: ValidationResponse["layers"] = [
  {
    target: "cost_pool",
    sum_pct: "100",
    count: 4,
    is_valid: true,
    hash: "a".repeat(64),
    message_ko: null,
  },
  {
    target: "activity",
    sum_pct: "100",
    count: 3,
    is_valid: true,
    hash: "b".repeat(64),
    message_ko: null,
  },
  {
    target: "driver",
    sum_pct: "100",
    count: 2,
    is_valid: true,
    hash: "c".repeat(64),
    message_ko: null,
  },
];

describe("AbcValidationGuardBadge component (Story 9.1)", () => {
  it("renders all-valid badge with green '계산 활성화' label", () => {
    render(<AbcValidationGuardBadge response={buildResponse(VALID_LAYERS, true)} />);
    const badge = screen.getByTestId("abc-validation-guard-badge");
    expect(badge.getAttribute("data-all-valid")).toBe("true");
    expect(screen.getByText("계산 활성화")).toBeInTheDocument();
  });

  it("renders locked badge with red '계산 잠김' label", () => {
    const invalidLayers: ValidationResponse["layers"] = VALID_LAYERS.map(
      (l, i) => ({
        ...l,
        is_valid: i !== 0,
        message_ko:
          i === 0 ? "원가풀 행 합이 100%가 아닙니다 (현재 105%)" : null,
      }),
    );
    render(
      <AbcValidationGuardBadge response={buildResponse(invalidLayers, false)} />,
    );
    const badge = screen.getByTestId("abc-validation-guard-badge");
    expect(badge.getAttribute("data-all-valid")).toBe("false");
    expect(screen.getByText("계산 잠김")).toBeInTheDocument();
  });

  it("renders all 3 layer indicators", () => {
    render(<AbcValidationGuardBadge response={buildResponse(VALID_LAYERS, true)} />);
    expect(screen.getByTestId("guard-layer-cost_pool")).toBeInTheDocument();
    expect(screen.getByTestId("guard-layer-activity")).toBeInTheDocument();
    expect(screen.getByTestId("guard-layer-driver")).toBeInTheDocument();
  });

  it("renders gray indicator when layer is absent in response", () => {
    const partialLayers: ValidationResponse["layers"] = [
      {
        target: "cost_pool",
        sum_pct: "100",
        count: 4,
        is_valid: true,
        hash: "a".repeat(64),
        message_ko: null,
      },
    ];
    render(
      <AbcValidationGuardBadge response={buildResponse(partialLayers, false)} />,
    );
    expect(screen.getByTestId("guard-layer-cost_pool")).toBeInTheDocument();
    expect(screen.getByTestId("guard-layer-activity")).toBeInTheDocument();
    expect(screen.getByTestId("guard-layer-driver")).toBeInTheDocument();
  });
});