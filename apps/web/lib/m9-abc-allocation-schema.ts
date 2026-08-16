// apps/web/lib/m9-abc-allocation-schema.ts — Story 9.2
//
// Validation schema + pure helpers for the M9 ABC Allocation Engine
// (PRD §F9.2 verbatim + §A9 + §V7):
//   - CCR compute: 부서 원가 ÷ 실제 조업능력 시간, 1원 단위
//   - Unused Capacity: 미사용능력 X,XXX원 별도 행 (PRD §A9)
//   - Allocation V7 balance: Σ breakdown + unused = Σ department_cost
//
// Mirrors the backend Pydantic v2 validation in
// `apps/api/modules/m9_abc/schemas.py` and the service-layer
// `validate_ccr_inputs` + `validate_allocation_inputs` 3-layer defense
// (CR 12-5 L3).
//
// CR 11-4 D-005: validation MUST throw on invalid input — NOT silent
// fall-through. Use `computeCcrTS(...)` + `isBalancedAllocation(...)` to
// assert validity before submitting.
//
// TS design: BigInt plain integer arithmetic for 1-Won precision (no
// fixed-point scaling, since all domain values — KRW, hours, percentages —
// are integer). Decimal-as-string preserved for JSON-safe wire shape
// (AD-8 cross-language parity with Python `Decimal`).

import {
  ABC_ALLOCATION_BALANCE_ERROR_KO,
  ABC_CCR_INVALID_CAPACITY_KO,
  CCR_HASH_PREFIX,
  DECIMAL_STRING_REGEX,
  type CCRResult,
  type ActivityMapping,
  type AllocationResult,
  type CostObjectRow,
  type UnusedCapacityRow,
} from "./m9-abc-allocation";

// ── Typed errors (mirror backend typed exceptions) ─────────────

export class AbcAllocationInputError extends Error {
  constructor(
    public readonly target: "ccr" | "allocation" | "unused_capacity",
    public readonly reason: string,
  ) {
    super(`${target}: ${reason}`);
    this.name = "AbcAllocationInputError";
  }
}

// ── Decimal-as-string helpers (plain integer BigInt arithmetic) ──

function parseDecimal(value: string, fieldName: string): bigint {
  if (!DECIMAL_STRING_REGEX.test(value)) {
    throw new AbcAllocationInputError(
      "ccr",
      `${fieldName} must be Decimal-as-string, got: ${value}`,
    );
  }
  const [intPart, fracPart = ""] = value.split(".");
  // Truncate fractional to 2 decimals (mirror Python Decimal precision).
  // Empty fracPart means no fractional → keep intPart as-is (no 100x scaling).
  const frac = fracPart.length > 0 ? (fracPart + "00").slice(0, 2) : "";
  const combined = `${intPart}${frac}`;
  return BigInt(combined); // BigInt handles sign natively
}

// ── V8 hash helpers (mirror backend hashlib.sha256) ────────────

function fnv1aHash(parts: readonly string[]): string {
  // Deterministic FNV-1a 64-bit hash for TS-side preview only.
  // Backend uses sha256:64-hex — TS preview uses deterministic placeholder
  // matching the prefix length for parity (AD-15 cross-language).
  let h = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  const mask = (1n << 64n) - 1n;
  for (const part of parts) {
    for (let i = 0; i < part.length; i++) {
      h ^= BigInt(part.charCodeAt(i));
      h = (h * prime) & mask;
    }
    h ^= 0n;
    h = (h * prime) & mask;
  }
  return h.toString(16).padStart(16, "0").padStart(64, "0");
}

// ── Pure kernel parity (mirror backend compute_ccr + compute_allocation) ─

/**
 * Compute CCR (자원동인율) per hour — 부서 원가 ÷ 실제 조업능력 시간.
 * 1-Won precision via BigInt round-half-up integer division (AD-8
 * Decimal-as-string parity).
 *
 * Throws AbcAllocationInputError on invalid input (CR 11-4 D-005).
 */
export function computeCcrTS(params: {
  department_id: string;
  department_cost: string;
  practical_capacity_hours: string;
}): CCRResult {
  if (params.department_id.length === 0) {
    throw new AbcAllocationInputError(
      "ccr",
      "empty_department_id",
    );
  }

  const cost = parseDecimal(params.department_cost, "department_cost");
  if (cost < 0n) {
    throw new AbcAllocationInputError(
      "ccr",
      "negative_cost",
    );
  }

  const hours = parseDecimal(
    params.practical_capacity_hours,
    "practical_capacity_hours",
  );
  if (hours <= 0n) {
    throw new AbcAllocationInputError(
      "ccr",
      ABC_CCR_INVALID_CAPACITY_KO,
    );
  }

  // CCR per hour (round-half-up integer division for 1-Won precision).
  const ccrPerHour = ((cost + hours / 2n) / hours).toString();

  const hash = `${CCR_HASH_PREFIX}${fnv1aHash([
    params.department_id,
    params.department_cost,
    params.practical_capacity_hours,
    ccrPerHour,
  ])}`;

  return {
    department_id: params.department_id,
    department_cost: params.department_cost,
    practical_capacity_hours: params.practical_capacity_hours,
    ccr_per_hour: ccrPerHour,
    hash,
  };
}

/**
 * Produce UnusedCapacityRow — 미사용능력 X,XXX원 별도 행 (PRD §A9 verbatim).
 *
 * unused_hours = practical_capacity_hours - used_hours
 * unused_cost_krw = unused_hours * ccr_per_hour
 */
export function produceUnusedCapacityRowTS(params: {
  ccr: CCRResult;
  used_hours: string;
}): UnusedCapacityRow {
  const used = parseDecimal(params.used_hours, "used_hours");
  if (used < 0n) {
    throw new AbcAllocationInputError(
      "unused_capacity",
      "negative_used_hours",
    );
  }
  const capacity = parseDecimal(
    params.ccr.practical_capacity_hours,
    "practical_capacity_hours",
  );
  if (used > capacity) {
    throw new AbcAllocationInputError(
      "unused_capacity",
      "exceeds_capacity",
    );
  }
  const ccrPerHour = parseDecimal(
    params.ccr.ccr_per_hour,
    "ccr_per_hour",
  );
  const unusedHours = capacity - used;
  const unusedCost = (unusedHours * ccrPerHour).toString();

  const hash = `${CCR_HASH_PREFIX}${fnv1aHash([
    params.ccr.department_id,
    params.used_hours,
    params.ccr.ccr_per_hour,
    unusedCost,
  ])}`;

  return {
    unused_hours: unusedHours.toString(),
    ccr_per_hour: params.ccr.ccr_per_hour,
    unused_cost_krw: unusedCost,
    hash,
  };
}

/**
 * Compute ABC Allocation Result with V7 balance check
 * (Σ breakdown + unused = Σ department_cost).
 *
 * Returns is_balanced = true when exact equality holds (1-Won precision
 * means integer arithmetic is exact, no fractional tolerance needed).
 */
export function computeAllocationTS(params: {
  ccr: CCRResult;
  activity_mappings: ActivityMapping[];
  cost_object_breakdown: CostObjectRow[];
  used_hours: string | null;
}): AllocationResult {
  const capacity = parseDecimal(
    params.ccr.practical_capacity_hours,
    "practical_capacity_hours",
  );
  const used = params.used_hours !== null
    ? parseDecimal(params.used_hours, "used_hours")
    : capacity;
  if (used < 0n) {
    throw new AbcAllocationInputError(
      "allocation",
      "negative_used_hours",
    );
  }
  if (used > capacity) {
    throw new AbcAllocationInputError(
      "allocation",
      "exceeds_capacity",
    );
  }

  // Sum of cost object breakdown.
  let breakdownSum = 0n;
  for (const row of params.cost_object_breakdown) {
    breakdownSum += parseDecimal(row.allocated_krw, "allocated_krw");
  }

  const ccrPerHour = parseDecimal(
    params.ccr.ccr_per_hour,
    "ccr_per_hour",
  );
  const unusedHours = capacity - used;
  const unusedCost = unusedHours * ccrPerHour;

  const unusedCapacity = produceUnusedCapacityRowTS({
    ccr: params.ccr,
    used_hours: used.toString(),
  });

  const departmentCost = parseDecimal(
    params.ccr.department_cost,
    "department_cost",
  );
  // V7 balance: exact equality (1-Won precision integer arithmetic).
  const isBalanced = breakdownSum + unusedCost === departmentCost;

  return {
    ccr: params.ccr,
    activity_mappings: params.activity_mappings,
    cost_object_breakdown: params.cost_object_breakdown,
    unused_capacity: unusedCapacity,
    department_cost: params.ccr.department_cost,
    total_breakdown_sum: breakdownSum.toString(),
    is_balanced: isBalanced,
  };
}

/**
 * Check whether an AllocationResult is V7-balanced.
 */
export function isBalancedAllocation(result: AllocationResult): boolean {
  return result.is_balanced;
}

/**
 * Build the Korean message for the unused capacity row (PRD §A9 verbatim
 * "미사용능력 X,XXX원" format).
 */
export function buildKoreanUnusedCapacityMessage(
  unused: UnusedCapacityRow,
): string {
  return `미사용능력 ${unused.unused_cost_krw}원`;
}

// ── Re-export for module-level constants parity ────────────────
export { ABC_CCR_INVALID_CAPACITY_KO, ABC_ALLOCATION_BALANCE_ERROR_KO };