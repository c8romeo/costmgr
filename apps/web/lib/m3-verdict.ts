/**
 * apps/web/lib/m3-verdict.ts — TypeScript mirror of the AD-12 verdict
 * envelope defined in
 * `apps/api/modules/m3_calculate/schemas.py` (CalcResponse.verdict).
 *
 * THIS FILE IS NOT THE SOURCE OF TRUTH. The Python Pydantic model is
 * canonical (AD-15/CalcResponse + AD-20/external Literal type).
 * Drift between this file and the Python verifier is caught by
 * `tests/web/test_m3_verdict_parity.py` (Story 4.3 — Task 6 cross-lang
 * boundary fixture).
 *
 * Cross-language parity discipline (Story 4.3 §Task 6 dev notes):
 * - snake_case (Python) ↔ camelCase (TS) at the API boundary
 * - `verification_status` ∈ {passed, failed} (AD-20 — pending internal-only)
 * - `top_failure` is non-null iff verification_status === 'failed'
 * - `verifications[]` contains only fired rules (silent skip for
 *   applies_to=False → not in array)
 * - Korean `message_ko` diagnostic strings are deterministic (AD-5 purity)
 * - rules[].code ∈ {V1, V4, V7, V8} governed by the same Literal type
 *   the Python Pydantic schema enforces
 *
 * Per-industry firing matrix (Story 4.3 AC #7):
 * - V1 (완전배부): all industries (universal 1원 단위 invariant)
 * - V4 (원가-손익 Reconciliation): all industries (universal 4요소)
 * - V7 (ABC 무결성): service-only (AD-12 spec interpretation, cj-default)
 * - V8 (엔진 대조): all industries (placeholder until Story 4.4 fills)
 *
 * UI usage (Story 4.4 future):
 * - rendering: pass / fail badge in [월 마감] → [결과 보기] modal
 * - toast: V* failure surfaces blocked calc + ERR_V1 / ERR_V4 / ERR_V7 / ERR_V8 codes
 * - audit trail: trace_id round-tripped for support diagnostics
 */

export type VerificationCode = "V1" | "V3" | "V4" | "V7" | "V8";

export type VerificationStatus = "passed" | "failed";

export type VerificationEnvelopeStatus = "passed" | "failed";

export type Industry =
  | "manufacturing"
  | "manufacturing_service"
  | "service"
  | "manufacturing_service_other";

export interface VerificationItem {
  code: VerificationCode;
  status: VerificationStatus;
  message_ko: string;
  details: { [key: string]: unknown };
}

export interface Verdict {
  verification_status: VerificationEnvelopeStatus;
  verifications: VerificationItem[];
  top_failure: VerificationItem | null;
  trace_id: string;
}

/**
 * Per-industry firing matrix — used by the UI to render the verdict
 * tree. Mirrors `INDUSTRY_VALUES` in `apps/api/modules/m3_calculate/services/rules/protocol.py`.
 *
 * Rules per industry (Story 4.3 AC #7 + Story 5.3 AC #6):
 * - manufacturing: V1, V3, V4, V8 (V7 silent skip; V3 = closing ≥ 0 invariant)
 * - manufacturing_service: V1, V3, V4, V8 (V7 silent skip; V3 fires)
 * - service: V1, V4, V7, V8 (V3 silent skip — service-only tenant has no inventory)
 * - manufacturing_service_other: V1, V3, V4, V8 (V7 silent skip; V3 fires)
 */
export const INDUSTRY_FIRES_V7: Readonly<Record<Industry, boolean>> = {
  manufacturing: false,
  manufacturing_service: false,
  service: true,
  manufacturing_service_other: false,
};

/**
 * P3-3rd-sweep: V3 (closing ≥ 0 invariant) fires for inventory-bearing industries.
 * service-only tenants skip V3 (no inventory semantics).
 */
export const INDUSTRY_FIRES_V3: Readonly<Record<Industry, boolean>> = {
  manufacturing: true,
  manufacturing_service: true,
  service: false,
  manufacturing_service_other: true,
};

/**
 * Returns the list of VerificationCode expected to fire for the given
 * industry. Mirrors the AD-12 ordering invariant
 * (V1 → V4 → V3 → V7 → V8, P3-3rd-sweep insertion).
 */
export function expectedRuleCodesForIndustry(industry: Industry): VerificationCode[] {
  const codes: VerificationCode[] = ["V1", "V4", "V8"];
  if (INDUSTRY_FIRES_V3[industry]) {
    codes.splice(2, 0, "V3"); // insert V3 between V4 and V8 (before optional V7)
  }
  if (INDUSTRY_FIRES_V7[industry]) {
    codes.splice(2, 0, "V7"); // insert V7 between V4 and V3 (or V4 and V8)
  }
  return codes;
}

/**
 * V* failure UI codes — surface in toast / modal when verdict.verification_status === 'failed'.
 * P3-3rd-sweep: V3 corrected from "ERR_V3_UNIT_OF_ACCOUNT_CONFLICT" (copy-paste smell) to
 * "ERR_V3_NEGATIVE_CLOSING_INVENTORY" matching the actual V3 rule (closing ≥ 0 invariant)
 * and Python `V3_FAILURE_KO_MESSAGE` ("기말재고 음수").
 */
export const V_FAILURE_CODES: Readonly<Record<VerificationCode, string>> = {
  V1: "ERR_V1_INCOMPLETE_ALLOCATION",
  V3: "ERR_V3_NEGATIVE_CLOSING_INVENTORY",
  V4: "ERR_V4_COST_INCOME_RECONCILIATION",
  V7: "ERR_V7_ABC_INTEGRITY",
  V8: "ERR_V8_ENGINE_REGRESSION",
};

/**
 * Type guard for the verdict envelope shape (defense-in-depth at the
 * API boundary). The Python FastAPI handler guarantees the type via
 * Pydantic, but the TS side re-validates in case of upstream drift.
 */
export function isVerdict(value: unknown): value is Verdict {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  if (v.verification_status !== "passed" && v.verification_status !== "failed") return false;
  if (!Array.isArray(v.verifications)) return false;
  if (typeof v.trace_id !== "string") return false;
  if (v.top_failure !== null && typeof v.top_failure !== "object") return false;
  return true;
}

/**
 * Convenience: returns the top failure's UI code (e.g. ERR_V1_INCOMPLETE_ALLOCATION)
 * or null if verdict is passed.
 */
export function topFailureCode(verdict: Verdict): string | null {
  if (verdict.verification_status === "passed" || verdict.top_failure === null) {
    return null;
  }
  return V_FAILURE_CODES[verdict.top_failure.code] ?? null;
}

/**
 * Convenience: aggregate a verdict's fired rules as a code summary
 * (e.g. ['V1', 'V4', 'V8']) for UI rendering.
 */
export function firedRuleCodes(verdict: Verdict): VerificationCode[] {
  return verdict.verifications.map((v) => v.code);
}
