/**
 * apps/web/lib/ai-extract.ts — Story 10.1 (Monthly AI Document Extraction) TS mirror.
 *
 * Sprint 10.5 (cj-style Epic 10 carry-over 14번째 진입점 = cj-style 38번째 epic 연속)
 * — A38 frontend test debt dedicated sprint T1 wire (D-10-1-DEFER-3 해소).
 *
 * AD-15 cross-language parity SSOT: this file mirrors the Python schema
 * (`apps/api/modules/m10_ai/schemas.py` "Story 10.1 EXTENSION" section) and the
 * kernel (`packages/services/m10_ai/extraction_port.py`) verbatim.
 *
 * AD-7 verbatim bind (frontend read-side, NEVER writes confirmed_inputs):
 *   - 10-1 frontend wire = display only (AiDraftCard + ConfidenceBadge + AiExtractModal)
 *   - Source draft target_table is fixed = 'monthly_inputs' (AD-7 strict invariant)
 *   - extraction_confidence < 0.70 → RED badge (master PRD §8.1 M0-c 70% 임계값)
 *
 * 8th TS mirror parity: this file = AD-15 cross-language parity SSOT 8th wire
 * (after ai-promote.ts 10-4 7th). Frontend integration tests for this wire
 * live in `apps/web/__tests__/lib/ai-extract-parity.test.ts` (T1 wire).
 */

import { ApiError } from "./api-client";

// ── SSOT mirror — Python `apps.api.modules.m10_ai.schemas` Story 10.1 EXTENSION ──

export type MonthlyExtractDocumentType = "pdf" | "xlsx";

export interface MonthlyExtractRequestBody {
  period_key: string;
  document_b64: string;
  document_type: MonthlyExtractDocumentType;
}

export interface MonthlyDraftEntry {
  field_name: string;
  value: string;
  confidence: string;
  target_table: "monthly_inputs";
  evidence_page: number | null;
  requires_user_confirmation: boolean;
}

export interface MonthlyExtractResponseSuccess {
  status: "success" | "low_confidence_warning";
  extraction_id: string;
  period_key: string;
  drafts: MonthlyDraftEntry[];
  low_confidence_count: number;
}

export interface MonthlyExtractErrorEnvelope {
  status: "error";
  error_code:
    | "AI_PIPA_CONSENT_MISSING"
    | "INVALID_MONTHLY_FIELD_VALUE"
    | "MONTHLY_EXTRACTION_ERROR";
  message_ko: string;
  trace_id: string;
}

export type MonthlyExtractEnvelope =
  | MonthlyExtractResponseSuccess
  | MonthlyExtractErrorEnvelope;

// ── AD-15 parity utilities (frontend read-side) ─────────────────────

export const MONTHLY_EXTRACT_CONFIDENCE_THRESHOLD = 0.7;

export function isLowConfidence(draft: MonthlyDraftEntry): boolean {
  return Number(draft.confidence) < MONTHLY_EXTRACT_CONFIDENCE_THRESHOLD;
}

export function isMonthlyExtractError(
  env: MonthlyExtractEnvelope,
): env is MonthlyExtractErrorEnvelope {
  return (
    typeof env === "object" &&
    env !== null &&
    (env as { status?: unknown }).status === "error"
  );
}

export function isMonthlyExtractSuccess(
  env: MonthlyExtractEnvelope,
): env is MonthlyExtractResponseSuccess {
  if (typeof env !== "object" || env === null) return false;
  const status = (env as { status?: unknown }).status;
  return status === "success" || status === "low_confidence_warning";
}

export const MONTHLY_EXTRACT_ERROR_MESSAGE_KO: Readonly<
  Record<MonthlyExtractErrorEnvelope["error_code"], string>
> = {
  AI_PIPA_CONSENT_MISSING:
    "개인정보 처리 동의가 필요합니다. 설정에서 동의해 주세요.",
  INVALID_MONTHLY_FIELD_VALUE:
    "입력값이 올바르지 않습니다 (월 입력 6개 카테고리 검증 실패)",
  MONTHLY_EXTRACTION_ERROR: "월별 AI 추출에 실패했습니다 — 잠시 후 다시 시도하세요",
} as const;

// ── HTTP wire (AD-15 parity SSOT — request() convention) ───────────

const MONTHLY_EXTRACT_PATH = "/api/v1/ai/extract-monthly";
const MONTHLY_EXTRACT_TIMEOUT_MS = 30_000;

function isApiErrorPayload(v: unknown): v is {
  error_code: string;
  message_ko: string;
  trace_id: string;
} {
  if (typeof v !== "object" || v === null) return false;
  const r = v as Record<string, unknown>;
  return (
    typeof r.error_code === "string" &&
    typeof r.message_ko === "string" &&
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
 * POST /api/v1/ai/extract-monthly — Story 10.1 AD-15 verbatim monthly
 * extraction port.
 *
 * Returns discriminated union `MonthlyExtractEnvelope`. Callers MUST
 * switch on `status` to discriminate success (with low_confidence_warning
 * for low-confidence drafts) from 3 error variants.
 *
 * Auth: requires PIPA consent (`AI_PIPA_CONSENT_MISSING` is one of the
 * error envelopes — wire 진입 carry-over from 10-1).
 */
export async function extractMonthlyAiDraft(
  body: MonthlyExtractRequestBody,
  accessToken?: string,
): Promise<MonthlyExtractEnvelope> {
  const headers = new Headers();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("Content-Type", "application/json");

  const controller = new AbortController();
  const timer = setTimeout(
    () =>
      controller.abort(
        new DOMException("Request timeout", "TimeoutError"),
      ),
    MONTHLY_EXTRACT_TIMEOUT_MS,
  );

  try {
    const res = await fetch(MONTHLY_EXTRACT_PATH, {
      method: "POST",
      headers,
      credentials: accessToken ? "omit" : "same-origin",
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const payload = await parseJsonSafe(res);

    if (!res.ok) {
      if (isApiErrorPayload(payload)) {
        throw new ApiError(res.status, {
          code: payload.error_code,
          message_ko: payload.message_ko,
          details: {},
          trace_id: payload.trace_id,
        });
      }
      const traceId = res.headers.get("X-Trace-Id") ?? "";
      throw new ApiError(res.status, {
        code: "UNPARSEABLE_RESPONSE",
        message_ko: `서버 응답을 해석할 수 없습니다 (HTTP ${res.status})`,
        details: { raw: String(payload) },
        trace_id: traceId,
      });
    }

    if (payload === null || typeof payload !== "object") {
      const traceId = res.headers.get("X-Trace-Id") ?? "";
      throw new ApiError(res.status, {
        code: "EMPTY_RESPONSE",
        message_ko: "서버 응답이 비어 있습니다",
        details: {},
        trace_id: traceId,
      });
    }

    return payload as MonthlyExtractEnvelope;
  } finally {
    clearTimeout(timer);
  }
}
