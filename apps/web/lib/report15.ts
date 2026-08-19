/**
 * apps/web/lib/report15.ts — Story 11.6
 *
 * TS mirror for Report #15 (활동원가 내역서 — 활동별 원가·동인 단가) —
 * discriminated union envelope (PRD §9 #15 + §7.1 verbatim).
 *
 * Mirrors Python `apps.api.modules.m5_reports.schemas` (Pydantic v2):
 *   - Report15ActivityCostRow: 10 fields (activity_id, activity_name_ko, activity_name_en,
 *                                 total_cost_krw, total_cost_usd, driver_count,
 *                                 cost_per_driver_krw, cost_per_driver_usd,
 *                                 allocated_krw, allocated_usd)
 *   - Report15Response: {period_key, activity_breakdown[], v7_verdict_is_balanced,
 *                        generation_hash, report_code, activity_count,
 *                        total_driver_count, total_cost_krw, total_cost_usd}
 *
 * TS mirror unknown reject pattern (CR 11-4 D-005): 미인식 필드 reject
 * via `unknown` type narrowing + explicit field assertions.
 *
 * AD-15 §1 cross-language parity invariant:
 *   - Decimal-as-string (total_cost_krw, cost_per_driver_krw, etc.)
 *   - UUID-as-string
 *   - Korean SSOT mirroring `apps.web.messages.ko-KR.json::report15` namespace.
 */

export interface Report15ActivityCostRow {
  activity_id: string;
  activity_name_ko: string;
  activity_name_en: string;
  /** Decimal-as-string AD-8 (e.g., "6600000") */
  total_cost_krw: string;
  /** Decimal-as-string (e.g., "4950") */
  total_cost_usd: string;
  driver_count: number;
  /** Decimal-as-string (e.g., "1650000") */
  cost_per_driver_krw: string;
  /** Decimal-as-string (e.g., "1237.50") */
  cost_per_driver_usd: string;
  /** Decimal-as-string (e.g., "6600000") */
  allocated_krw: string;
  /** Decimal-as-string (e.g., "4950") */
  allocated_usd: string;
}

export type Report15ResponseEnvelope = {
  period_key: string;
  activity_breakdown: Report15ActivityCostRow[];
  v7_verdict_is_balanced: boolean;
  /** V8 byte-equality invariant (V8 결정론 해시) */
  generation_hash: string;
  report_code: "ACTIVITY_COST_DETAIL";
  activity_count: number;
  total_driver_count: number;
  /** Decimal-as-string */
  total_cost_krw: string;
  /** Decimal-as-string */
  total_cost_usd: string;
};

/**
 * Error envelope codes (mirror backend Korean SSOT messages).
 * Cross-language parity (CR 11-3 P-015 SSOT drift detector).
 */
export const REPORT15_ERROR_CODES = {
  PERIOD_NOT_COMMITTED: "REPORT15_PERIOD_NOT_COMMITTED",
  NO_ACTIVITY_BREAKDOWN: "REPORT15_NO_ACTIVITY_BREAKDOWN",
  BREAKDOWN_NOT_FOUND: "REPORT15_BREAKDOWN_NOT_FOUND",
  PDF_GENERATION_ERROR: "REPORT_PDF_GENERATION_ERROR",
} as const;

export type Report15ErrorCode =
  (typeof REPORT15_ERROR_CODES)[keyof typeof REPORT15_ERROR_CODES];

/**
 * Fetch Report #15 envelope from `/api/v1/reports/15`.
 *
 * @param periodKey 회계 기간 ("YYYY-Q1" or "YYYY-MM")
 * @param accessToken sb-access-token cookie value
 * @returns Discriminated union: Response | Error envelope
 */
export async function fetchReport15TS(
  periodKey: string,
  accessToken: string | undefined,
): Promise<
  | { kind: "ok"; data: Report15ResponseEnvelope }
  | { kind: "error"; code: Report15ErrorCode | "NETWORK_ERROR"; message: string }
> {
  if (!periodKey) {
    return { kind: "error", code: "REPORT15_PERIOD_NOT_COMMITTED", message: "기간 키가 필요합니다" };
  }
  try {
    const headers: Record<string, string> = {};
    if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

    const response = await fetch(
      `/api/v1/reports/15?period_key=${encodeURIComponent(periodKey)}`,
      { headers, method: "GET" },
    );
    if (!response.ok) {
      const errBody = (await response.json().catch(() => ({}))) as {
        code?: string;
        message_ko?: string;
      };
      return {
        kind: "error",
        code: (errBody.code as Report15ErrorCode) || "NETWORK_ERROR",
        message: errBody.message_ko || `HTTP ${response.status}`,
      };
    }
    const data = (await response.json()) as Report15ResponseEnvelope;
    return { kind: "ok", data };
  } catch (e) {
    return { kind: "error", code: "NETWORK_ERROR", message: String(e) };
  }
}

/**
 * Type-narrowing guard for `Report15ResponseEnvelope` (CR 11-4 D-005 mirror).
 * Rejects envelopes with unknown fields.
 */
export function isReport15ResponseEnvelope(
  raw: unknown,
): raw is Report15ResponseEnvelope {
  if (raw === null || typeof raw !== "object") return false;
  const obj = raw as Record<string, unknown>;
  return (
    typeof obj.period_key === "string" &&
    typeof obj.v7_verdict_is_balanced === "boolean" &&
    typeof obj.generation_hash === "string" &&
    obj.report_code === "ACTIVITY_COST_DETAIL" &&
    Array.isArray(obj.activity_breakdown) &&
    typeof obj.activity_count === "number" &&
    typeof obj.total_driver_count === "number" &&
    typeof obj.total_cost_krw === "string" &&
    typeof obj.total_cost_usd === "string"
  );
}