// apps/web/lib/m9-abc-validation.ts — Story 9.1
//
// TS mirror for the M9 ABC 100% validation wire (PRD §F9.1 verbatim:
// "원가풀 행 합·활동 열 합·동인 합 모두 100% 가드").
//
// Mirrors `packages/cost_engine/abc_engine.py` constants + validation state
// types + `serialize_validation_state` serializer shape (CR 11-3
// ALLOWED_SERVICE_SUBMODULES — `packages/services/m9_abc/abc_validation_serializers`).
//
// AD-15 §1 cross-language parity with `apps/api/modules/m9_abc/schemas.py`.
// Decimal-as-string (no Number) — preserve precision (AD-8 monetary parity).

// ── Constants (mirror packages/cost_engine/abc_engine.py) ──────

/** 100% 가드 target (PRD §F9.1 verbatim). */
export const VALIDATION_100_PCT_TARGET = 100;

/** Decimal-as-string regex (CR 11-4 D-005 — strict regex match). */
export const DECIMAL_STRING_REGEX = /^-?\d+(\.\d+)?$/;

/** Layer target literals (mirror Pydantic ValidationTarget). */
export const VALIDATION_TARGETS = ["cost_pool", "activity", "driver"] as const;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type ValidationTarget = (typeof VALIDATION_TARGETS)[number];

/** Korean SSOT constants — ko-KR.json SSOT CR 11-4 D-002 fallback. */
export const ABC_COST_POOL_INVALID_SUM_KO = "원가풀 행 합이 100%가 아닙니다";
export const ABC_ACTIVITY_INVALID_SUM_KO = "활동 열 합이 100%가 아닙니다";
export const ABC_DRIVER_INVALID_SUM_KO = "동인 합이 100%가 아닙니다";
export const ABC_VALIDATION_NOT_FOUND_KO = "ABC 검증 대상을 찾을 수 없습니다";

// ── Validation state types (mirror pure kernel frozen dataclasses) ──

export interface CostPoolValidationState {
  department_id: string;
  sum_pct: string; // Decimal-as-string
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  department_count: number;
  is_valid: boolean;
  hash: string; // sha256:64-hex
}

export interface ActivityValidationState {
  cost_pool_id: string;
  sum_pct: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  activity_count: number;
  is_valid: boolean;
  hash: string;
}

export interface DriverValidationState {
  activity_id: string;
  sum_pct: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  driver_count: number;
  is_valid: boolean;
  hash: string;
}

// ── Wire envelope (mirror ValidationResponse Pydantic) ─────────

export interface ValidationLayerWire {
  target: ValidationTarget;
  sum_pct: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  count: number;
  is_valid: boolean;
  hash: string;
  message_ko: string | null;
}

export interface ValidationResponse {
  cost_pool_id: string;
  activity_id: string;
  all_valid: boolean;
  layers: ValidationLayerWire[];
}

// ── Request envelopes (mirror Pydantic request models) ────────

export interface CostPoolValidationRequest {
  department_id: string;
  allocation_pcts: string[]; // Decimal-as-string
}

export interface ActivityValidationRequest {
  cost_pool_id: string;
  activity_pcts: string[];
}

export interface DriverValidationRequest {
  activity_id: string;
  driver_pcts: string[];
}

export interface ValidateRequest {
  cost_pool_id: string;
  activity_id: string;
  cost_pool?: string[] | null;
  activities?: string[] | null;
  drivers?: string[] | null;
}

// ── Type guards (mirror Pydantic extra="forbid") ──────────────

export function isValidationResponse(obj: unknown): obj is ValidationResponse {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  if (typeof o.cost_pool_id !== "string") return false;
  if (typeof o.activity_id !== "string") return false;
  if (typeof o.all_valid !== "boolean") return false;
  if (!Array.isArray(o.layers)) return false;
  for (const layer of o.layers) {
    if (!isValidationLayerWire(layer)) return false;
  }
  return true;
}

export function isValidationLayerWire(obj: unknown): obj is ValidationLayerWire {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.target === "string" &&
    VALIDATION_TARGETS.includes(o.target as ValidationTarget) &&
    typeof o.sum_pct === "string" &&
    typeof o.count === "number" &&
    typeof o.is_valid === "boolean" &&
    typeof o.hash === "string" &&
    (o.message_ko === null || typeof o.message_ko === "string")
  );
}

export function isValidAbcPct(value: string): boolean {
  if (!DECIMAL_STRING_REGEX.test(value)) return false;
  const num = Number(value);
  return num >= 0 && num <= VALIDATION_100_PCT_TARGET;
}

export function isValidAbcPctList(values: string[]): boolean {
  if (values.length === 0) return false;
  return values.every(isValidAbcPct);
}

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function sumPct(values: string[]): number {
  return values.reduce((acc, v) => acc + Number(v), 0);
}

export function isValidV8Hash(hash: string): boolean {
  return hash.length === 64 && /^[0-9a-f]{64}$/.test(hash);
}

// ── Error code → message map (CR 11-4 D-002 ko-KR.json SSOT) ───

export const ABC_VALIDATION_ERROR_CODE_MAP: Record<
  string,
  string
> = {
  COST_POOL_INVALID_SUM: ABC_COST_POOL_INVALID_SUM_KO,
  ACTIVITY_INVALID_SUM: ABC_ACTIVITY_INVALID_SUM_KO,
  DRIVER_INVALID_SUM: ABC_DRIVER_INVALID_SUM_KO,
  ABC_VALIDATION_NOT_FOUND: ABC_VALIDATION_NOT_FOUND_KO,
  CAPABILITY_NOT_GRANTED: "ABC 계산 권한이 없습니다.",
};

/**
 * Extract the Korean error message from a fetch response body, falling back
 * to the envelope's `message_ko` field, then to a ko-KR.json SSOT constant
 * via `ABC_VALIDATION_ERROR_CODE_MAP`.
 */
export function extractAbcValidationErrorMessage(
  body: { code?: string; message_ko?: string } | null | undefined,
): string {
  if (!body) return "알 수 없는 오류가 발생했습니다.";
  if (typeof body.message_ko === "string" && body.message_ko.length > 0) {
    return body.message_ko;
  }
  if (typeof body.code === "string" && body.code in ABC_VALIDATION_ERROR_CODE_MAP) {
    return ABC_VALIDATION_ERROR_CODE_MAP[body.code] ?? "알 수 없는 오류가 발생했습니다.";
  }
  return "알 수 없는 오류가 발생했습니다.";
}