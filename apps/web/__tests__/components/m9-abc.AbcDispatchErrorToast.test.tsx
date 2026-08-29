/**
 * apps/web/__tests__/components/m9-abc.AbcDispatchErrorToast.test.tsx — Story 9.7
 *
 * Vitest tests for AbcDispatchErrorToast (M9 ABC 422 envelope error surface).
 *
 * Coverage (T2 A35):
 *   - 3 error codes: ABC_EMPTY_DEPARTMENTS / ABC_TOO_MANY_DEPARTMENTS / ABC_DISPATCH_GENERIC_ERROR (4 cases)
 *   - data-error-code attribute (3 cases)
 *   - Korean SSOT label rendering (ko-KR.json fallback + ABC_*_KO SSOT constants) (3 cases)
 *   - dismiss button callback (when onDismiss provided) (2 cases)
 *   - null rendering when errorCode is null (2 cases)
 *
 * Total: ~14 NEW vitest cases (T2 A35 wire).
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import { AbcDispatchErrorToast } from "@/components/m9-abc/AbcDispatchErrorToast";
import koKR from "@/messages/ko-KR.json";


const messages = koKR;

function renderWithIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider locale="ko-KR" messages={messages}>
      {node}
    </NextIntlClientProvider>
  );
}

// ── null rendering (2 cases) ─────────────────────────────────

describe("AbcDispatchErrorToast null rendering", () => {
  it("returns null when errorCode is null", () => {
    const { container } = render(
      renderWithIntl(
        <AbcDispatchErrorToast errorCode={null} onDismiss={vi.fn()} />,
      ),
    );
    expect(container.firstChild).toBeNull();
  });

  it("does not render error container when errorCode is null and onDismiss omitted", () => {
    const { container } = render(
      renderWithIntl(<AbcDispatchErrorToast errorCode={null} />),
    );
    expect(container.firstChild).toBeNull();
  });
});

// ── 3 error codes (4 cases) ──────────────────────────────────

describe("AbcDispatchErrorToast error codes", () => {
  it("renders ABC_EMPTY_DEPARTMENTS error label", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_EMPTY_DEPARTMENTS"
          onDismiss={vi.fn()}
        />,
      ),
    );
    expect(screen.getByTestId("abc-dispatch-error-code")).toBeTruthy();
    // Both codeLabel (i18n) and description (Korean SSOT constant) render
    // the same text — use getAllByText to assert at least one match exists.
    expect(screen.getAllByText(/ABC 부서가 등록되지 않았습니다/).length).toBeGreaterThan(0);
  });

  it("renders ABC_TOO_MANY_DEPARTMENTS error label", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_TOO_MANY_DEPARTMENTS"
          onDismiss={vi.fn()}
        />,
      ),
    );
    expect(
      screen.getAllByText(/ABC 부서 수가 한도를 초과했습니다/).length,
    ).toBeGreaterThan(0);
  });

  it("renders ABC_DISPATCH_GENERIC_ERROR fallback label", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_DISPATCH_GENERIC_ERROR"
          onDismiss={vi.fn()}
        />,
      ),
    );
    expect(screen.getByTestId("abc-dispatch-error-code")).toBeTruthy();
  });

  it("uses errorMessage when provided and code is generic", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_DISPATCH_GENERIC_ERROR"
          errorMessage="Custom error context"
          onDismiss={vi.fn()}
        />,
      ),
    );
    expect(screen.getByText(/Custom error context/)).toBeTruthy();
  });
});

// ── data-error-code attribute (3 cases) ──────────────────────

describe("AbcDispatchErrorToast data-error-code", () => {
  it("renders data-error-code='ABC_EMPTY_DEPARTMENTS'", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_EMPTY_DEPARTMENTS"
          onDismiss={vi.fn()}
        />,
      ),
    );
    expect(
      screen.getByTestId("abc-dispatch-error-toast").getAttribute("data-error-code"),
    ).toBe("ABC_EMPTY_DEPARTMENTS");
  });

  it("renders data-error-code='ABC_TOO_MANY_DEPARTMENTS'", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_TOO_MANY_DEPARTMENTS"
          onDismiss={vi.fn()}
        />,
      ),
    );
    expect(
      screen.getByTestId("abc-dispatch-error-toast").getAttribute("data-error-code"),
    ).toBe("ABC_TOO_MANY_DEPARTMENTS");
  });

  it("renders data-error-code='ABC_DISPATCH_GENERIC_ERROR'", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_DISPATCH_GENERIC_ERROR"
          onDismiss={vi.fn()}
        />,
      ),
    );
    expect(
      screen.getByTestId("abc-dispatch-error-toast").getAttribute("data-error-code"),
    ).toBe("ABC_DISPATCH_GENERIC_ERROR");
  });
});

// ── Korean SSOT labels (3 cases) ────────────────────────────

describe("AbcDispatchErrorToast Korean SSOT", () => {
  it("renders ABC_EMPTY_DEPARTMENTS_KO SSOT constant in description", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_EMPTY_DEPARTMENTS"
          onDismiss={vi.fn()}
        />,
      ),
    );
    const desc = screen.getByTestId("abc-dispatch-error-description");
    expect(desc.textContent).toContain("ABC 부서가 등록되지 않았습니다");
  });

  it("renders ABC_TOO_MANY_DEPARTMENTS_KO SSOT constant in description", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_TOO_MANY_DEPARTMENTS"
          onDismiss={vi.fn()}
        />,
      ),
    );
    const desc = screen.getByTestId("abc-dispatch-error-description");
    expect(desc.textContent).toContain("ABC 부서 수가 한도를 초과했습니다");
  });

  it("uses role='alert' and aria-live='assertive' for accessibility", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_EMPTY_DEPARTMENTS"
          onDismiss={vi.fn()}
        />,
      ),
    );
    const toast = screen.getByTestId("abc-dispatch-error-toast");
    expect(toast.getAttribute("role")).toBe("alert");
    expect(toast.getAttribute("aria-live")).toBe("assertive");
  });
});

// ── dismiss callback (2 cases) ──────────────────────────────

describe("AbcDispatchErrorToast dismiss callback", () => {
  it("invokes onDismiss when dismiss button is clicked", () => {
    const onDismiss = vi.fn();
    render(
      renderWithIntl(
        <AbcDispatchErrorToast
          errorCode="ABC_EMPTY_DEPARTMENTS"
          onDismiss={onDismiss}
        />,
      ),
    );
    fireEvent.click(screen.getByTestId("abc-dispatch-error-dismiss"));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("does not render dismiss button when onDismiss is undefined", () => {
    render(
      renderWithIntl(
        <AbcDispatchErrorToast errorCode="ABC_EMPTY_DEPARTMENTS" />,
      ),
    );
    expect(screen.queryByTestId("abc-dispatch-error-dismiss")).toBeNull();
  });
});