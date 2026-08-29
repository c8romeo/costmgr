// apps/web/lib/m8-budget-scenario.ts — Story 8.1 (Epic 8)
//
// M8 budget scenario TS projection (AD-15 §11 SSOT parity with
// `apps/api/modules/m8_budget/services/budget_scenario_service.py`).
//
// Frontend mirror of the POST/GET /api/v1/budget/scenarios response.
// Drift caught by parity tests in `apps/web/__tests__/lib/m8-budget-scenario-parity.test.ts`.

// ── Constants (AD-24 + PRD §F8.1 verbatim) ─────────────────────
// Real fiscal period key pattern — `^\d{4}-(0[1-9]|1[0-2])$`.
// Mirrors Python `packages/cost_engine/budget_period_key.py::REAL_PERIOD_KEY_PATTERN`.
export const REAL_PERIOD_KEY_PATTERN: RegExp = /^\d{4}-(0[1-9]|1[0-2])$/;

// Virtual budget period key pattern — `^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*$`.
// Mirrors Python `VIRTUAL_BUDGET_PERIOD_KEY_PATTERN`.
export const VIRTUAL_BUDGET_PERIOD_KEY_PATTERN: RegExp =
  /^(\d{4})-(0[1-9]|1[0-2])#B([1-9]\d*)$/;

// 1차 MVP scenario 한도 (PRD §F8.1 verbatim + §15 NON-GOAL #2).
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const MVP_MAX_SCENARIOS_PER_TENANT: number = 1;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const MVP_SCENARIO_INDEX: number = 1;

// Korean SSOT message (HTTP 409 SCENARIO_LIMIT_EXCEEDED envelope).
// Mirrors Python `SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO`.
export const SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO: string =
  "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)";

// ── Serialized scenario (TS view model) ─────────────────────────
// Mirror `apps/api/modules/m8_budget/schemas.py::BudgetScenarioSerialized`.
// Decimal-as-string + UUID-as-string parity (AD-8 + AD-15 §1).
export interface BudgetScenarioSerialized {
  id: string; // UUID v7
  tenant_id: string; // UUID
  period_key: string; // AD-24 virtual: YYYY-MM#B<n>
  real_period_key: string; // AD-24 real: YYYY-MM
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  scenario_index: number; // 1차 MVP = 1 only
  scenario_hash: string; // V8 determinism sha256:32hex
  created_by: string; // UUID
  created_at_kst: string; // ISO 8601
}

// ── Wire payload types ──────────────────────────────────────────
export interface CreateBudgetScenarioRequest {
  real_period_key: string;
}

export interface BudgetScenarioResponse {
  scenario: BudgetScenarioSerialized;
}

export interface BudgetScenarioListResponse {
  scenarios: BudgetScenarioSerialized[];
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total_count: number;
  trace_id: string | null;
}

// ── Error code SSOT (CR 12-5 D-14 typed envelope) ───────────────
// Mirrors Python main.py handler `code` field.
export const ERROR_CODE_SCENARIO_LIMIT_EXCEEDED: string =
  "SCENARIO_LIMIT_EXCEEDED" as const;
export const ERROR_CODE_INVALID_VIRTUAL_BUDGET_PERIOD_KEY: string =
  "INVALID_VIRTUAL_BUDGET_PERIOD_KEY" as const;
export const ERROR_CODE_BUDGET_SCENARIO_NOT_FOUND: string =
  "BUDGET_SCENARIO_NOT_FOUND" as const;

// ── Pure validators (mirrors kernel regex) ──────────────────────
/**
 * Validate real period key (AD-24 §6.1) — `YYYY-MM` format.
 * Returns true if the input matches the canonical real pattern.
 */
export function isValidRealPeriodKeyTS(value: string): boolean {
  return typeof value === "string" && REAL_PERIOD_KEY_PATTERN.test(value);
}

/**
 * Validate virtual budget period key (AD-24 §6.2) — `YYYY-MM#B<n>` format.
 * Returns true if the input matches the canonical virtual pattern.
 */
// eslint-disable-next-line camelcase
export function isValidVirtualBudgetPeriodKeyTS(period_key: string): boolean {
  return (
    // eslint-disable-next-line camelcase
    typeof period_key === "string" &&
    VIRTUAL_BUDGET_PERIOD_KEY_PATTERN.test(period_key)
  );
}

/**
 * Parse virtual budget period key into parts (AD-24 §6.2).
 * Returns null if invalid.
 */
export interface BudgetPeriodKeyPartsTS {
  real_period_key: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  scenario_index: number;
  scenario_suffix: string;
}

export function parseVirtualBudgetPeriodKeyTS(
  // eslint-disable-next-line camelcase
  period_key: string,
): BudgetPeriodKeyPartsTS | null {
  if (!isValidVirtualBudgetPeriodKeyTS(period_key)) {
    return null;
  }
  const match = VIRTUAL_BUDGET_PERIOD_KEY_PATTERN.exec(period_key);
  if (!match) {
    return null;
  }
  const year = match[1];
  const month = match[2];
  // eslint-disable-next-line @typescript-eslint/naming-convention, camelcase
  const scenario_index = parseInt(match[3], 10);
  // eslint-disable-next-line camelcase
  if (scenario_index > MVP_SCENARIO_INDEX) {
    return null; // 1차 MVP 한도
  }
  return {
    real_period_key: `${year}-${month}`,
    // eslint-disable-next-line camelcase
    scenario_index,
    // eslint-disable-next-line camelcase
    scenario_suffix: `#B${scenario_index}`,
  };
}

/**
 * Derive virtual budget period key from real period key (AD-24 §6.2).
 * Returns null if real_period_key is invalid OR scenario_index > 1.
 *
 * Mirrors Python `packages.cost_engine.budget_period_key.py::derive_budget_period_key`.
 */
export function deriveBudgetPeriodKeyTS(
  // eslint-disable-next-line camelcase
  real_period_key: string,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  // eslint-disable-next-line camelcase
  scenario_index: number = MVP_SCENARIO_INDEX,
): string | null {
  if (!isValidRealPeriodKeyTS(real_period_key)) {
    return null;
  }
  // eslint-disable-next-line camelcase
  if (!Number.isInteger(scenario_index) || scenario_index < 1) {
    return null;
  }
  // eslint-disable-next-line camelcase
  if (scenario_index > MVP_SCENARIO_INDEX) {
    return null; // 1차 MVP 한도
  }
  // eslint-disable-next-line camelcase
  return `${real_period_key}#B${scenario_index}`;
}

/**
 * Validate scenario uniqueness (1차 MVP = 1).
 * Returns the typed error message if limit exceeded; null otherwise.
 *
 * Mirrors Python `validate_scenario_uniqueness`.
 */
export function validateScenarioUniquenessTS(
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  // eslint-disable-next-line camelcase
  existing_count: number,
): string | null {
  // eslint-disable-next-line camelcase
  if (!Number.isInteger(existing_count) || existing_count < 0) {
    return "existing_count must be a non-negative integer";
  }
  // eslint-disable-next-line camelcase
  if (existing_count >= MVP_MAX_SCENARIOS_PER_TENANT) {
    return SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO;
  }
  return null;
}

// ── TS JSON-safe serializer (AD-15 §1 + AD-8 parity) ───────────
// Mirror Python `packages/services/m8_budget/budget_period_key_serializers.py`.
export function serializeBudgetScenarioTS(
  scenario: BudgetScenarioSerialized,
// eslint-disable-next-line @typescript-eslint/no-restricted-types
): Record<string, string | number> {
  return {
    id: String(scenario.id),
    tenant_id: String(scenario.tenant_id),
    period_key: String(scenario.period_key),
    real_period_key: String(scenario.real_period_key),
    scenario_index: Number(scenario.scenario_index),
    scenario_hash: String(scenario.scenario_hash),
    created_by: String(scenario.created_by),
    created_at_kst: String(scenario.created_at_kst),
  };
}