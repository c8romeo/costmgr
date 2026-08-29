/**
 * apps/web/lib/insight-cache.ts — Story 10.2 (Three-Insight Cache Policy) TS mirror.
 *
 * Sprint 10.5 (cj-style Epic 10 carry-over 14번째 진입점 = cj-style 38번째 epic 연속)
 * — A38 frontend test debt dedicated sprint T2 wire (D-10-2-DEFER-4 해소).
 *
 * AD-15 cross-language parity SSOT: this file mirrors the Python schema
 * (`apps/api/modules/m10_ai/schemas.py` "Story 10.2 EXTENSION" section) and
 * the kernel (`packages/services/m10_ai/insight_cache_kernel.py`) verbatim.
 *
 * AD-7 verbatim bind: 10-2 wire 진입 시점에 all 3 default insights are
 * `source_kind='auto_analysis'`. `source_kind='ai_reference'` 추가는
 * Story 10.3 wire 진입 시점에 detailed wire (badge separation).
 *
 * AD-25 verbatim bind: cache key shape = (tenant_id, period_key, calculation_result_hash).
 *
 * Test debt (A38 — D-10-2-DEFER-4 해소): parity + mount tests live in
 * `apps/web/__tests__/lib/insight-cache-parity.test.ts` + component test.
 */

import { ApiError } from "./api-client";

// ── SSOT mirror — Python `apps.api.modules.m10_ai.schemas` Story 10.2 EXTENSION ──

export type InsightKind =
  | "cost_reduction_candidate"
  | "anomaly_pattern"
  | "forecast";

export type SourceKind = "auto_analysis" | "ai_reference";

export const INSIGHT_KIND_VALUES = [
  "cost_reduction_candidate",
  "anomaly_pattern",
  "forecast",
] as const;

export const SOURCE_KIND_VALUES = [
  "auto_analysis",
  "ai_reference",
] as const;

export interface InsightEntry {
  insight_kind: InsightKind;
  question: string;
  answer: string;
  source_kind: SourceKind;
  evidence_ref: string | null;
  generated_at: string;
}

export interface InsightListResponse {
  status: "success";
  insights: InsightEntry[];
  period_key: string;
  calculation_result_hash: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  hit_count: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  miss_count: number;
}

export interface InsightCacheError {
  error_code:
    | "AI_PIPA_CONSENT_MISSING"
    | "INSIGHT_CACHE_KEY_ERROR"
    | "INSIGHT_COLD_COMPUTE_TIMEOUT"
    | "AI_INSIGHT_CACHE_CONTAMINATION";
  message_ko: string;
  details: Record<string, unknown>;
  trace_id: string;
}

export type InsightEnvelope = InsightListResponse | {
  status: "error";
  error_code: InsightCacheError["error_code"];
  message_ko: string;
  details: Record<string, unknown>;
  trace_id: string;
};

// ── AD-25 cache key helper (3-tuple verbatim) ─────────────────────

export function composeInsightCacheKey(
  tenantId: string,
  periodKey: string,
  calculationResultHash: string,
): string {
  return `${tenantId}::${periodKey}::${calculationResultHash}`;
}

// ── HTTP wire ─────────────────────────────────────────────────────

const INSIGHTS_PATH = "/api/v1/ai/insights";
const INSIGHTS_TIMEOUT_MS = 30_000;

function isApiErrorPayload(v: unknown): v is {
  code: string;
  message_ko: string;
  details: Record<string, unknown>;
  trace_id: string;
} {
  if (typeof v !== "object" || v === null) return false;
  const r = v as Record<string, unknown>;
  return (
    typeof r.code === "string" &&
    typeof r.message_ko === "string" &&
    typeof r.details === "object" &&
    r.details !== null &&
    typeof r.trace_id === "string"
  );
}

async function parseJsonSafe(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return { __non_json__: true };
  }
}

/**
 * GET /api/v1/ai/insights — Story 10.2 AD-25 verbatim three-insight cache lookup.
 *
 * Cache key = (tenant_id, period_key, calculation_result_hash) — mirrored
 * by `compose_insight_cache_key` in `packages/services/m10_ai/insight_cache_kernel.py`.
 *
 * Returns discriminated union `InsightEnvelope`. Callers MUST switch on
 * `error_code` or check the `insights` array presence.
 */
export async function fetchInsightCache(
  params: { period_key: string; calculation_result_hash: string },
  accessToken?: string,
): Promise<InsightEnvelope> {
  const qs = new URLSearchParams({
    period_key: params.period_key,
    calculation_result_hash: params.calculation_result_hash,
  });
  const url = `${INSIGHTS_PATH}?${qs.toString()}`;

  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const controller = new AbortController();
  const timer = setTimeout(
    () =>
      controller.abort(
        new DOMException("Request timeout", "TimeoutError"),
      ),
    INSIGHTS_TIMEOUT_MS,
  );

  try {
    const res = await fetch(url, {
      method: "GET",
      headers,
      credentials: accessToken ? "omit" : "same-origin",
      signal: controller.signal,
    });

    const payload = await parseJsonSafe(res);

    if (!res.ok) {
      if (isApiErrorPayload(payload)) {
        throw new ApiError(res.status, payload);
      }
      const traceId = res.headers.get("X-Trace-Id") ?? "";
      throw new ApiError(res.status, {
        code: "UNPARSEABLE_RESPONSE",
        message_ko: `서버 응답을 해석할 수 없습니다 (HTTP ${res.status})`,
        details: { raw: String(payload) },
        trace_id: traceId,
      });
    }

    return payload as InsightEnvelope;
  } finally {
    clearTimeout(timer);
  }
}

export const INSIGHT_CACHE_ERROR_MESSAGE_KO: Readonly<
  Record<InsightCacheError["error_code"], string>
> = {
  AI_PIPA_CONSENT_MISSING:
    "개인정보 처리 동의가 필요합니다. 설정에서 동의해 주세요.",
  INSIGHT_CACHE_KEY_ERROR: "캐시 키 형식이 올바르지 않습니다 (period_key/해시)",
  INSIGHT_COLD_COMPUTE_TIMEOUT:
    "콜드 컴퓨트 시간 초과 (NFR11 P95 ≤ 30s)",
  AI_INSIGHT_CACHE_CONTAMINATION:
    "캐시 채널 오염 감지 — tenant/period 격리 위반",
} as const;

export function isInsightListResponse(
  env: InsightEnvelope,
): env is InsightListResponse {
  return (
    typeof env === "object" &&
    env !== null &&
    (env as { status?: unknown }).status === "success"
  );
}
