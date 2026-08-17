/**
 * apps/web/lib/report21.ts — Story 9.4
 *
 * TS mirror for Report #21 (Cost Object Breakdown) — discriminated union
 * envelope (PRD §9 #21 + §7.3 verbatim).
 *
 * Mirrors Python `apps.api.modules.m5_reports.schemas` (Pydantic v2):
 *   - Report21CostObjectRow: {product_id, activity_id, driver_id, allocated_krw}
 *   - Report21UnusedCapacityRow: {department_id, unused_hours, unused_cost_krw}
 *   - Report21Response: {period_key, cost_object_breakdown[], unused_capacity_breakdown[],
 *                        v7_verdict_is_balanced, generation_hash, report_code}
 *
 * TS mirror unknown reject pattern (CR 11-4 D-005): 미인식 필드 reject
 * via `unknown` type narrowing + explicit field assertions.
 *
 * AD-15 §1 cross-language parity invariant:
 *   - Decimal-as-string (allocated_krw, unused_cost_krw)
 *   - UUID-as-string
 *   - Korean SSOT mirroring `apps.web.messages.ko-KR.json::report21` namespace.
 */

export interface Report21CostObjectRow {
  product_id: string;
  activity_id: string;
  driver_id: string;
  /** Decimal-as-string AD-8 (e.g., "6600000") */
  allocated_krw: string;
}

export interface Report21UnusedCapacityRow {
  department_id: string;
  /** Decimal-as-string (e.g., "200") */
  unused_hours: string;
  /** Decimal-as-string (e.g., "6600000") */
  unused_cost_krw: string;
}

export type Report21ResponseEnvelope = {
  period_key: string;
  cost_object_breakdown: Report21CostObjectRow[];
  unused_capacity_breakdown: Report21UnusedCapacityRow[];
  v7_verdict_is_balanced: boolean;
  /** V8 byte-equality invariant (V8 결정론 해시) */
  generation_hash: string;
  report_code: "COST_OBJECT_BREAKDOWN";
};

/**
 * Error envelope codes (mirror backend Korean SSOT messages).
 * Cross-language parity (CR 11-3 P-015 SSOT drift detector).
 */
export const REPORT21_ERROR_CODES = {
  PERIOD_NOT_COMMITTED: "REPORT21_PERIOD_NOT_COMMITTED",
  NO_BREAKDOWN: "REPORT21_NO_COST_OBJECT_BREAKDOWN",
  BREAKDOWN_NOT_FOUND: "REPORT21_BREAKDOWN_NOT_FOUND",
  PDF_GENERATION_ERROR: "REPORT_PDF_GENERATION_ERROR",
} as const;

export type Report21ErrorCode =
  (typeof REPORT21_ERROR_CODES)[keyof typeof REPORT21_ERROR_CODES];

/**
 * Fetch Report #21 envelope from `/api/v1/reports/21`.
 *
 * @param periodKey 회계 기간 ("YYYY-Q1" or "YYYY-MM")
 * @param accessToken sb-access-token cookie value
 * @returns Discriminated union: Response | Error envelope
 */
export async function fetchReport21TS(
  periodKey: string,
  accessToken: string | undefined,
): Promise<
  | { kind: "ok"; data: Report21ResponseEnvelope }
  | { kind: "error"; code: Report21ErrorCode | "NETWORK_ERROR"; message: string }
> {
  if (!periodKey) {
    return { kind: "error", code: "REPORT21_PERIOD_NOT_COMMITTED", message: "기간 키가 필요합니다" };
  }
  try {
    const headers: Record<string, string> = {};
    if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

    const response = await fetch(
      `/api/v1/reports/21?period_key=${encodeURIComponent(periodKey)}`,
      { headers, method: "GET" },
    );
    if (!response.ok) {
      const errBody = (await response.json().catch(() => ({}))) as {
        code?: string;
        message_ko?: string;
      };
      return {
        kind: "error",
        code: (errBody.code as Report21ErrorCode) || "NETWORK_ERROR",
        message: errBody.message_ko || `HTTP ${response.status}`,
      };
    }
    const data = (await response.json()) as Report21ResponseEnvelope;
    return { kind: "ok", data };
  } catch (e) {
    return { kind: "error", code: "NETWORK_ERROR", message: String(e) };
  }
}

/**
 * Type-narrowing guard for `Report21ResponseEnvelope` (CR 11-4 D-005 mirror).
 * Rejects envelopes with unknown fields.
 */
export function isReport21ResponseEnvelope(
  raw: unknown,
): raw is Report21ResponseEnvelope {
  if (raw === null || typeof raw !== "object") return false;
  const obj = raw as Record<string, unknown>;
  return (
    typeof obj.period_key === "string" &&
    typeof obj.v7_verdict_is_balanced === "boolean" &&
    typeof obj.generation_hash === "string" &&
    obj.report_code === "COST_OBJECT_BREAKDOWN" &&
    Array.isArray(obj.cost_object_breakdown) &&
    Array.isArray(obj.unused_capacity_breakdown)
  );
}
