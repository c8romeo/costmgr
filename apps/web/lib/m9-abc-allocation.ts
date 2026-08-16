// apps/web/lib/m9-abc-allocation.ts — Story 9.2
//
// TS mirror for the M9 ABC Allocation Engine wire (PRD §F9.2 verbatim:
// "CCR = 부서 원가 ÷ 실제 조업능력 시간, 1원 단위 + 미사용능력 별도 행").
//
// Mirrors `packages/cost_engine/abc_engine.py` CCR + Allocation +
// UnusedCapacityRow frozen dataclasses + serializer shape (CR 11-3
// ALLOWED_SERVICE_SUBMODULES — `packages/services/m9_abc/abc_allocation_serializers`).
//
// AD-15 §1 cross-language parity with `apps/api/modules/m9_abc/schemas.py`.
// Decimal-as-string (no Number) — preserve precision (AD-8 monetary parity).

// ── Constants (mirror packages/cost_engine/abc_engine.py) ──────

/** 1원 단위 양자화 (CCR_KRW_QUANTUM mirror). */
export const CCR_KRW_QUANTUM = "1";

/** KRW 1원 단위 허용 오차 (PRD §V7 "Σ breakdown + unused = Σ department_cost"). */
export const ABC_PRECISION_KRW_TOLERANCE = "0.01";

/** Decimal-as-string regex (CR 11-4 D-005 — strict regex match). */
export const DECIMAL_STRING_REGEX = /^-?\d+(\.\d+)?$/;

/** V8 hash prefix (mirror CCR_HASH_PREFIX). */
export const CCR_HASH_PREFIX = "sha256:";
export const CCR_HASH_LENGTH = 64;
export const CCR_HASH_REGEX = /^[0-9a-f]{64}$/;

/** Korean SSOT constants — ko-KR.json SSOT CR 11-4 D-002 fallback. */
export const ABC_CCR_INVALID_CAPACITY_KO =
  "CCR 계산: 실제 조업능력은 0보다 커야 합니다";
export const ABC_ALLOCATION_BALANCE_ERROR_KO =
  "ABC 배부액 합계가 부서 원가와 일치하지 않습니다";

// ── Allocation state types (mirror pure kernel frozen dataclasses) ──

export interface CCRResult {
  department_id: string;
  department_cost: string; // Decimal-as-string (KRW integer)
  practical_capacity_hours: string; // Decimal-as-string
  ccr_per_hour: string; // Decimal-as-string (KRW integer)
  hash: string; // sha256:64-hex
}

export interface ActivityMapping {
  activity_id: string;
  hours: string; // Decimal-as-string
  ccr_amount_krw: string; // Decimal-as-string (KRW integer)
}

export interface CostObjectRow {
  product_id: string;
  activity_id: string;
  driver_id: string;
  allocated_krw: string; // Decimal-as-string (KRW integer)
}

export interface UnusedCapacityRow {
  unused_hours: string; // Decimal-as-string
  ccr_per_hour: string; // Decimal-as-string
  unused_cost_krw: string; // Decimal-as-string (KRW integer)
  hash: string; // sha256:64-hex
}

export interface AllocationResult {
  ccr: CCRResult;
  activity_mappings: ActivityMapping[];
  cost_object_breakdown: CostObjectRow[];
  unused_capacity: UnusedCapacityRow;
  department_cost: string; // Decimal-as-string (KRW integer)
  total_breakdown_sum: string; // Decimal-as-string (KRW integer)
  is_balanced: boolean;
}

// ── Wire envelope (mirror AllocationResponse Pydantic) ─────────

export interface AllocationWire {
  department_id: string;
  department_cost: string;
  ccr_per_hour: string;
  total_breakdown_sum: string;
  unused_hours: string;
  unused_cost_krw: string;
  is_balanced: boolean;
  activity_mappings: AllocationActivityMappingWire[];
  cost_object_breakdown: AllocationCostObjectWire[];
  ccr_hash: string;
  allocation_hash: string;
  message_ko: string | null;
  unused_message_ko: string | null;
}

export interface AllocationActivityMappingWire {
  activity_id: string;
  hours: string;
  ccr_amount_krw: string;
}

export interface AllocationCostObjectWire {
  product_id: string;
  activity_id: string;
  driver_id: string;
  allocated_krw: string;
}

// ── AllocationState union (mirror Python AllocationState) ──────

export type AllocationState =
  | CCRResult
  | AllocationResult
  | UnusedCapacityRow
  | ActivityMapping
  | CostObjectRow;

// ── Type guards (mirror Pydantic extra="forbid") ──────────────

export function isCCRResult(obj: unknown): obj is CCRResult {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.department_id === "string" &&
    typeof o.department_cost === "string" &&
    typeof o.practical_capacity_hours === "string" &&
    typeof o.ccr_per_hour === "string" &&
    typeof o.hash === "string" &&
    o.hash.startsWith(CCR_HASH_PREFIX)
  );
}

export function isUnusedCapacityRow(obj: unknown): obj is UnusedCapacityRow {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.unused_hours === "string" &&
    typeof o.ccr_per_hour === "string" &&
    typeof o.unused_cost_krw === "string" &&
    typeof o.hash === "string"
  );
}

export function isAllocationResult(obj: unknown): obj is AllocationResult {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    isCCRResult(o.ccr) &&
    Array.isArray(o.activity_mappings) &&
    Array.isArray(o.cost_object_breakdown) &&
    isUnusedCapacityRow(o.unused_capacity) &&
    typeof o.department_cost === "string" &&
    typeof o.total_breakdown_sum === "string" &&
    typeof o.is_balanced === "boolean"
  );
}

export function isAllocationState(obj: unknown): obj is AllocationState {
  return (
    isCCRResult(obj) ||
    isAllocationResult(obj) ||
    isUnusedCapacityRow(obj) ||
    isActivityMapping(obj) ||
    isCostObjectRow(obj)
  );
}

export function isActivityMapping(obj: unknown): obj is ActivityMapping {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.activity_id === "string" &&
    typeof o.hours === "string" &&
    typeof o.ccr_amount_krw === "string"
  );
}

export function isCostObjectRow(obj: unknown): obj is CostObjectRow {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.product_id === "string" &&
    typeof o.activity_id === "string" &&
    typeof o.driver_id === "string" &&
    typeof o.allocated_krw === "string"
  );
}

export function isAllocationWire(obj: unknown): obj is AllocationWire {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.department_id === "string" &&
    typeof o.department_cost === "string" &&
    typeof o.ccr_per_hour === "string" &&
    typeof o.total_breakdown_sum === "string" &&
    typeof o.unused_hours === "string" &&
    typeof o.unused_cost_krw === "string" &&
    typeof o.is_balanced === "boolean" &&
    Array.isArray(o.activity_mappings) &&
    Array.isArray(o.cost_object_breakdown) &&
    typeof o.ccr_hash === "string" &&
    typeof o.allocation_hash === "string" &&
    (o.message_ko === null || typeof o.message_ko === "string") &&
    (o.unused_message_ko === null || typeof o.unused_message_ko === "string")
  );
}

export function isValidV8AllocationHash(hash: string): boolean {
  return (
    hash.length === CCR_HASH_LENGTH &&
    hash.startsWith(CCR_HASH_PREFIX) === false &&
    CCR_HASH_REGEX.test(hash.slice(CCR_HASH_PREFIX.length))
  );
}

// ── Error code → message map (CR 11-4 D-002 ko-KR.json SSOT) ───

export const ABC_ALLOCATION_ERROR_CODE_MAP: Record<string, string> = {
  CCR_INVALID_CAPACITY: ABC_CCR_INVALID_CAPACITY_KO,
  ALLOCATION_BALANCE_ERROR: ABC_ALLOCATION_BALANCE_ERROR_KO,
  CAPABILITY_NOT_GRANTED: "ABC 계산 권한이 없습니다.",
};

/**
 * Extract the Korean error message from a fetch response body, falling back
 * to the envelope's `message_ko` field, then to a ko-KR.json SSOT constant
 * via `ABC_ALLOCATION_ERROR_CODE_MAP`.
 */
export function extractAbcAllocationErrorMessage(
  body: { code?: string; message_ko?: string } | null | undefined,
): string {
  if (!body) return "알 수 없는 오류가 발생했습니다.";
  if (typeof body.message_ko === "string" && body.message_ko.length > 0) {
    return body.message_ko;
  }
  if (
    typeof body.code === "string" &&
    body.code in ABC_ALLOCATION_ERROR_CODE_MAP
  ) {
    return (
      ABC_ALLOCATION_ERROR_CODE_MAP[body.code] ??
      "알 수 없는 오류가 발생했습니다."
    );
  }
  return "알 수 없는 오류가 발생했습니다.";
}