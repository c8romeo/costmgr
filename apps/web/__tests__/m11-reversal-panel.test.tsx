/**
 * apps/web/__tests__/m11-reversal-panel.test.tsx — Story 11.1 T10.10
 *
 * Vitest + React Testing Library scenarios for `<ReversalRequestDialog />`
 * + `<ReversalRequestForm />`:
 *
 * 1. test_dialog_renders_when_open — Dialog visible with reason textarea.
 * 2. test_period_status_locked_disables_submit — period_status='locked' →
 *    submit button disabled.
 * 3. test_capability_false_disables_submit — capability_granted=false →
 *    submit button disabled.
 * 4. test_corrected_qty_period_key_pair_validation — corrected_qty without
 *    corrected_period_key → validation error.
 * 5. test_submit_success_calls_handler — fills reason → [역분개 실행] →
 *    onSubmit called with valid payload.
 * 6. test_capability_gated_hide — capability_granted=false →
 *    ReversalRequestButton returns null (hidden).
 */

import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ReversalRequestDialog } from "@/components/m4-inventory/ReversalRequestDialog";
import { ReversalRequestButton } from "@/components/m4-inventory/ReversalRequestButton";

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}));

// Mock next-intl useTranslations (return key as-is)
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}));

const TARGET_EVENT_ID = "11111111-1111-1111-1111-111111111111";
const PERIOD_KEY = "2026-08";

describe("ReversalRequestDialog", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  // ── Case 1: Dialog renders when open ─────────────────────────
  it("test_dialog_renders_when_open", () => {
    render(
      <ReversalRequestDialog
        open={true}
        onOpenChange={() => {}}
        target_event_id={TARGET_EVENT_ID}
        period_key={PERIOD_KEY}
        period_status="closed"
        capability_granted={true}
      />,
    );
    expect(screen.getByTestId("reversal-request-dialog")).toBeInTheDocument();
    expect(screen.getByTestId("reversal-request-reason")).toBeInTheDocument();
    expect(screen.getByTestId("reversal-request-submit")).toBeInTheDocument();
    expect(screen.getByTestId("reversal-request-cancel")).toBeInTheDocument();
  });

  // ── Case 2: period_status='locked' → submit disabled ─────────
  it("test_period_status_locked_disables_submit", () => {
    render(
      <ReversalRequestDialog
        open={true}
        onOpenChange={() => {}}
        target_event_id={TARGET_EVENT_ID}
        period_key={PERIOD_KEY}
        period_status="locked"
        capability_granted={true}
      />,
    );
    const submit = screen.getByTestId("reversal-request-submit");
    expect(submit).toBeDisabled();
  });

  // ── Case 3: capability_granted=false → submit disabled ───────
  it("test_capability_false_disables_submit", () => {
    render(
      <ReversalRequestDialog
        open={true}
        onOpenChange={() => {}}
        target_event_id={TARGET_EVENT_ID}
        period_key={PERIOD_KEY}
        period_status="closed"
        capability_granted={false}
      />,
    );
    const submit = screen.getByTestId("reversal-request-submit");
    expect(submit).toBeDisabled();
  });

  // ── Case 4: corrected_qty without corrected_period_key → validation error ──
  it("test_corrected_qty_period_key_pair_validation", async () => {
    const user = userEvent.setup();
    render(
      <ReversalRequestDialog
        open={true}
        onOpenChange={() => {}}
        target_event_id={TARGET_EVENT_ID}
        period_key={PERIOD_KEY}
        period_status="closed"
        capability_granted={true}
      />,
    );
    await user.type(
      screen.getByTestId("reversal-request-reason"),
      "오류 정정 사유",
    );
    await user.type(
      screen.getByTestId("reversal-request-corrected-qty"),
      "10.5",
    );
    // corrected_period_key NOT filled — validation error
    await user.click(screen.getByTestId("reversal-request-submit"));
    expect(
      screen.getByTestId("reversal-request-validation-error"),
    ).toHaveTextContent("error_corrected_pair_required");
  });

  // ── Case 5: submit success calls handler ─────────────────────
  it("test_submit_success_calls_handler", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue({
      correction_group_id: "22222222-2222-2222-2222-222222222222",
      negating_event_id: "33333333-3333-3333-3333-333333333333",
      corrected_event_id: null,
      target_event_id: TARGET_EVENT_ID,
      reversal_history: [],
      trace_id: "44444444-4444-4444-4444-444444444444",
      cache_invalidation_receipt: {},
    });
    render(
      <ReversalRequestDialog
        open={true}
        onOpenChange={() => {}}
        target_event_id={TARGET_EVENT_ID}
        period_key={PERIOD_KEY}
        period_status="closed"
        capability_granted={true}
        onSubmit={onSubmit}
      />,
    );
    await user.type(
      screen.getByTestId("reversal-request-reason"),
      "오류 정정 사유",
    );
    await user.click(screen.getByTestId("reversal-request-submit"));
    expect(onSubmit).toHaveBeenCalledWith({
      target_event_id: TARGET_EVENT_ID,
      reason: "오류 정정 사유",
      corrected_qty: null,
      corrected_period_key: null,
    });
  });

  // ── Case 6: capability-gated UI (button hidden) ──────────────
  it("test_capability_gated_hide", () => {
    const { container } = render(
      <ReversalRequestButton
        target_event_id={TARGET_EVENT_ID}
        period_key={PERIOD_KEY}
        period_status="closed"
        capability_granted={false}
      />,
    );
    // Button is hidden — Dialog should NOT render at all.
    expect(container.firstChild).toBeNull();
    expect(screen.queryByTestId("reversal-request-button")).toBeNull();
  });
});
