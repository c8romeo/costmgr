/**
 * apps/web/__tests__/components/m10-ai.PromoteResultToast.test.tsx — Sprint 10.5 T4 wire (D-10-4-DEFER-4 해소)
 *
 * Story 10.4 frontend toast for Discriminated union PromoteEnvelope result.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PromoteResultToast } from "@/components/m10-ai/PromoteResultToast";
import type { PromoteEnvelope } from "@/lib/ai-promote";


const successEnv: PromoteEnvelope = {
  status: "success",
  tenant_id: "tenant-1",
  period_key: "2026-07",
  source_draft_id: "draft-1",
  promotion_id: "promo-1",
  idempotency_key: "idem-1",
  confirmed_input_row_id: "row-1",
  promoted_at: "2026-08-19T00:00:00Z",
  draft_hash: "deadbeef",
  idempotent_replay: false,
  audit_log_ids: ["audit-1", "audit-2"],
};

describe("PromoteResultToast — Sprint 10.5 T4", () => {
  it("returns null when envelope is null", () => {
    const { container } = render(<PromoteResultToast envelope={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders success status with role=status + audit_log_ids", () => {
    render(<PromoteResultToast envelope={successEnv} />);
    const toast = screen.getByTestId("promote-result-toast");
    expect(toast.getAttribute("data-status")).toBe("success");
    expect(toast.getAttribute("role")).toBe("status");
    expect(toast.textContent).toContain("승격 완료");
    expect(screen.getByTestId("promote-result-promo-id").textContent).toContain("promo-1");
    expect(screen.getByTestId("promote-result-audit-ids").textContent).toContain(
      "audit-1, audit-2",
    );
  });

  it("renders replay indicator when idempotent_replay=true", () => {
    render(
      <PromoteResultToast
        envelope={{ ...successEnv, idempotent_replay: true }}
      />,
    );
    expect(screen.getByTestId("promote-result-replay")).toBeInTheDocument();
  });

  it("renders error envelope with role=alert", () => {
    const err: PromoteEnvelope = {
      status: "m2_only",
      code: "INPUT_PROMOTION_M2_ONLY",
      message_ko: "M2만 가능",
      details: {},
      trace_id: "tr-1",
    };
    render(<PromoteResultToast envelope={err} />);
    const toast = screen.getByTestId("promote-result-toast");
    expect(toast.getAttribute("role")).toBe("alert");
    expect(toast.getAttribute("data-status")).toBe("m2_only");
    expect(screen.getByTestId("promote-result-error-code").textContent).toContain(
      "INPUT_PROMOTION_M2_ONLY",
    );
  });

  it("renders pipa_consent_missing with PIPA ko-KR message", () => {
    const err: PromoteEnvelope = {
      status: "pipa_consent_missing",
      code: "AI_PIPA_CONSENT_MISSING",
      message_ko: "PIPA 동의 필요",
      details: {},
      trace_id: "tr-1",
    };
    render(<PromoteResultToast envelope={err} />);
    expect(screen.getByTestId("promote-result-toast").getAttribute("data-status")).toBe(
      "pipa_consent_missing",
    );
  });

  it("CR 11-4 D-005 — unknown status → null + warning", () => {
    const unknown = {
      status: "totally_unknown",
      code: "UNKNOWN",
      message_ko: "x",
      details: {},
      trace_id: "tr-1",
    } as unknown as PromoteEnvelope;
    const { container } = render(
      <PromoteResultToast envelope={unknown} />,
    );
    expect(container.firstChild).toBeNull();
  });
});
