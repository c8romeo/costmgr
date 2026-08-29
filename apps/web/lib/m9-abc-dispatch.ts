// apps/web/lib/m9-abc-dispatch.ts — Story 9.3
//
// TS mirror for the M9 ABC Dispatch dual-route wire
// (PRD §F9.3 + A29 forward-lock dual-route + AD-19).
//
// Mirrors `packages/cost_engine/abc_engine.py` 9-3 EXTENSION surface:
//   - DispatchState frozen dataclass (engine_type tag discriminator)
//   - V7Verdict frozen dataclass (Σ breakdown + unused = Σ department)
//   - MultiDepartmentCcrResult frozen dataclass (CCR aggregation)
//   - DepartmentAllocation frozen dataclass (per-dept allocation summary)
//   - UnusedCapacitySubRow frozen dataclass (per-dept unused capacity sub-row)
//   - validate_department_count pure function (1-50 guard)
//   - dispatch_abc_path pure function (engine_type tag dispatch decision)
//
// AD-15 §1 cross-language parity with
// `apps/api/modules/m3_calculate/services/calc_orchestrator.py`
// (CalcOutcome | CalcOutcomeABC discriminated union envelope) +
// `apps/api/modules/m9_abc/services/abc_allocation_service.py`.
// Decimal-as-string (no Number) — preserve precision (AD-8 monetary parity).

// ── Constants (mirror packages/cost_engine/abc_engine.py 9-3 EXTENSION) ──

/** V7 ABC 무결성 1원 단위 허용 오차 (PRD §V7 verbatim). */
export const V7_BALANCE_TOLERANCE_KRW = "0.01";

/** Multi-department CCR aggregation 부서 한도 (PRD §F9.3). */
export const MAX_DEPARTMENT_COUNT = 50;

/** V8 hash prefix (mirror ABC_HASH_PREFIX + VALIDATION_HASH_PREFIX + CCR_HASH_PREFIX). */
export const ABC_HASH_PREFIX = "sha256:";
export const ABC_HASH_LENGTH = 64;
export const ABC_HASH_REGEX = /^[0-9a-f]{64}$/;

/** Korean SSOT constants — ko-KR.json SSOT CR 11-4 D-002 fallback. */
export const ABC_EMPTY_DEPARTMENTS_KO =
  "ABC 부서가 등록되지 않았습니다";
export const ABC_TOO_MANY_DEPARTMENTS_KO =
  "ABC 부서 수가 한도를 초과했습니다";

/** engine_type tag discriminator Literal (Pydantic v2 verbatim — AD-19 dual-route). */
export type EngineTypeTag = "trad" | "abc";

// ── DispatchState (mirror pure kernel frozen dataclass) ──────────

/** PRD §F9.3 + AD-19 — M3 dispatch decision state (V8 determinism). */
export interface DispatchState {
  tenant_industry: string;
  resolved_engine_type: EngineTypeTag; // Literal["trad", "abc"] tag discriminator
  reason: string;
  hash: string; // sha256:64-hex (V8 determinism)
}

// ── V7Verdict (mirror pure kernel frozen dataclass) ──────────────

/** PRD §A6 + §V7 verbatim — Σ breakdown + unused = Σ department. */
export interface V7Verdict {
  is_balanced: boolean;
  breakdown_sum: string; // Decimal-as-string (KRW integer)
  unused_cost: string; // Decimal-as-string (KRW integer)
  expected_sum: string; // Decimal-as-string (KRW integer)
  delta_krw: string; // Decimal-as-string (KRW integer)
  hash: string; // sha256:64-hex
}

// ── MultiDepartmentCcrResult (mirror pure kernel frozen dataclass) ─

/** PRD §F9.3 — multi-department CCR aggregation summary. */
export interface MultiDepartmentCcrResult {
  ccr_results: CCRSummary[];
  total_department_cost: string; // Decimal-as-string
  total_capacity_hours: string; // Decimal-as-string
  aggregate_hash: string; // sha256:64-hex
}

export interface CCRSummary {
  department_id: string;
  ccr_per_hour: string; // Decimal-as-string
  hash: string; // sha256:64-hex
}

// ── DepartmentAllocation (mirror pure kernel frozen dataclass) ───

/** PRD §F9.3 — per-department allocation summary (V7 verdict + CCR + allocation). */
export interface DepartmentAllocation {
  department_id: string;
  ccr: CCRSummary;
  v7_verdict: V7Verdict;
}

// ── UnusedCapacitySubRow (mirror pure kernel frozen dataclass) ───

/** PRD §A9 verbatim — per-department 미사용능력 sub-row. */
export interface UnusedCapacitySubRow {
  department_id: string;
  unused_hours: string; // Decimal-as-string
  unused_cost_krw: string; // Decimal-as-string
  hash: string; // sha256:64-hex
}

// ── AllocationOutcomeABC (mirror m3_calculate/schemas.py wire) ───

/** CalcAbcResponse.allocation_outcome wire envelope (PRD §F9.3 + A29 forward-lock). */
export interface AllocationOutcomeABC {
  breakdown: CostObjectBreakdownRow[];
  unused_capacity: UnusedCapacitySubRowBlock;
  v7_verdict: V7Verdict;
  ccr: CCRBlock;
  is_balanced: boolean;
}

export interface CostObjectBreakdownRow {
  department_id: string;
  product_id: string;
  activity_id: string;
  driver_id: string;
  allocated_krw: string; // Decimal-as-string
}

export interface UnusedCapacitySubRowBlock {
  rows: UnusedCapacitySubRow[];
  is_balanced: boolean;
  delta_krw: string; // Decimal-as-string
}

export interface CCRBlock {
  departments: CCRSummary[];
}

// ── CalcAbcResponse (mirror m3_calculate/schemas.py discriminated union member) ─

/** POST /api/v1/calc success envelope for service industry (engine_type='abc' tag). */
export interface CalcAbcResponse {
  engine_type: "abc";
  tenant_id: string;
  period_key: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  baseline_revision: number;
  allocation_outcome: AllocationOutcomeABC;
  snapshot_id: string;
  result_hash: string;
  state: "verified";
  trace_id: string;
  verdict: VerdictWire;
}

// ── VerdictWire (mirror m3_calculate/schemas.py Verdict envelope) ─

export interface VerdictWire {
  verification_status: "passed" | "failed";
  verifications: VerificationItemWire[];
  top_failure: VerificationItemWire | null;
  trace_id: string;
}

export interface VerificationItemWire {
  code: "V1" | "V4" | "V7" | "V8";
  status: "passed" | "failed";
  message_ko: string;
  details: Record<string, unknown>;
}

// ── CalcResponse (mirror m3_calculate/schemas.py trad path) ──────

export interface CalcResponse {
  // Note: trad path uses engine_type implicitly (no explicit tag).
  // M3 orchestrator's `_resolve_engine_type` discriminates.
  tenant_id: string;
  period_key: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  baseline_revision: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  material_cost: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  labor_cost: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  overhead_cost: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  manufacturing_cost: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  inventory_adjustment: number;
  result_hash: string;
  state: "verified";
  trace_id: string;
  verdict: VerdictWire;
}

// ── Discriminated union envelope (Pydantic v2 + FastAPI tag) ─────

export type CalcOutcomeResponse = CalcResponse | CalcAbcResponse;

/** Type guard — narrow to ABC path at handler boundary. */
export function isCalcAbcResponse(
  outcome: CalcOutcomeResponse,
): outcome is CalcAbcResponse {
  return "engine_type" in outcome && outcome.engine_type === "abc";
}

/** Type guard — narrow to trad path. */
export function isCalcResponse(
  outcome: CalcOutcomeResponse,
): outcome is CalcResponse {
  return !("engine_type" in outcome);
}
