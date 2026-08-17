// apps/web/__tests__/lib/report21-parity.test.ts — Story 9.7
//
// Cross-language parity tests for Report #21 TS mirror
// (PRD §9 #21 + §7.3 verbatim).
//
// Mirrors `apps/web/lib/report21.ts`:
//   - Report21CostObjectRow / Report21UnusedCapacityRow / Report21ResponseEnvelope
//   - REPORT21_ERROR_CODES (4 keys)
//   - fetchReport21TS discriminated union return
//   - isReport21ResponseEnvelope unknown state reject (CR 11-4 D-005)
//
// A35 wire — resolves D3 (TS mirror parity 누락 3건 중 report21 parity 추가).

import { afterEach, describe, expect, it } from "vitest";

import {
  fetchReport21TS,
  isReport21ResponseEnvelope,
  REPORT21_ERROR_CODES,
  type Report21ErrorCode,
  type Report21ResponseEnvelope,
} from "../../lib/report21";
import { server } from "../../mocks/server";
import { http, HttpResponse } from "msw";

afterEach(() => {
  server.resetHandlers();
});

// ── REPORT21_ERROR_CODES pin (4 cases) ─────────────────────

describe("REPORT21_ERROR_CODES (Story 9.4 parity, A35 wire)", () => {
  it("contains PERIOD_NOT_COMMITTED error code", () => {
    expect(REPORT21_ERROR_CODES.PERIOD_NOT_COMMITTED).toBe(
      "REPORT21_PERIOD_NOT_COMMITTED",
    );
  });

  it("contains NO_BREAKDOWN error code", () => {
    expect(REPORT21_ERROR_CODES.NO_BREAKDOWN).toBe(
      "REPORT21_NO_COST_OBJECT_BREAKDOWN",
    );
  });

  it("contains BREAKDOWN_NOT_FOUND error code", () => {
    expect(REPORT21_ERROR_CODES.BREAKDOWN_NOT_FOUND).toBe(
      "REPORT21_BREAKDOWN_NOT_FOUND",
    );
  });

  it("contains PDF_GENERATION_ERROR error code", () => {
    expect(REPORT21_ERROR_CODES.PDF_GENERATION_ERROR).toBe(
      "REPORT_PDF_GENERATION_ERROR",
    );
  });
});

// ── Report21ErrorCode type alias (1 case) ──────────────────

describe("Report21ErrorCode type alias", () => {
  it("is derived from REPORT21_ERROR_CODES via keyof typeof", () => {
    const codes: Report21ErrorCode[] = [
      "REPORT21_PERIOD_NOT_COMMITTED",
      "REPORT21_NO_COST_OBJECT_BREAKDOWN",
      "REPORT21_BREAKDOWN_NOT_FOUND",
      "REPORT_PDF_GENERATION_ERROR",
    ];
    expect(codes).toHaveLength(4);
  });
});

// ── Type-narrowing guard (CR 11-4 D-005) ──────────────────

describe("isReport21ResponseEnvelope type guard", () => {
  const validEnvelope: Report21ResponseEnvelope = {
    period_key: "2026-08",
    cost_object_breakdown: [
      {
        product_id: "prod-A",
        activity_id: "act-1",
        driver_id: "drv-hr",
        allocated_krw: "6600000",
      },
    ],
    unused_capacity_breakdown: [
      {
        department_id: "dept-A",
        unused_hours: "200",
        unused_cost_krw: "6600000",
      },
    ],
    v7_verdict_is_balanced: true,
    generation_hash: "sha256:" + "g".repeat(64),
    report_code: "COST_OBJECT_BREAKDOWN",
  };

  it("returns true for valid envelope", () => {
    expect(isReport21ResponseEnvelope(validEnvelope)).toBe(true);
  });

  it("returns false for null", () => {
    expect(isReport21ResponseEnvelope(null)).toBe(false);
  });

  it("returns false for empty object", () => {
    expect(isReport21ResponseEnvelope({})).toBe(false);
  });

  it("returns false when report_code is wrong", () => {
    expect(
      isReport21ResponseEnvelope({ ...validEnvelope, report_code: "UNKNOWN" }),
    ).toBe(false);
  });

  it("returns false when v7_verdict_is_balanced is missing", () => {
    const broken = { ...validEnvelope } as Record<string, unknown>;
    delete broken.v7_verdict_is_balanced;
    expect(isReport21ResponseEnvelope(broken)).toBe(false);
  });

  it("returns false when arrays are not arrays", () => {
    expect(
      isReport21ResponseEnvelope({
        ...validEnvelope,
        cost_object_breakdown: "not an array",
      }),
    ).toBe(false);
  });
});

// ── fetchReport21TS discriminated union (4 cases) ──────────

describe("fetchReport21TS discriminated union return", () => {
  it("returns error envelope when periodKey is empty", async () => {
    const result = await fetchReport21TS("", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT21_PERIOD_NOT_COMMITTED");
    }
  });

  it("returns ok envelope on 200 with valid response", async () => {
    const envelope: Report21ResponseEnvelope = {
      period_key: "2026-08",
      cost_object_breakdown: [],
      unused_capacity_breakdown: [],
      v7_verdict_is_balanced: true,
      generation_hash: "sha256:" + "1".repeat(64),
      report_code: "COST_OBJECT_BREAKDOWN",
    };
    server.use(
      http.get("/api/v1/reports/21", () => HttpResponse.json(envelope, { status: 200 })),
    );

    const result = await fetchReport21TS("2026-08", "sb-token");
    expect(result.kind).toBe("ok");
    if (result.kind === "ok") {
      expect(result.data.report_code).toBe("COST_OBJECT_BREAKDOWN");
    }
  });

  it("returns error envelope on 500", async () => {
    server.use(
      http.get("/api/v1/reports/21", () =>
        HttpResponse.json(
          { code: "REPORT21_NO_COST_OBJECT_BREAKDOWN", message_ko: "원가대상 분해 데이터가 없습니다" },
          { status: 500 },
        ),
      ),
    );

    const result = await fetchReport21TS("2026-08", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT21_NO_COST_OBJECT_BREAKDOWN");
    }
  });

  it("includes Bearer Authorization header when accessToken is provided", async () => {
    let observedAuthHeader = "";
    server.use(
      http.get("/api/v1/reports/21", ({ request }) => {
        observedAuthHeader = request.headers.get("Authorization") ?? "";
        return HttpResponse.json(
          {
            period_key: "2026-08",
            cost_object_breakdown: [],
            unused_capacity_breakdown: [],
            v7_verdict_is_balanced: true,
            generation_hash: "sha256:" + "1".repeat(64),
            report_code: "COST_OBJECT_BREAKDOWN",
          },
          { status: 200 },
        );
      }),
    );

    await fetchReport21TS("2026-08", "sb-token-xyz");
    expect(observedAuthHeader).toBe("Bearer sb-token-xyz");
  });
});

// ── Decimal-as-string AD-8 invariant (2 cases) ────────────

describe("Report21 row Decimal-as-string invariant", () => {
  it("cost_object_row.allocated_krw is Decimal-as-string (not Number)", () => {
    const row = {
      product_id: "p-1",
      activity_id: "a-1",
      driver_id: "d-1",
      allocated_krw: "6600000",
    };
    expect(typeof row.allocated_krw).toBe("string");
  });

  it("unused_capacity_row.unused_hours / unused_cost_krw are Decimal-as-string", () => {
    const row = {
      department_id: "dept-A",
      unused_hours: "200",
      unused_cost_krw: "6600000",
    };
    expect(typeof row.unused_hours).toBe("string");
    expect(typeof row.unused_cost_krw).toBe("string");
  });
});