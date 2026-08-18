/**
 * apps/web/lib/ai-promote.ts — Story 10.4 (AI Promotion Port Idempotency) TS mirror.
 *
 * cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속.
 *
 * AD-15 cross-language parity SSOT: this file mirrors the Python schema
 * (`apps/api/modules/m10_ai/schemas.py` EXTENSION section) and the kernel
 * (`packages/services/m10_ai/promoter_port.py`) verbatim.
 *
 * AD-17 verbatim bind (handler contract):
 *   - POST /api/v1/ai/promote
 *   - Body: { tenant_id, period_key, source_draft_id, confirmed_value_hash, actor_id }
 *   - Returns discriminated union `PromoteEnvelope` with `status` tag.
 *
 * Test debt (A35 carry-over — honestly DEFER (d)):
 *   Frontend integration tests for this wire are NOT included in the
 *   Story 10.4 atomic sprint. The TS mirror is shipped for parity SSOT
 *   (AD-15) and type safety; frontend vitest coverage is delegated to
 *   the A35 "frontend test debt" dedicated sprint per A19 lesson
 *   `cr-a19-lessons` + A34 4-category honestly DEFER framework.
 *
 *   Reference: D-10-4-DEFER-4 (d) — frontend test debt (TS mirror parity).
 */

import { ApiError } from "./api-client";

// ── SSOT mirror — Python `apps.api.modules.m10_ai.schemas` section ─

export type PromoteStatus =
  | "success"
  | "draft_immutable"
  | "source_draft_not_found"
  | "idempotency_mismatch"
  | "m2_only"
  | "pipa_consent_missing"
  | "promotion_denied";

export interface PromoteRequestBody {
  tenant_id: string;
  period_key: string;
  source_draft_id: string;
  confirmed_value_hash?: string | null;
  actor_id: string;
}

export interface PromoteResponseSuccess {
  status: "success";
  tenant_id: string;
  period_key: string;
  source_draft_id: string;
  promotion_id: string;
  idempotency_key: string;
  confirmed_input_row_id: string;
  promoted_at: string;
  draft_hash: string;
  idempotent_replay: boolean;
  audit_log_ids: [string, string];
}

export interface PromoteErrorEnvelope {
  status: Exclude<PromoteStatus, "success">;
  code:
    | "PROMOTE_DRAFT_IMMUTABLE"
    | "PROMOTE_SOURCE_DRAFT_NOT_FOUND"
    | "PROMOTE_IDEMPOTENCY_MISMATCH"
    | "INPUT_PROMOTION_M2_ONLY"
    | "AI_PIPA_CONSENT_MISSING"
    | "INPUT_PROMOTION_DENIED";
  message_ko: string;
  details: Record<string, unknown>;
  trace_id: string;
}

export type PromoteEnvelope = PromoteResponseSuccess | PromoteErrorEnvelope;

export type PromoteErrorCode = PromoteErrorEnvelope["code"];

// ── HTTP wire (AD-15 parity SSOT — request() convention) ───────────

const PROMOTE_PATH = "/api/v1/ai/promote";
const PROMOTE_TIMEOUT_MS = 10_000;

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
 * POST /api/v1/ai/promote — AD-17 verbatim promotion port.
 *
 * Idempotent on (tenant_id, period_key, source_draft_id) 3-tuple.
 * Returns discriminated union `PromoteEnvelope`. Callers MUST switch on
 * `status` to discriminate success vs the 6 error variants.
 *
 * Auth: requires M2 service-role JWT (`actor_role = "m2_service_role"`).
 * The HTTP layer's `get_current_m2_user` enforces this; the kernel
 * re-checks the actor_role Literal as defense-in-depth.
 */
export async function promoteAiDraft(
  body: PromoteRequestBody,
  accessToken?: string,
): Promise<PromoteEnvelope> {
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
    PROMOTE_TIMEOUT_MS,
  );

  try {
    const res = await fetch(PROMOTE_PATH, {
      method: "POST",
      headers,
      credentials: accessToken ? "omit" : "same-origin",
      body: JSON.stringify(body),
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

    if (payload === null || typeof payload !== "object") {
      const traceId = res.headers.get("X-Trace-Id") ?? "";
      throw new ApiError(res.status, {
        code: "EMPTY_RESPONSE",
        message_ko: "서버 응답이 비어 있습니다",
        details: {},
        trace_id: traceId,
      });
    }

    return payload as PromoteEnvelope;
  } finally {
    clearTimeout(timer);
  }
}

// ── AD-15 parity type-narrowing helpers (frontend read-side) ───────

/**
 * Type guard: returns true if the envelope is a success response.
 * Use to discriminate from `PromoteErrorEnvelope` variants.
 */
export function isPromoteSuccess(
  env: PromoteEnvelope,
): env is PromoteResponseSuccess {
  return env.status === "success";
}

/**
 * Type guard: returns true if the envelope is any error variant.
 */
export function isPromoteError(
  env: PromoteEnvelope,
): env is PromoteErrorEnvelope {
  return env.status !== "success";
}

/**
 * Map envelope error code → ko-KR user-facing message.
 * Mirrors the Python handler's `message_ko` for client-side fallbacks
 * (offline / pre-fetch display). For online errors, prefer the server's
 * `message_ko` verbatim.
 */
export const PROMOTE_ERROR_MESSAGE_KO: Readonly<Record<PromoteErrorCode, string>> = {
  PROMOTE_DRAFT_IMMUTABLE: "초안이 이미 승격 완료 또는 superseded 상태입니다",
  PROMOTE_SOURCE_DRAFT_NOT_FOUND: "해당 초안을 찾을 수 없습니다",
  PROMOTE_IDEMPOTENCY_MISMATCH:
    "동일 초안에 다른 값으로 재호출되었습니다. 원본 초안의 confirmed_value_hash를 사용해 주세요.",
  INPUT_PROMOTION_M2_ONLY:
    "승격 포트는 M2 모듈만 호출할 수 있습니다. M2 서비스 토큰으로 인증해 주세요.",
  AI_PIPA_CONSENT_MISSING:
    "승격 포트는 개인정보 처리 동의가 필요합니다. 설정에서 동의해 주세요.",
  INPUT_PROMOTION_DENIED: "승격이 거부되었습니다 (counter increment 후 retry 권장).",
} as const;