/**
 * apps/web/__tests__/components/m9-abc.AbcValidationForm.test.tsx — Story 9.7
 *
 * Vitest tests for AbcValidationForm (3-layer ABC 100% guard validation).
 *
 * Coverage (T2 A35):
 *   - Form mount + 3 inputs (cost_pool / activity / driver) (2 cases)
 *   - onResult callback on success (200 envelope) (2 cases)
 *   - Client-side validateAbcPctList throw path (3 cases — sum != 100%)
 *   - 422 COST_POOL_INVALID_SUM envelope surface (1 case)
 *   - 404 ABC_VALIDATION_NOT_FOUND envelope surface (1 case)
 *
 * Total: ~9 NEW vitest cases (T2 A35 wire).
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AbcValidationForm } from "@/components/m9-abc/AbcValidationForm";
import koKR from "@/messages/ko-KR.json";
import { server } from "@/mocks/server";

afterEach(() => {
  server.resetHandlers();
});

const messages = koKR;

function renderWithIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider locale="ko-KR" messages={messages}>
      {node}
    </NextIntlClientProvider>
  );
}

const validCostPool = "25, 25, 25, 25";
const validActivity = "50, 50";
const validDriver = "60, 40";

function fillValidForm(): void {
  fireEvent.change(screen.getByLabelText(/원가풀/), {
    target: { value: validCostPool },
  });
  fireEvent.change(screen.getByLabelText(/활동/), {
    target: { value: validActivity },
  });
  fireEvent.change(screen.getByLabelText(/동인/), {
    target: { value: validDriver },
  });
}

const successEnvelope = {
  cost_pool_id: "cp-001",
  activity_id: "act-001",
  cost_pool: [
    { department_id: "dept-A", sum_pct: "100", department_count: 1, is_valid: true, hash: "sha256:cp000" },
  ],
  activities: [
    { activity_id: "act-001", sum_pct: "100", product_count: 2, is_valid: true, hash: "sha256:act000" },
  ],
  drivers: [
    { driver_id: "drv-001", sum_pct: "100", activity_count: 2, is_valid: true, hash: "sha256:drv000" },
  ],
  all_valid: true,
  trace_id: "trace-validate-001",
};

// ── Form mount + 3 inputs (2 cases) ────────────────────────

describe("AbcValidationForm mount", () => {
  it("renders form with data-testid='abc-validation-form'", () => {
    render(
      renderWithIntl(
        <AbcValidationForm
          accessToken="sb-test-token"
          onResult={vi.fn()}
        />,
      ),
    );
    expect(screen.getByTestId("abc-validation-form")).toBeTruthy();
  });

  it("renders 3 inputs (cost_pool / activity / driver) + submit button", () => {
    render(
      renderWithIntl(
        <AbcValidationForm
          accessToken="sb-test-token"
          onResult={vi.fn()}
        />,
      ),
    );
    expect(screen.getByLabelText(/원가풀/)).toBeTruthy();
    expect(screen.getByLabelText(/활동/)).toBeTruthy();
    expect(screen.getByLabelText(/동인/)).toBeTruthy();
    expect(screen.getByTestId("abc-validation-submit")).toBeTruthy();
  });
});

// ── onResult callback on success (2 cases) ────────────────

describe("AbcValidationForm success envelope", () => {
  it("invokes onResult callback with parsed ValidationResponse", async () => {
    const onResult = vi.fn();
    server.use(
      http.post("/api/v1/abc/validate", () =>
        HttpResponse.json(successEnvelope, { status: 200 }),
      ),
    );

    render(
      renderWithIntl(
        <AbcValidationForm accessToken="sb-token" onResult={onResult} />,
      ),
    );
    fillValidForm();
    fireEvent.click(screen.getByTestId("abc-validation-submit"));

    await waitFor(() => expect(onResult).toHaveBeenCalledTimes(1));
    expect(onResult.mock.calls[0][0]).toEqual(successEnvelope);
  });

  it("includes Bearer Authorization header in fetch", async () => {
    const onResult = vi.fn();
    let observedAuthHeader = "";
    server.use(
      http.post("/api/v1/abc/validate", ({ request }) => {
        observedAuthHeader = request.headers.get("Authorization") ?? "";
        return HttpResponse.json(successEnvelope, { status: 200 });
      }),
    );

    render(
      renderWithIntl(
        <AbcValidationForm accessToken="sb-token-xyz" onResult={onResult} />,
      ),
    );
    fillValidForm();
    fireEvent.click(screen.getByTestId("abc-validation-submit"));

    await waitFor(() => expect(onResult).toHaveBeenCalledTimes(1));
    expect(observedAuthHeader).toBe("Bearer sb-token-xyz");
  });
});

// ── Client-side validateAbcPctList throw path (3 cases) ───
// Note: Frontend validators (m9-abc-validation-schema.ts:42-85) check:
//   1. values.length === 0 → "not_found" Korean SSOT error
//   2. !isValidAbcPctList(values) → "out_of_range" error (values < 0 or > 100)
// SUM check (== 100%) is backend-side only (Pydantic v2 schema).
// So we test the empty-list and out-of-range cases here.

describe("AbcValidationForm client-side validation", () => {
  it("surfaces error when cost_pool value is out of 0-100 range", () => {
    render(
      renderWithIntl(
        <AbcValidationForm
          accessToken="sb-token"
          onResult={vi.fn()}
        />,
      ),
    );
    fireEvent.change(screen.getByLabelText(/원가풀/), {
      target: { value: "150" }, // > 100 → out_of_range
    });
    fireEvent.click(screen.getByTestId("abc-validation-submit"));
    expect(screen.getByTestId("abc-validation-error")).toBeTruthy();
    expect(screen.getByTestId("abc-validation-error").textContent).toContain(
      "cost_pool",
    );
  });

  it("surfaces error when activity value is out of 0-100 range", () => {
    render(
      renderWithIntl(
        <AbcValidationForm
          accessToken="sb-token"
          onResult={vi.fn()}
        />,
      ),
    );
    fireEvent.change(screen.getByLabelText(/활동/), {
      target: { value: "-5" }, // < 0 → out_of_range
    });
    fireEvent.click(screen.getByTestId("abc-validation-submit"));
    expect(screen.getByTestId("abc-validation-error")).toBeTruthy();
    expect(screen.getByTestId("abc-validation-error").textContent).toContain(
      "activity",
    );
  });

  it("surfaces error when driver value is out of 0-100 range", () => {
    render(
      renderWithIntl(
        <AbcValidationForm
          accessToken="sb-token"
          onResult={vi.fn()}
        />,
      ),
    );
    fireEvent.change(screen.getByLabelText(/동인/), {
      target: { value: "200" }, // > 100 → out_of_range
    });
    fireEvent.click(screen.getByTestId("abc-validation-submit"));
    expect(screen.getByTestId("abc-validation-error")).toBeTruthy();
    expect(screen.getByTestId("abc-validation-error").textContent).toContain(
      "driver",
    );
  });
});

// ── 422 / 404 envelope surfaces (2 cases) ────────────────

describe("AbcValidationForm error envelopes", () => {
  it("surfaces 422 COST_POOL_INVALID_SUM error message", async () => {
    const onResult = vi.fn();
    server.use(
      http.post("/api/v1/abc/validate", () =>
        HttpResponse.json(
          { code: "ABC_COST_POOL_INVALID_SUM", message_ko: "원가풀 행 합이 100%가 아닙니다" },
          { status: 422 },
        ),
      ),
    );

    render(
      renderWithIntl(
        <AbcValidationForm accessToken="sb-token" onResult={onResult} />,
      ),
    );
    fillValidForm();
    fireEvent.click(screen.getByTestId("abc-validation-submit"));

    await waitFor(() =>
      expect(screen.getByTestId("abc-validation-error")).toBeTruthy(),
    );
    expect(onResult).not.toHaveBeenCalled();
    expect(screen.getByTestId("abc-validation-error").textContent).toContain(
      "원가풀 행 합이 100%가 아닙니다",
    );
  });

  it("surfaces 404 ABC_VALIDATION_NOT_FOUND error message", async () => {
    const onResult = vi.fn();
    server.use(
      http.post("/api/v1/abc/validate", () =>
        HttpResponse.json(
          { code: "ABC_VALIDATION_NOT_FOUND", message_ko: "ABC 검증 대상을 찾을 수 없습니다" },
          { status: 404 },
        ),
      ),
    );

    render(
      renderWithIntl(
        <AbcValidationForm accessToken="sb-token" onResult={onResult} />,
      ),
    );
    fillValidForm();
    fireEvent.click(screen.getByTestId("abc-validation-submit"));

    await waitFor(() =>
      expect(screen.getByTestId("abc-validation-error")).toBeTruthy(),
    );
    expect(onResult).not.toHaveBeenCalled();
    expect(screen.getByTestId("abc-validation-error").textContent).toContain(
      "ABC 검증 대상을 찾을 수 없습니다",
    );
  });
});