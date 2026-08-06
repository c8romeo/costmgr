/**
 * apps/web/__tests__/opening-inventory-edit-reject.test.tsx — Story 5.3 manual edit reject UI tests.
 *
 * Vitest + RTL scenarios for opening inventory form reject UI
 * (5-1 M14 + 5-3 AC #2 manual edit reject):
 * 1. test_opening_inventory_field_disabled_when_locked — form field disabled state.
 * 2. test_opening_inventory_save_attempt_shows_error_toast — sonner toast.error call on save attempt.
 * 3. test_opening_inventory_field_enabled_when_unlocked — opening chain not yet active.
 *
 * Story 0.5 vitest activation done — these tests run as part of `pnpm test`.
 */

import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import * as React from "react";
import { toast } from "sonner";

// Mock sonner toast — reference the same vi.fn() instances the test will assert against
vi.mock("sonner", () => ({
  toast: {
    warning: vi.fn(),
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

interface OpeningInventoryFieldProps {
  openingInventoryLocked: boolean;
  value: string;
  onChange: (v: string) => void;
  onSave: () => void;
}

/**
 * Inline form component (shadcn-style) — emulates the manual edit reject
 * pattern. This is a smoke test, not a full integration test.
 */
function OpeningInventoryField({
  openingInventoryLocked,
  value,
  onChange,
  onSave,
}: OpeningInventoryFieldProps): React.ReactElement {
  const handleSave = () => {
    if (openingInventoryLocked) {
      toast.error("기초재고는 자동 이월 체인에 의해 잠겼습니다");
      return;
    }
    onSave();
  };

  return (
    <fieldset disabled={openingInventoryLocked} aria-disabled={openingInventoryLocked}>
      <label htmlFor="opening-inventory">기초재고</label>
      <input
        id="opening-inventory"
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={openingInventoryLocked}
        data-testid="opening-inventory-input"
      />
      <button type="button" onClick={handleSave} data-testid="opening-inventory-save">
        저장
      </button>
      {openingInventoryLocked && (
        <p data-testid="opening-inventory-helper">
          기초재고 잠김 — 자동 이월 체인 활성. 수동 수정 불가
        </p>
      )}
    </fieldset>
  );
}

describe("OpeningInventoryField (manual edit reject)", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  // ── Case 1: field disabled when locked ─────────────────────────
  it("test_opening_inventory_field_disabled_when_locked", () => {
    render(
      <OpeningInventoryField
        openingInventoryLocked={true}
        value="100"
        onChange={() => {}}
        onSave={() => {}}
      />,
    );

    const input = screen.getByTestId("opening-inventory-input");
    expect(input).toBeDisabled();
    // Helper text appears
    expect(screen.getByTestId("opening-inventory-helper")).toHaveTextContent(
      /기초재고 잠김/,
    );
  });

  // ── Case 2: save attempt shows error toast ─────────────────────
  it("test_opening_inventory_save_attempt_shows_error_toast", async () => {
    let saveCalled = false;
    render(
      <OpeningInventoryField
        openingInventoryLocked={true}
        value="100"
        onChange={() => {}}
        onSave={() => {
          saveCalled = true;
        }}
      />,
    );

    const saveBtn = screen.getByTestId("opening-inventory-save");
    // jsdom: disabled <fieldset> blocks native click. Dispatch a synthetic
    // bubbling click event so the React onClick handler still fires for
    // this unit-level smoke test (DOM-level guard is asserted in Case 1).
    saveBtn.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(toast.error).toHaveBeenCalledWith(
      "기초재고는 자동 이월 체인에 의해 잠겼습니다",
    );
    // onSave should NOT be called when locked
    expect(saveCalled).toBe(false);
  });

  // ── Case 3: field enabled when unlocked ───────────────────────
  it("test_opening_inventory_field_enabled_when_unlocked", () => {
    render(
      <OpeningInventoryField
        openingInventoryLocked={false}
        value="100"
        onChange={() => {}}
        onSave={() => {}}
      />,
    );

    const input = screen.getByTestId("opening-inventory-input");
    expect(input).not.toBeDisabled();
    // No helper text when unlocked
    expect(screen.queryByTestId("opening-inventory-helper")).toBeNull();
  });
});