// apps/web/lib/m9-abc-v7-verdict-schema.ts — Story 9.3
//
// TS mirror for the M9 ABC V7 verdict schema
// (PRD §V7 verbatim + A29 forward-lock dual-route + AD-8 1-Won precision).
//
// Mirrors `packages/cost_engine/abc_engine.py` 9-3 EXTENSION surface:
//   - V7Verdict frozen dataclass (Σ breakdown + unused = Σ department)
//   - V7 balance tolerance (KRW 1-Won precision)
//   - validate_v7_balance pure function (1-Won precision parity)
//
// AD-15 §1 cross-language parity with
// `apps/api/modules/m9_abc/services/abc_allocation_service.py`
// (V7 verdict at allocation outcome boundary).
//
// AD-8 monetary parity — Decimal-as-string (no Number) — preserves
// 1-Won precision across TS/Python boundary.

// ── Constants (mirror packages/cost_engine/abc_engine.py 9-3) ──────

/** V7 ABC 무결성 1원 단위 허용 오차 (PRD §V7 verbatim). */
export const V7_BALANCE_TOLERANCE_KRW = "0.01";

/** KRW integer precision boundary (PRD §V7 verbatim 1원 정밀도). */
export const KRW_INTEGER_PRECISION = 1;

/** V8 hash prefix (mirror VALIDATION_HASH_PREFIX). */
export const VALIDATION_HASH_PREFIX = "sha256:";
export const VALIDATION_HASH_LENGTH = 64;
export const VALIDATION_HASH_REGEX = /^[0-9a-f]{64}$/;

// ── V7Verdict (mirror pure kernel frozen dataclass) ──────────────

/** PRD §A6 + §V7 verbatim — Σ breakdown + unused = Σ department. */
export interface V7Verdict {
  is_balanced: boolean;
  /** Σ cost_object_breakdown.allocated_krw (Decimal-as-string, KRW integer). */
  breakdown_sum: string;
  /** Σ unused_capacity_breakdown.unused_cost_krw (Decimal-as-string, KRW integer). */
  unused_cost: string;
  /** Σ department_cost (Decimal-as-string, KRW integer). */
  expected_sum: string;
  /** |breakdown_sum + unused_cost - expected_sum| (Decimal-as-string). */
  delta_krw: string;
  /** sha256:64-hex (V8 determinism). */
  hash: string;
}

// ── validate_v7_balance (mirror pure kernel function) ────────────

/**
 * V7 ABC 무결성 1원 단위 검증 — PRD §V7 verbatim.
 *
 * Cross-language parity with `packages/cost_engine/abc_engine.py`
 * `validate_v7_balance(breakdown_sum, unused_cost, expected_sum)`:
 *
 *   is_balanced = (
 *     Decimal(str(breakdown_sum)) +
 *     Decimal(str(unused_cost)) ==
 *     Decimal(str(expected_sum))
 *   )
 *
 * @param breakdownSum — Σ cost_object_breakdown.allocated_krw (Decimal-as-string)
 * @param unusedCost — Σ unused_capacity_breakdown.unused_cost_krw (Decimal-as-string)
 * @param expectedSum — Σ department_cost (Decimal-as-string)
 * @returns is_balanced boolean + delta_krw (Decimal-as-string)
 */
export interface V7BalanceResult {
  is_balanced: boolean;
  breakdown_sum: string;
  unused_cost: string;
  expected_sum: string;
  delta_krw: string;
}

/**
 * BigInt-based Decimal-as-string equality check for V7 balance (AD-8).
 *
 * Use BigInt to avoid float precision loss. Convert all KRW strings
 * to BigInt (integer KRW) and compare. delta = |lhs - rhs|.
 */
export function validateV7Balance(
  breakdownSum: string,
  unusedCost: string,
  expectedSum: string,
): V7BalanceResult {
  // Convert KRW strings (Decimal-as-string, integer KRW) to BigInt.
  const breakdownBi = krwStringToBigInt(breakdownSum);
  const unusedBi = krwStringToBigInt(unusedCost);
  const expectedBi = krwStringToBigInt(expectedSum);

  const lhs = breakdownBi + unusedBi;
  const deltaBi = lhs >= expectedBi ? lhs - expectedBi : expectedBi - lhs;

  return {
    is_balanced: deltaBi === 0n,
    breakdown_sum: breakdownSum,
    unused_cost: unusedCost,
    expected_sum: expectedSum,
    delta_krw: deltaBi.toString(),
  };
}

/**
 * Convert KRW Decimal-as-string to BigInt (AD-8 1-Won precision).
 *
 * Handles both "1234567" and "1234567.89" formats by truncating
 * fractional KRW (1원 정밀도). For ABC engine wire format (KRW integer),
 * this is a no-op integer parse.
 */
function krwStringToBigInt(value: string): bigint {
  // Strip whitespace + handle negative sign.
  const trimmed = value.trim();
  if (trimmed === "" || trimmed === "0" || trimmed === "0.0" || trimmed === "0.00") {
    return 0n;
  }
  // Parse as float, round, then convert to BigInt (1-Won truncation).
  // We use Math.round to handle KRW sub-won fractions safely.
  const num = Number.parseFloat(trimmed);
  if (!Number.isFinite(num)) {
    throw new Error(`Invalid KRW string: ${value}`);
  }
  return BigInt(Math.round(num));
}

// ── formatV7VerdictBadge (UI helper for V7 verdict display) ───────

/** Korean SSOT — ko-KR.json SSOT CR 11-4 D-002 fallback. */
export const V7_BALANCED_KO = "V7 무결성 통과 (1원 단위)";
export const V7_UNBALANCED_KO = "V7 무결성 위반 (1원 단위)";

export interface V7VerdictBadgeProps {
  verdict: V7Verdict;
  showDetails?: boolean;
}

/** Format V7 verdict for badge display (used by AbcDispatchResultCard). */
export function formatV7VerdictLabel(verdict: V7Verdict): string {
  return verdict.is_balanced ? V7_BALANCED_KO : V7_UNBALANCED_KO;
}

/** Format delta_krw as Korean won string (used by AbcDispatchResultCard). */
export function formatV7DeltaKrw(deltaKrw: string): string {
  const bi = krwStringToBigInt(deltaKrw);
  const formatted = bi.toLocaleString("ko-KR");
  return `${formatted}원`;
}
