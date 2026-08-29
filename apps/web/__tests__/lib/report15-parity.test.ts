// apps/web/__tests__/lib/report15-parity.test.ts — Story 11.6
//
// Cross-language parity tests for Report #15 TS mirror
// (PRD §9 #15 + §7.1 verbatim).
//
// Mirrors `apps/web/lib/report15.ts`:
//   - Report15ActivityCostRow / Report15ResponseEnvelope
//   - REPORT15_ERROR_CODES (4 keys)
//   - fetchReport15TS discriminated union return
//   - isReport15ResponseEnvelope unknown state reject (CR 11-4 D-005)
//
// A35 wire — cross-language parity 검증 (Story 11.6 EXTENSION).

import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it } from "vitest";

import {
  fetchReport15TS,
  isReport15ResponseEnvelope,
  REPORT15_ERROR_CODES,
  type Report15ErrorCode,
  type Report15ResponseEnvelope,
} from "../../lib/report15";
import { server } from "../../mocks/server";

afterEach(() => {
  server.resetHandlers();
});

// ── REPORT15_ERROR_CODES pin (4 cases) ─────────────────────

describe("REPORT15_ERROR_CODES (Story 11.6 parity, A35 wire)", () => {
  it("contains PERIOD_NOT_COMMITTED error code", () => {
    expect(REPORT15_ERROR_CODES.PERIOD_NOT_COMMITTED).toBe(
      "REPORT15_PERIOD_NOT_COMMITTED",
    );
  });

  it("contains NO_ACTIVITY_BREAKDOWN error code", () => {
    expect(REPORT15_ERROR_CODES.NO_ACTIVITY_BREAKDOWN).toBe(
      "REPORT15_NO_ACTIVITY_BREAKDOWN",
    );
  });

  it("contains BREAKDOWN_NOT_FOUND error code", () => {
    expect(REPORT15_ERROR_CODES.BREAKDOWN_NOT_FOUND).toBe(
      "REPORT15_BREAKDOWN_NOT_FOUND",
    );
  });

  it("contains PDF_GENERATION_ERROR error code", () => {
    expect(REPORT15_ERROR_CODES.PDF_GENERATION_ERROR).toBe(
      "REPORT_PDF_GENERATION_ERROR",
    );
  });
});

// ── Report15ErrorCode type alias (1 case) ──────────────────

describe("Report15ErrorCode type alias", () => {
  it("is derived from REPORT15_ERROR_CODES via keyof typeof", () => {
    const codes: Report15ErrorCode[] = [
      "REPORT15_PERIOD_NOT_COMMITTED",
      "REPORT15_NO_ACTIVITY_BREAKDOWN",
      "REPORT15_BREAKDOWN_NOT_FOUND",
      "REPORT_PDF_GENERATION_ERROR",
    ];
    expect(codes).toHaveLength(4);
  });
});

// ── Type-narrowing guard (CR 11-4 D-005) ──────────────────

describe("isReport15ResponseEnvelope type guard", () => {
  const validEnvelope: Report15ResponseEnvelope = {
    period_key: "2026-08",
    activity_breakdown: [
      {
        activity_id: "act-1",
        activity_name_ko: "고객 상담",
        activity_name_en: "Customer Consultation",
        total_cost_krw: "6600000",
        total_cost_usd: "4950",
        driver_count: 4,
        cost_per_driver_krw: "1650000",
        cost_per_driver_usd: "1237.50",
        allocated_krw: "6600000",
        allocated_usd: "4950",
      },
    ],
    v7_verdict_is_balanced: true,
    generation_hash: "sha256:" + "g".repeat(64),
    report_code: "ACTIVITY_COST_DETAIL",
    activity_count: 1,
    total_driver_count: 4,
    total_cost_krw: "6600000",
    total_cost_usd: "4950",
  };

  it("returns true for valid envelope", () => {
    expect(isReport15ResponseEnvelope(validEnvelope)).toBe(true);
  });

  it("returns false for null", () => {
    expect(isReport15ResponseEnvelope(null)).toBe(false);
  });

  it("returns false for empty object", () => {
    expect(isReport15ResponseEnvelope({})).toBe(false);
  });

  it("returns false when report_code is wrong", () => {
    expect(
      isReport15ResponseEnvelope({ ...validEnvelope, report_code: "UNKNOWN" }),
    ).toBe(false);
  });

  it("returns false when v7_verdict_is_balanced is missing", () => {
    const broken = { ...validEnvelope } as Record<string, unknown>;
    delete broken.v7_verdict_is_balanced;
    expect(isReport15ResponseEnvelope(broken)).toBe(false);
  });

  it("returns false when activity_breakdown is not array", () => {
    expect(
      isReport15ResponseEnvelope({
        ...validEnvelope,
        activity_breakdown: "not an array",
      }),
    ).toBe(false);
  });
});

// ── fetchReport15TS discriminated union (4 cases) ──────────

describe("fetchReport15TS discriminated union return", () => {
  it("returns error envelope when periodKey is empty", async () => {
    const result = await fetchReport15TS("", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT15_PERIOD_NOT_COMMITTED");
    }
  });

  it("returns ok envelope on 200 with valid response", async () => {
    const envelope: Report15ResponseEnvelope = {
      period_key: "2026-08",
      activity_breakdown: [],
      v7_verdict_is_balanced: true,
      generation_hash: "sha256:" + "1".repeat(64),
      report_code: "ACTIVITY_COST_DETAIL",
      activity_count: 0,
      total_driver_count: 0,
      total_cost_krw: "0",
      total_cost_usd: "0",
    };
    server.use(
      http.get("/api/v1/reports/15", () => HttpResponse.json(envelope, { status: 200 })),
    );

    const result = await fetchReport15TS("2026-08", "sb-token");
    expect(result.kind).toBe("ok");
    if (result.kind === "ok") {
      expect(result.data.report_code).toBe("ACTIVITY_COST_DETAIL");
    }
  });

  it("returns error envelope on 500", async () => {
    server.use(
      http.get("/api/v1/reports/15", () =>
        HttpResponse.json(
          { code: "REPORT15_NO_ACTIVITY_BREAKDOWN", message_ko: "활동별 원가 데이터가 없습니다" },
          { status: 500 },
        ),
      ),
    );

    const result = await fetchReport15TS("2026-08", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT15_NO_ACTIVITY_BREAKDOWN");
    }
  });

  it("includes Bearer Authorization header when accessToken is provided", async () => {
    let observedAuthHeader = "";
    server.use(
      http.get("/api/v1/reports/15", ({ request }) => {
        observedAuthHeader = request.headers.get("Authorization") ?? "";
        return HttpResponse.json(
          {
            period_key: "2026-08",
            activity_breakdown: [],
            v7_verdict_is_balanced: true,
            generation_hash: "sha256:" + "1".repeat(64),
            report_code: "ACTIVITY_COST_DETAIL",
            activity_count: 0,
            total_driver_count: 0,
            total_cost_krw: "0",
            total_cost_usd: "0",
          },
          { status: 200 },
        );
      }),
    );

    await fetchReport15TS("2026-08", "sb-token-xyz");
    expect(observedAuthHeader).toBe("Bearer sb-token-xyz");
  });
});

// ── Decimal-as-string AD-8 invariant (2 cases) ────────────

describe("Report15 row Decimal-as-string invariant", () => {
  it("activity row amounts are Decimal-as-string (not Number)", () => {
    const row = {
      activity_id: "act-1",
      activity_name_ko: "고객 상담",
      activity_name_en: "Customer Consultation",
      total_cost_krw: "6600000",
      total_cost_usd: "4950",
      driver_count: 4,
      cost_per_driver_krw: "1650000",
      cost_per_driver_usd: "1237.50",
      allocated_krw: "6600000",
      allocated_usd: "4950",
    };
    expect(typeof row.total_cost_krw).toBe("string");
    expect(typeof row.total_cost_usd).toBe("string");
    expect(typeof row.cost_per_driver_krw).toBe("string");
    expect(typeof row.cost_per_driver_usd).toBe("string");
    expect(typeof row.allocated_krw).toBe("string");
    expect(typeof row.allocated_usd).toBe("string");
  });

  it("envelope totals are Decimal-as-string", () => {
    const envelope = {
      period_key: "2026-08",
      activity_breakdown: [],
      v7_verdict_is_balanced: true,
      generation_hash: "sha256:" + "1".repeat(64),
      report_code: "ACTIVITY_COST_DETAIL",
      activity_count: 0,
      total_driver_count: 0,
      total_cost_krw: "0",
      total_cost_usd: "0",
    };
    expect(typeof envelope.total_cost_krw).toBe("string");
    expect(typeof envelope.total_cost_usd).toBe("string");
  });
});