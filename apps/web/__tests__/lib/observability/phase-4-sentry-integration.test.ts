/**
 * apps/web/__tests__/lib/observability/phase-4-sentry-integration.test.ts
 * — Sentry browser observability validation.
 *
 * Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.4 (frontend side).
 * SSR-safe guard + lazy-load + no-op when DSN unset.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock @sentry/nextjs BEFORE importing the Sentry wrapper module so that the
// module-level `initSentry()` call observes a captured mock.
const mockSentryInit = vi.fn();
const mockSentryCaptureException = vi.fn();
const mockSentryCaptureMessage = vi.fn();

vi.mock("@sentry/nextjs", () => ({
  init: (...args: unknown[]) => mockSentryInit(...args),
  captureException: (...args: unknown[]) =>
    mockSentryCaptureException(...args),
  captureMessage: (...args: unknown[]) => mockSentryCaptureMessage(...args),
}));

describe("phase-4 Sentry browser integration", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
    mockSentryInit.mockClear();
    mockSentryCaptureException.mockClear();
    mockSentryCaptureMessage.mockClear();
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  describe("isSentryEnabled()", () => {
    it("returns false when NEXT_PUBLIC_SENTRY_DSN is unset", async () => {
      delete process.env.NEXT_PUBLIC_SENTRY_DSN;
      const mod = await import("@/lib/observability/sentry");
      expect(mod.isSentryEnabled()).toBe(false);
    });

    it("returns false when NEXT_PUBLIC_SENTRY_DSN is empty string", async () => {
      process.env.NEXT_PUBLIC_SENTRY_DSN = "";
      const mod = await import("@/lib/observability/sentry");
      expect(mod.isSentryEnabled()).toBe(false);
    });

    it("returns true when NEXT_PUBLIC_SENTRY_DSN is set", async () => {
      process.env.NEXT_PUBLIC_SENTRY_DSN = "https://examplePublicKey@o0.ingest.sentry.io/0";
      const mod = await import("@/lib/observability/sentry");
      expect(mod.isSentryEnabled()).toBe(true);
    });
  });

  describe("initSentry()", () => {
    it("is a no-op when NEXT_PUBLIC_SENTRY_DSN is unset (SSR-safe)", async () => {
      delete process.env.NEXT_PUBLIC_SENTRY_DSN;
      const mod = await import("@/lib/observability/sentry");
      await expect(mod.initSentry()).resolves.toBe(false);
      expect(mockSentryInit).not.toHaveBeenCalled();
    });

    it("is safe to call when window is undefined (Edge/SSR)", async () => {
      process.env.NEXT_PUBLIC_SENTRY_DSN = "https://examplePublicKey@o0.ingest.sentry.io/0";
      // Save original window and delete it to simulate SSR.
      const originalWindow = globalThis.window;
      // @ts-expect-error - we deliberately remove window for this test.
      delete globalThis.window;
      try {
        const mod = await import("@/lib/observability/sentry");
        // Module-level guard means no Sentry init when window is undefined.
        await expect(mod.initSentry()).resolves.toBe(false);
      } finally {
        globalThis.window = originalWindow;
      }
    });

    it("initializes Sentry with tracesSampleRate=0.1 when DSN present", async () => {
      process.env.NEXT_PUBLIC_SENTRY_DSN = "https://examplePublicKey@o0.ingest.sentry.io/0";
      // Ensure window exists.
      (globalThis as { window?: unknown }).window = globalThis.window ?? {};
      const mod = await import("@/lib/observability/sentry");
      await mod.initSentry();
      expect(mockSentryInit).toHaveBeenCalledTimes(1);
      const initArg = mockSentryInit.mock.calls[0][0] as { tracesSampleRate?: number };
      expect(initArg.tracesSampleRate).toBe(0.1);
    });

    it("disables session replays (replaysSessionSampleRate=0)", async () => {
      process.env.NEXT_PUBLIC_SENTRY_DSN = "https://examplePublicKey@o0.ingest.sentry.io/0";
      (globalThis as { window?: unknown }).window = globalThis.window ?? {};
      const mod = await import("@/lib/observability/sentry");
      await mod.initSentry();
      const initArg = mockSentryInit.mock.calls[0][0] as {
        replaysSessionSampleRate?: number;
      };
      expect(initArg.replaysSessionSampleRate).toBe(0);
    });

    it("never sends default PII (sendDefaultPii=false)", async () => {
      process.env.NEXT_PUBLIC_SENTRY_DSN = "https://examplePublicKey@o0.ingest.sentry.io/0";
      (globalThis as { window?: unknown }).window = globalThis.window ?? {};
      const mod = await import("@/lib/observability/sentry");
      await mod.initSentry();
      const initArg = mockSentryInit.mock.calls[0][0] as { sendDefaultPii?: boolean };
      expect(initArg.sendDefaultPii).toBe(false);
    });
  });

  describe("captureException() / captureMessage()", () => {
    it("captureException never throws when Sentry is not initialized", async () => {
      delete process.env.NEXT_PUBLIC_SENTRY_DSN;
      const mod = await import("@/lib/observability/sentry");
      expect(() => mod.captureException(new Error("boom"))).not.toThrow();
    });

    it("captureMessage never throws when Sentry is not initialized", async () => {
      delete process.env.NEXT_PUBLIC_SENTRY_DSN;
      const mod = await import("@/lib/observability/sentry");
      expect(() => mod.captureMessage("info")).not.toThrow();
    });
  });
});