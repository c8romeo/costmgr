/**
 * apps/web/__tests__/app/api/health/phase-4-vercel-health.test.ts
 * — Vercel Edge health route validation.
 *
 * Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.4 (frontend side).
 * Edge runtime + force-dynamic + build SHA + region + timestamp.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

describe("phase-4 /api/health route handler", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  describe("runtime configuration", () => {
    it("declares runtime = 'edge'", async () => {
      const mod = await import("@/app/api/health/route");
      expect(mod.runtime).toBe("edge");
    });

    it("declares dynamic = 'force-dynamic'", async () => {
      const mod = await import("@/app/api/health/route");
      expect(mod.dynamic).toBe("force-dynamic");
    });
  });

  describe("GET /api/health response envelope", () => {
    it("returns status: 'healthy'", async () => {
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      const json = await response.json();
      expect(json.status).toBe("healthy");
    });

    it("returns a build field from NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA", async () => {
      process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA = "abc123def456";
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      const json = await response.json();
      expect(json.build).toBe("abc123def456");
    });

    it("returns a region field from NEXT_PUBLIC_VERCEL_REGION", async () => {
      process.env.NEXT_PUBLIC_VERCEL_REGION = "icn1";
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      const json = await response.json();
      expect(json.region).toBe("icn1");
    });

    it("returns an ISO-8601 timestamp", async () => {
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      const json = await response.json();
      expect(typeof json.timestamp).toBe("string");
      // ISO-8601: YYYY-MM-DDTHH:MM:SS.sssZ
      expect(json.timestamp).toMatch(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/,
      );
    });

    it("returns 200 status code", async () => {
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      expect(response.status).toBe(200);
    });

    it("returns application/json content type", async () => {
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      expect(response.headers.get("content-type")).toMatch(
        /application\/json/,
      );
    });

    it("omits build field when NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA is unset", async () => {
      delete process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA;
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      const json = await response.json();
      expect(json.build).toBeNull();
    });

    it("defaults region to null when NEXT_PUBLIC_VERCEL_REGION is unset", async () => {
      delete process.env.NEXT_PUBLIC_VERCEL_REGION;
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      const json = await response.json();
      expect(json.region).toBeNull();
    });
  });

  describe("response shape contract (D-14 typed envelope)", () => {
    it("envelope contains exactly the documented keys", async () => {
      process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA = "abc123";
      process.env.NEXT_PUBLIC_VERCEL_REGION = "icn1";
      const { GET } = await import("@/app/api/health/route");
      const response = await GET();
      const json = await response.json();
      const keys = Object.keys(json).sort();
      expect(keys).toEqual(["build", "region", "status", "timestamp"]);
    });
  });
});