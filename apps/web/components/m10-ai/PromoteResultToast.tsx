/**
 * apps/web/components/m10-ai/PromoteResultToast.tsx — Sprint 10.5 T4 wire (D-10-4-DEFER-4 해소)
 *
 * Story 10.4 (AI Promotion Port Idempotency) frontend mount.
 * Renders the post-promotion result toast based on the discriminated
 * union `PromoteEnvelope` (CR 12-5 D-13/D-14 verbatim).
 *
 * AD-15 parity SSOT: the Discriminated union tag `status` carries:
 *   - "success"                 → "✅ 승격 완료" toast
 *   - "draft_immutable"         → "PROMOTE_DRAFT_IMMUTABLE" error toast
 *   - "source_draft_not_found"  → "PROMOTE_SOURCE_DRAFT_NOT_FOUND" error toast
 *   - "idempotency_mismatch"    → "PROMOTE_IDEMPOTENCY_MISMATCH" error toast
 *   - "m2_only"                 → "INPUT_PROMOTION_M2_ONLY" error toast (AD-17)
 *   - "pipa_consent_missing"    → "AI_PIPA_CONSENT_MISSING" error toast
 *   - "promotion_denied"        → "INPUT_PROMOTION_DENIED" error toast
 *
 * CR 11-4 D-005 — Unknown state reject: unknown status → null + console.warn.
 */

"use client";

import type { PromoteEnvelope } from "@/lib/ai-promote";

interface PromoteResultToastProps {
  envelope: PromoteEnvelope | null;
  locale?: "ko-KR" | "en-US";
}

const STATUS_LABEL_KO: Readonly<Record<PromoteEnvelope["status"], string>> = {
  success: "✅ 승격 완료",
  draft_immutable: "❌ 초안이 이미 승격 완료 또는 superseded 상태입니다",
  source_draft_not_found: "❌ 해당 초안을 찾을 수 없습니다",
  idempotency_mismatch:
    "❌ 동일 초안에 다른 값으로 재호출되었습니다. 원본 초안의 confirmed_value_hash를 사용해 주세요.",
  m2_only: "❌ 승격 포트는 M2 모듈만 호출할 수 있습니다. M2 서비스 토큰으로 인증해 주세요.",
  pipa_consent_missing: "❌ 승격 포트는 개인정보 처리 동의가 필요합니다. 설정에서 동의해 주세요.",
  promotion_denied: "❌ 승격이 거부되었습니다 (counter increment 후 retry 권장)",
};

export function PromoteResultToast({
  envelope,
  locale = "ko-KR",
}: PromoteResultToastProps): React.ReactElement | null {
  if (envelope === null) {
    return null;
  }

  const isKnownStatus =
    envelope.status === "success" ||
    envelope.status === "draft_immutable" ||
    envelope.status === "source_draft_not_found" ||
    envelope.status === "idempotency_mismatch" ||
    envelope.status === "m2_only" ||
    envelope.status === "pipa_consent_missing" ||
    envelope.status === "promotion_denied";

  if (!isKnownStatus) {
    if (process.env.NODE_ENV === "development") {
       
      console.warn(
        `[PromoteResultToast] Unknown status='${(envelope as { status?: unknown }).status}' — refusing to render.`,
      );
    }
    return null;
  }

  const isSuccess = envelope.status === "success";
  const label =
    locale === "ko-KR"
      ? STATUS_LABEL_KO[envelope.status]
      : `Promote envelope status: ${envelope.status}`;

  return (
    <div
      role={isSuccess ? "status" : "alert"}
      aria-live={isSuccess ? "polite" : "assertive"}
      data-testid="promote-result-toast"
      data-status={envelope.status}
      className={`rounded-md border px-4 py-3 text-sm ${
        isSuccess
          ? "border-green-300 bg-green-50 text-green-900 dark:border-green-700 dark:bg-green-950 dark:text-green-200"
          : "border-red-300 bg-red-50 text-red-900 dark:border-red-700 dark:bg-red-950 dark:text-red-200"
      }`}
    >
      <div className="font-medium">{label}</div>
      {isSuccess && (
        <div className="mt-1 space-y-1 text-xs">
          <div data-testid="promote-result-promo-id">
            promotion_id: {envelope.promotion_id}
          </div>
          {envelope.idempotent_replay && (
            <div className="text-blue-700 dark:text-blue-300" data-testid="promote-result-replay">
              ℹ️ 멱등 재호출 (기존 promotion 반환)
            </div>
          )}
          <div data-testid="promote-result-audit-ids">
            감사로그 ID: {envelope.audit_log_ids.join(", ")}
          </div>
        </div>
      )}
      {!isSuccess && (
        <div
          className="mt-1 text-xs"
          data-testid="promote-result-error-code"
          data-error-code={envelope.code}
        >
          code: {envelope.code}
        </div>
      )}
    </div>
  );
}
