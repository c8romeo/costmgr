/**
 * apps/web/lib/ai-comments.ts — Story 10.3 (AI Reference vs Auto Analysis Badge) TS mirror.
 *
 * Sprint 10.5 (cj-style Epic 10 carry-over 14번째 진입점 = cj-style 38번째 epic 연속)
 * — A38 frontend test debt dedicated sprint T3 wire (D-10-3-DEFER-4 해소).
 *
 * AD-15 cross-language parity SSOT: this file mirrors the Python schema
 * (`apps/api/modules/m10_ai/schemas.py` "Story 10.3 EXTENSION" section).
 *
 * AD-7 verbatim bind (F10.2 (a)~(d)):
 *   (a) source_kind='auto_analysis' → 파란 배지 '📊 자동 분석'
 *       source_kind='ai_reference'  → 보라 배지 '🤖 AI 참고(검증 필요)'
 *   (b) source_kind 미매칭 value → strict reject + 1행 counter increment
 *   (c) auto_analysis 의견 수정 시도 → denied + 동일 카운터 추적 (SM-3a)
 *   (d) 1-line ko-KR 메시지로 reject ("분석 의견 출처가 불분명합니다")
 *
 * AD-25 verbatim bind: cache key shape = (tenant_id, period_key, calculation_result_hash).
 */

import { ApiError } from "./api-client";

// ── SSOT mirror — Python `apps.api.modules.m10_ai.schemas` Story 10.3 EXTENSION ──

export type AICommentKind =
  | "cost_reduction_candidate"
  | "anomaly_pattern"
  | "forecast"
  | "risk_warning"
  | "industry_benchmark";

export type SourceKind = "auto_analysis" | "ai_reference";

export const AI_COMMENT_KIND_VALUES: ReadonlyArray<AICommentKind> = [
  "cost_reduction_candidate",
  "anomaly_pattern",
  "forecast",
  "risk_warning",
  "industry_benchmark",
] as const;

export const SOURCE_KIND_VALUES: ReadonlyArray<SourceKind> = [
  "auto_analysis",
  "ai_reference",
] as const;

export const AI_COMMENT_SOURCE_KIND_WARNING = "AI_COMMENT_SOURCE_KIND_WARNING";

export interface AICommentEntry {
  comment_id: string;
  comment_kind: AICommentKind;
  body_text: string;
  source_kind: SourceKind;
  evidence_ref: string | null;
  generated_at: string;
}

export interface AICommentListResponse {
  status: "success";
  comments: AICommentEntry[];
  period_key: string;
  calculation_result_hash: string;
  hit_count: number;
  miss_count: number;
  counter_total: number;
}

export interface AICommentErrorEnvelope {
  status: "error";
  error_code:
    | "AI_PIPA_CONSENT_MISSING"
    | "AI_COMMENT_SOURCE_KIND_INVALID"
    | "AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS"
    | "AI_COMMENT_SOURCE_KIND_WARNING";
  message_ko: string;
  details: Record<string, unknown>;
  trace_id: string;
}

export type AICommentEnvelope = AICommentListResponse | AICommentErrorEnvelope;

// ── AD-15 parity utilities (frontend read-side) ─────────────────────

export const AI_COMMENT_KIND_LABEL_KO: Readonly<Record<AICommentKind, string>> = {
  cost_reduction_candidate: "비용 절감 후보",
  anomaly_pattern: "이상 패턴",
  forecast: "예측",
  risk_warning: "리스크 경고",
  industry_benchmark: "업종 벤치마크",
} as const;

export function isSourceKind(v: unknown): v is SourceKind {
  return v === "auto_analysis" || v === "ai_reference";
}

export function isAICommentError(
  env: AICommentEnvelope,
): env is AICommentErrorEnvelope {
  return (
    typeof env === "object" &&
    env !== null &&
    (env as { status?: unknown }).status === "error"
  );
}

export function isAICommentListSuccess(
  env: AICommentEnvelope,
): env is AICommentListResponse {
  return (
    typeof env === "object" &&
    env !== null &&
    (env as { status?: unknown }).status === "success"
  );
}

// ── HTTP wire ─────────────────────────────────────────────────────

const COMMENTS_PATH = "/api/v1/ai/comments";
const COMMENTS_TIMEOUT_MS = 30_000;

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
 * GET /api/v1/ai/comments — Story 10.3 AD-15 verbatim AI comment lookup.
 *
 * Returns comments with `source_kind` tag discriminator. Frontend renders
 * the badge based on the source_kind value (F10.2-(a) verbatim).
 *
 * Auto-analysis comments (source_kind='auto_analysis') are IMMUTABLE —
 * the frontend MUST NOT provide a modify/edit path for them (F10.2-(c)).
 */
export async function fetchAIComments(
  params: { period_key: string; calculation_result_hash: string },
  accessToken?: string,
): Promise<AICommentEnvelope> {
  const qs = new URLSearchParams({
    period_key: params.period_key,
    calculation_result_hash: params.calculation_result_hash,
  });
  const url = `${COMMENTS_PATH}?${qs.toString()}`;

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
    COMMENTS_TIMEOUT_MS,
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

    return payload as AICommentEnvelope;
  } finally {
    clearTimeout(timer);
  }
}

export const AI_COMMENT_ERROR_MESSAGE_KO: Readonly<
  Record<AICommentErrorEnvelope["error_code"], string>
> = {
  AI_PIPA_CONSENT_MISSING:
    "개인정보 처리 동의가 필요합니다. 설정에서 동의해 주세요.",
  AI_COMMENT_SOURCE_KIND_INVALID:
    "분석 의견 출처가 불분명합니다 — strict reject 적용",
  AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS:
    "auto_analysis 의견은 수정할 수 없습니다 — 사용자는 검토만 가능",
  AI_COMMENT_SOURCE_KIND_WARNING:
    "분석 의견 출처가 불분명합니다 — strict reject 적용",
} as const;
