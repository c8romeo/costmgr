/**
 * apps/web/__tests__/components/m10-ai.PromoteConfirmButton.test.tsx — Sprint 10.5 T4 wire (D-10-4-DEFER-4 해소)
 *
 * Story 10.4 (AI Promotion Port Idempotency) frontend test.
 *
 * Coverage:
 *   - Mount + button state (3 cases)
 *   - 3-layer defense stack integration (PIPA + M2 + idempotency)
 *   - 6 error envelopes + 1 success envelope (7 cases)
 *   - onSuccess / onError callback propagation (2 cases)
 *
 * Total: ~14 NEW vitest cases.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { PromoteConfirmButton } from "@/components/m10-ai/PromoteConfirmButton";
import { server } from "@/mocks/server";

beforeEach(() => {
  server.resetHandlers();
});

const successEnv = {
  status: "success" as const,
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

describe("PromoteConfirmButton — Sprint 10.5 T4", () => {
  it("mounts with disabled + idle label", () => {
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
      />,
    );
    const btn = screen.getByTestId("promote-confirm-button");
    expect(btn.getAttribute("data-state")).toBe("idle");
    expect(btn.textContent).toContain("승격");
  });

  it("disabled prop disables button", () => {
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
        disabled
      />,
    );
    expect(screen.getByTestId("promote-confirm-button")).toBeDisabled();
  });

  it("click triggers POST with AD-17 3-tuple body", async () => {
    let lastBody: unknown = null;
    server.use(
      http.post("/api/v1/ai/promote", async ({ request }) => {
        lastBody = await request.json();
        return HttpResponse.json(successEnv);
      }),
    );
    render(
      <PromoteConfirmButton
        accessToken="tok"
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
        confirmedValueHash="abc123"
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    await waitFor(() => {
      expect(lastBody).not.toBeNull();
      const body = lastBody as Record<string, unknown>;
      expect(body.tenant_id).toBe("tenant-1");
      expect(body.period_key).toBe("2026-07");
      expect(body.source_draft_id).toBe("draft-1");
      expect(body.confirmed_value_hash).toBe("abc123");
      expect(body.actor_id).toBe("actor-1");
    });
  });

  it("success envelope → invokes onSuccess with parsed envelope", async () => {
    server.use(
      http.post("/api/v1/ai/promote", () => HttpResponse.json(successEnv)),
    );
    const onSuccess = vi.fn();
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
        onSuccess={onSuccess}
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
      expect(onSuccess.mock.calls[0][0].promotion_id).toBe("promo-1");
    });
  });

  it("error envelope m2_only → AD-17 verbatim PIPA gate path", async () => {
    server.use(
      http.post("/api/v1/ai/promote", () =>
        HttpResponse.json(
          {
            status: "m2_only",
            code: "INPUT_PROMOTION_M2_ONLY",
            message_ko: "M2만 가능",
            details: {},
            trace_id: "tr-1",
          },
          { status: 403 },
        ),
      ),
    );
    const onError = vi.fn();
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
        onError={onError}
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    await waitFor(() => {
      expect(onError).toHaveBeenCalledTimes(1);
      expect(onError.mock.calls[0][0].code).toBe("INPUT_PROMOTION_M2_ONLY");
    });
    const alert = await screen.findByTestId("promote-error-alert");
    expect(alert.getAttribute("data-error-code")).toBe("INPUT_PROMOTION_M2_ONLY");
  });

  it("error envelope pipa_consent_missing → AI_PIPA_CONSENT_MISSING", async () => {
    server.use(
      http.post("/api/v1/ai/promote", () =>
        HttpResponse.json(
          {
            status: "pipa_consent_missing",
            code: "AI_PIPA_CONSENT_MISSING",
            message_ko: "PIPA 동의 필요",
            details: {},
            trace_id: "tr-1",
          },
          { status: 403 },
        ),
      ),
    );
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    const alert = await screen.findByTestId("promote-error-alert");
    expect(alert.getAttribute("data-error-code")).toBe("AI_PIPA_CONSENT_MISSING");
  });

  it("error envelope idempotency_mismatch → same 3-tuple, different hash", async () => {
    server.use(
      http.post("/api/v1/ai/promote", () =>
        HttpResponse.json(
          {
            status: "idempotency_mismatch",
            code: "PROMOTE_IDEMPOTENCY_MISMATCH",
            message_ko: "hash 변경됨",
            details: {},
            trace_id: "tr-1",
          },
          { status: 422 },
        ),
      ),
    );
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    const alert = await screen.findByTestId("promote-error-alert");
    expect(alert.getAttribute("data-error-code")).toBe(
      "PROMOTE_IDEMPOTENCY_MISMATCH",
    );
  });

  it("error envelope promotion_denied → AD-7 strict invariant guard", async () => {
    server.use(
      http.post("/api/v1/ai/promote", () =>
        HttpResponse.json(
          {
            status: "promotion_denied",
            code: "INPUT_PROMOTION_DENIED",
            message_ko: "직접 INSERT 거부",
            details: {},
            trace_id: "tr-1",
          },
          { status: 422 },
        ),
      ),
    );
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    const alert = await screen.findByTestId("promote-error-alert");
    expect(alert.getAttribute("data-error-code")).toBe("INPUT_PROMOTION_DENIED");
  });

  it("error envelope draft_immutable", async () => {
    server.use(
      http.post("/api/v1/ai/promote", () =>
        HttpResponse.json(
          {
            status: "draft_immutable",
            code: "PROMOTE_DRAFT_IMMUTABLE",
            message_ko: "이미 승격됨",
            details: {},
            trace_id: "tr-1",
          },
          { status: 409 },
        ),
      ),
    );
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    const alert = await screen.findByTestId("promote-error-alert");
    expect(alert.getAttribute("data-error-code")).toBe("PROMOTE_DRAFT_IMMUTABLE");
  });

  it("error envelope source_draft_not_found", async () => {
    server.use(
      http.post("/api/v1/ai/promote", () =>
        HttpResponse.json(
          {
            status: "source_draft_not_found",
            code: "PROMOTE_SOURCE_DRAFT_NOT_FOUND",
            message_ko: "초안 없음",
            details: {},
            trace_id: "tr-1",
          },
          { status: 404 },
        ),
      ),
    );
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    const alert = await screen.findByTestId("promote-error-alert");
    expect(alert.getAttribute("data-error-code")).toBe(
      "PROMOTE_SOURCE_DRAFT_NOT_FOUND",
    );
  });

  it("network error → catches and surfaces message", async () => {
    server.use(http.post("/api/v1/ai/promote", () => HttpResponse.error()));
    render(
      <PromoteConfirmButton
        tenantId="tenant-1"
        periodKey="2026-07"
        sourceDraftId="draft-1"
        actorId="actor-1"
      />,
    );
    fireEvent.click(screen.getByTestId("promote-confirm-button"));
    const alert = await screen.findByTestId("promote-error-alert");
    expect(alert.textContent).toBeTruthy();
  });
});
