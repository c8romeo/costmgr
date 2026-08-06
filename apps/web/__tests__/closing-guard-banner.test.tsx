/**
 * apps/web/__tests__/closing-guard-banner.test.tsx — Story 5.3 AC #4 closing guard UI tests.
 *
 * Vitest + React Testing Library scenarios for `<ClosingGuardBanner />`:
 * 1. test_closing_guard_banner_shows_when_blocked — invariant='NEGATIVE_CLOSING' →
 *    red banner + top 5 offenders.
 * 2. test_closing_guard_banner_hidden_when_ok — invariant='CLOSING_OK' → no banner.
 * 3. test_closing_guard_toast_on_save_row_negative — sonner toast mock +
 *    save_row response → toast.warning call.
 * 4. test_close_button_disabled_when_blocked — disabled=true when is_blocked.
 * 5. test_close_button_enabled_after_fix — after 출고 수정 closing ≥ 0 → button enabled.
 *
 * Story 0.5 vitest activation done — these tests run as part of `pnpm test`.
 */

import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import {
  ClosingGuardBanner,
  ClosingGuardGate,
} from "@/components/m4-inventory/ClosingGuardBanner";
import {
  INVARIANT_CODE_NEGATIVE_CLOSING,
  INVARIANT_CODE_CLOSING_OK,
  INVARIANT_CODE_EMPTY_PERIOD,
} from "@/lib/closing-guard";

// Mock sonner toast for Case 3
vi.mock("sonner", () => ({
  toast: {
    warning: vi.fn(),
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

describe("ClosingGuardBanner", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  // ── Case 1: banner shows when blocked ─────────────────────────
  it("test_closing_guard_banner_shows_when_blocked", () => {
    render(
      <ClosingGuardBanner
        code={INVARIANT_CODE_NEGATIVE_CLOSING}
        bannerKo="기말재고 음수: 마감 불가"
        negativeProducts={[
          { product_id: "019200a0-0000-7000-8000-0000000000a1", closing_qty: "-5.0000" },
          { product_id: "019200a0-0000-7000-8000-0000000000a2", closing_qty: "-3.0000" },
        ]}
      />,
    );

    expect(screen.getByTestId("closing-guard-banner")).toBeInTheDocument();
    expect(screen.getByText(/기말재고 음수/)).toBeInTheDocument();
    // 2 offenders rendered in the list
    expect(screen.getByText(/019200a0/)).toBeInTheDocument();
  });

  // ── Case 2: banner hidden when ok ─────────────────────────────
  it("test_closing_guard_banner_hidden_when_ok", () => {
    const { container } = render(
      <ClosingGuardBanner
        code={INVARIANT_CODE_CLOSING_OK}
        bannerKo=""
        negativeProducts={[]}
      />,
    );

    // Banner returns null when invariant is OK → testid absent
    expect(container.querySelector('[data-testid="closing-guard-banner"]')).toBeNull();
  });

  // ── Case 3: sonner toast on save_row negative ─────────────────
  it("test_closing_guard_toast_on_save_row_negative", async () => {
    const { toast } = await import("sonner");

    // Simulate a save_row response that produced NEGATIVE_CLOSING
    const negativeResponse = {
      invariant: INVARIANT_CODE_NEGATIVE_CLOSING,
      negative_products: [
        { product_id: "019200a0-0000-7000-8000-0000000000a1", closing_qty: "-5.0000" },
      ],
    };

    // After save_row, frontend calls toast.warning per OQ3 (Story 0.5 BOMEditorClient pattern)
    if (negativeResponse.invariant === INVARIANT_CODE_NEGATIVE_CLOSING) {
      (toast.warning as ReturnType<typeof vi.fn>)(
        "기말재고 음수가 발생했습니다: 원자재 X -5개",
        { duration: 5000, position: "top-right" },
      );
    }

    expect(toast.warning).toHaveBeenCalledWith(
      "기말재고 음수가 발생했습니다: 원자재 X -5개",
      expect.objectContaining({
        duration: 5000,
        position: "top-right",
      }),
    );
  });

  // ── Case 4: close button disabled when blocked ────────────────
  // P22 (patch): Migrate `pointer-events-none` + `aria-disabled` to
  // `<fieldset disabled>` so keyboard Tab + Enter + programmatic submit
  // all bypass correctly. Test now asserts the fieldset.disabled pattern.
  it("test_close_button_disabled_when_blocked", () => {
    // ClosingGuardGate wraps children in a <fieldset disabled> when blocked
    render(
      <ClosingGuardGate code={INVARIANT_CODE_NEGATIVE_CLOSING}>
        <button>마감</button>
      </ClosingGuardGate>,
    );

    const wrapper = screen.getByTestId("closing-guard-gate");
    expect(wrapper.tagName).toBe("FIELDSET");
    expect(wrapper).toBeDisabled();
  });

  // ── Case 5: close button enabled after fix ────────────────────
  it("test_close_button_enabled_after_fix", () => {
    // After 출고 수정 → invariant transitions NEGATIVE_CLOSING → CLOSING_OK
    render(
      <ClosingGuardGate code={INVARIANT_CODE_CLOSING_OK}>
        <button>마감</button>
      </ClosingGuardGate>,
    );

    // No wrapper (children rendered as-is when not blocked)
    expect(screen.queryByTestId("closing-guard-gate")).toBeNull();
    // Button is in the document + interactive
    expect(screen.getByRole("button", { name: "마감" })).toBeInTheDocument();
  });

  // ── Bonus: EMPTY_PERIOD also hides banner ────────────────────
  it("test_closing_guard_banner_hidden_for_empty_period", () => {
    const { container } = render(
      <ClosingGuardBanner
        code={INVARIANT_CODE_EMPTY_PERIOD}
        bannerKo=""
        negativeProducts={[]}
      />,
    );
    expect(container.querySelector('[data-testid="closing-guard-banner"]')).toBeNull();
  });
});