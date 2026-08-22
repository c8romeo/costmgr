/**
 * apps/web/__tests__/api/phase-5-multi-region-health.test.ts — Next.js multi-region health route test.
 *
 * Phase 5 (cj-style 75번째 wire) — AC #5.1~#5.4 verbatim + CR 12-5 D-PARITY-01 inversion.
 * Verifies the TypeScript Next.js Edge Runtime route handler at
 * apps/web/app/api/health/multi-region/route.ts mirrors the Python backend
 * /api/v1/health/multi-region envelope.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";

describe("Multi-Region Health Route (Phase 5)", () => {
  beforeEach(() => {
    vi.resetModules();
    process.env.SUPABASE_URL = "https://test.supabase.co";
    process.env.SUPABASE_ANON_KEY = "test-anon-key";
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test.costmgr.example.com";
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("route configuration", () => {
    it("uses edge runtime", async () => {
      const routeModule = await import(
        "@/app/api/health/multi-region/route"
      );
      expect(routeModule.runtime).toBe("edge");
    });

    it("uses force-dynamic to bypass cache", async () => {
      const routeModule = await import(
        "@/app/api/health/multi-region/route"
      );
      expect(routeModule.dynamic).toBe("force-dynamic");
    });

    it("exports GET handler", async () => {
      const routeModule = await import(
        "@/app/api/health/multi-region/route"
      );
      expect(typeof routeModule.GET).toBe("function");
    });
  });

  describe("CR 12-5 D-14 envelope structure", () => {
    it("returns envelope on backend success", async () => {
      const mockResponse = {
        status: "healthy",
        primary: {
          region: "primary_seoul",
          replication_status: "healthy",
          lag_seconds: 12,
          last_wal_received_at: "2026-08-22T10:00:00Z",
        },
        secondary: {
          region: "secondary_tokyo",
          replication_status: "healthy",
          lag_seconds: 8,
          last_wal_received_at: "2026-08-22T10:00:00Z",
        },
        timestamp: "2026-08-22T10:00:01Z",
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      });

      const routeModule = await import(
        "@/app/api/health/multi-region/route"
      );
      const response = await routeModule.GET();
      const data = await response.json();

      expect(data.status).toBe("healthy");
      expect(data.primary.region).toBe("primary_seoul");
      expect(data.secondary.region).toBe("secondary_tokyo");
      expect(typeof data.timestamp).toBe("string");
    });

    it("returns unhealthy envelope on backend failure", async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error("Backend down"));

      const routeModule = await import(
        "@/app/api/health/multi-region/route"
      );
      const response = await routeModule.GET();
      expect(response.status).toBe(503);

      const data = await response.json();
      expect(data.status).toBe("unhealthy");
      expect(data.primary.replication_status).toBe("disconnected");
      expect(data.secondary.replication_status).toBe("disconnected");
      expect(data.primary.region).toBe("primary_seoul");
      expect(data.secondary.region).toBe("secondary_tokyo");
      expect(data.primary.last_wal_received_at).toBeNull();
      expect(data.secondary.last_wal_received_at).toBeNull();
    });

    it("returns unhealthy envelope on backend 5xx", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      });

      const routeModule = await import(
        "@/app/api/health/multi-region/route"
      );
      const response = await routeModule.GET();
      expect(response.status).toBe(503);

      const data = await response.json();
      expect(data.status).toBe("unhealthy");
    });
  });

  describe("CR 12-5 D-PARITY-01 inversion", () => {
    it("TS envelope mirrors Python backend envelope verbatim", async () => {
      // The Python backend envelope has these keys: status, primary,
      // secondary, timestamp. The TS route must return the same keys.
      const requiredKeys = ["status", "primary", "secondary", "timestamp"];
      const mockResponse: Record<string, unknown> = {};
      for (const key of requiredKeys) {
        mockResponse[key] = null;
      }
      mockResponse.status = "healthy";
      mockResponse.primary = {
        region: "primary_seoul",
        replication_status: "healthy",
        lag_seconds: 0,
        last_wal_received_at: null,
      };
      mockResponse.secondary = {
        region: "secondary_tokyo",
        replication_status: "healthy",
        lag_seconds: 0,
        last_wal_received_at: null,
      };
      mockResponse.timestamp = "2026-08-22T10:00:00Z";

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      });

      const routeModule = await import(
        "@/app/api/health/multi-region/route"
      );
      const response = await routeModule.GET();
      const data = await response.json();

      for (const key of requiredKeys) {
        expect(key in data).toBe(true);
      }
    });
  });
});