// apps/web/test/setup.ts — vitest global setup
// Story 0.5 — T4.3 (AC #4)
//
// Adds jest-dom matchers (toBeInTheDocument / toHaveClass / etc.) and
// starts MSW server for HTTP request interception during component tests.

import "@testing-library/jest-dom/vitest";

import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "../mocks/server";

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
