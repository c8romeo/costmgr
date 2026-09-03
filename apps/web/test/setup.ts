// apps/web/test/setup.ts — vitest global setup
// Story 0.5 — T4.3 (AC #4)
//
// Adds jest-dom matchers (toBeInTheDocument / toHaveClass / etc.) and
// starts MSW server for HTTP request interception during component tests.

import "@testing-library/jest-dom/vitest";

import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { server } from "../mocks/server";

// cj-266: Disable OpenTelemetry Browser SDK in test env. The OTLP
// exporter requires an absolute URL; tracing.test.ts exercises
// initBrowserTracing() which would otherwise throw
// "Configuration: Could not parse user-provided export URL".
process.env.NEXT_PUBLIC_OTEL_SDK_DISABLED = "true";

// cj-266: Provide a default useRouter mock for components that call
// next/navigation APIs (SloDashboardPanel, etc.). Vitest does not mount
// the App Router context, so `invariant expected app router to be
// mounted` would otherwise throw on useRouter(). Tests that need a
// different router behavior can override locally via vi.mock.
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
  }),
  redirect: vi.fn(),
}));

// HTMLDialogElement polyfill for jsdom.
// jsdom does not implement HTMLDialogElement.showModal() / close()
// natively. AuditLogDetailModal uses a native <dialog> element; we
// mock the methods so RTL tests can exercise the row-click → modal
// flow without requiring a full browser. Epic 17 T2 (cj-style 83번째).
if (typeof HTMLDialogElement !== "undefined") {
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function showModal(): void {
      this.setAttribute("open", "");
    };
  }
  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function close(): void {
      this.removeAttribute("open");
    };
  }
}

// MSW server lifecycle:
// - beforeAll: start the request interceptor.
// - afterEach: reset any runtime handlers added during tests.
// - afterAll: close the server.
beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
