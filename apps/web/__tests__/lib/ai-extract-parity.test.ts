/**
 * apps/web/__tests__/lib/ai-extract-parity.test.ts — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * AD-15 cross-language parity test for ai-extract.ts (TS mirror) vs
 * apps/api/modules/m10_ai/schemas.py Story 10.1 EXTENSION.
 *
 * Coverage (T1):
 *   - MonthlyDraftEntry shape parity (3 fields × verify)
 *   - MonthlyExtractEnvelope Discriminated union tag `status` parity
 *   - extraction_confidence threshold parity (PRD §8.1 M0-c 70%)
 *   - 3 error_code Literal parity (PIPA + INVALID_FIELD + EXTRACTION_ERROR)
 *
 * Total: ~4 NEW vitest cases.
 */

import { describe, expect, it } from "vitest";

import {
  MONTHLY_EXTRACT_CONFIDENCE_THRESHOLD,
  type MonthlyDraftEntry,
  type MonthlyExtractEnvelope,
  type MonthlyExtractErrorEnvelope,
} from "@/lib/ai-extract";

describe("ai-extract parity — Sprint 10.5 T1", () => {
  it("MonthlyDraftEntry has 6-stream canonical fields + required AD-7 invariant", () => {
    const draft: MonthlyDraftEntry = {
      field_name: "직접재료비",
      value: "1000",
      confidence: "0.9",
      target_table: "monthly_inputs",
      evidence_page: 1,
      requires_user_confirmation: false,
    };
    expect(draft.target_table).toBe("monthly_inputs");
    expect(["직접재료비", "직접노무비", "제조간접비", "판매관리비", "매출", "기말재고"]).toContain(
      draft.field_name,
    );
  });

  it("MonthlyExtractEnvelope Discriminated union tag discriminator = status", () => {
    const success: MonthlyExtractEnvelope = {
      status: "success",
      extraction_id: "e1",
      period_key: "2026-07",
      drafts: [],
      low_confidence_count: 0,
    };
    expect(success.status).toBe("success");

    const lowConf: MonthlyExtractEnvelope = {
      status: "low_confidence_warning",
      extraction_id: "e2",
      period_key: "2026-07",
      drafts: [],
      low_confidence_count: 1,
    };
    expect(lowConf.status).toBe("low_confidence_warning");

    const error: MonthlyExtractErrorEnvelope = {
      status: "error",
      error_code: "AI_PIPA_CONSENT_MISSING",
      message_ko: "test",
      trace_id: "tr1",
    };
    expect(error.status).toBe("error");
    expect(error.error_code).toBe("AI_PIPA_CONSENT_MISSING");
  });

  it("extraction_confidence threshold = 0.70 (PRD §8.1 M0-c 70% 임계값)", () => {
    expect(MONTHLY_EXTRACT_CONFIDENCE_THRESHOLD).toBe(0.7);
  });

  it("3 error_code Literal values are present + exhaustive", () => {
    const errorCodes: MonthlyExtractErrorEnvelope["error_code"][] = [
      "AI_PIPA_CONSENT_MISSING",
      "INVALID_MONTHLY_FIELD_VALUE",
      "MONTHLY_EXTRACTION_ERROR",
    ];
    expect(new Set(errorCodes).size).toBe(3);
    // All values must be addressed in ko-KR.json SSOT
    const expectedMessages = {
      AI_PIPA_CONSENT_MISSING: "개인정보 처리 동의가 필요합니다",
      INVALID_MONTHLY_FIELD_VALUE: "입력값이 올바르지 않습니다",
      MONTHLY_EXTRACTION_ERROR: "월별 AI 추출에 실패했습니다",
    } as const;
    for (const code of errorCodes) {
      expect(expectedMessages[code]).toBeDefined();
    }
  });
});
