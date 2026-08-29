// apps/web/lib/m11-close-sequence.ts — Story 11.4 (A13 sprint-up) TS mirror.
//
// M11 close sequence lock TS projection (AD-15 §11 SSOT parity with
// `packages/services/m11_close/close_sequence_order.py` +
// `close_sequence_state.py`).
//
// Drift caught by `apps/web/lib/m11-close-sequence-parity.ts`.
//
// Korean message SSOT (single source of truth for ko-KR.json parity):
// - DIVISIONS_MISSING_KO mirrors Python `DIVISIONS_MISSING_KO`.
// - MANUFACTURING_MISSING_KO mirrors Python `MANUFACTURING_MISSING_KO`.
// - ABC_MISSING_KO mirrors Python `ABC_MISSING_KO`.
// - COMMON_MISSING_KO mirrors Python `COMMON_MISSING_KO`.
// - ALL_STAGES_REQUIRED_KO mirrors Python `ALL_STAGES_REQUIRED_KO`.
// - CHRONOLOGICAL_VIOLATION_KO mirrors Python `CHRONOLOGICAL_VIOLATION_KO`.
//
// AD-6 close lock PRIMARY guard (PRD §F11.1 + §8.M11(a)) — 4-stage close
// sequence: divisions → manufacturing → abc → common → confirmed. The
// sequence is 1-way; each step's completion timestamp must be
// chronologically ordered (or NULL). Defense-in-depth against
// stage-skipping.
//
// AD-6 INSERT refusal (Architecture Spine §AD-6) — `check_ad6_insert_allowed`
// gates business-data INSERTs into monthly_input_periods / monthly_input_rows
// / inventory_ledger / fiscal_period_snapshots. AD-22 reversal/correction
// events (reversal_negating + reversal_corrected) are EXPLICITLY allowed
// past the close lock (PRD §F11.2 / §AD-6 exception clause).

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const DIVISIONS_MISSING_KO = "divisions 단계 미완료" as const;
export const MANUFACTURING_MISSING_KO = "manufacturing 단계 미완료" as const;
export const ABC_MISSING_KO = "abc 단계 미완료" as const;
export const COMMON_MISSING_KO = "common 단계 미완료" as const;
export const ALL_STAGES_REQUIRED_KO = "4단계 모두 완료 후 마감 가능" as const;
export const CHRONOLOGICAL_VIOLATION_KO =
  "단계 완료 시각이 순서대로여야 합니다" as const;

// ── Close sequence stages (PRD §F11.1 canonical order) ───────────
export const CLOSE_SEQUENCE_STAGES = [
  "divisions",
  "manufacturing",
  "abc",
  "common",
  "confirmed",
] as const;

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type CloseSequenceStage = (typeof CLOSE_SEQUENCE_STAGES)[number];

// ── Step timestamp attribute pairing (PRD §F11.1) ───────────────
export const STEP_TIMESTAMP_ATTRS = [
  "divisions_completed_at",
  "manufacturing_completed_at",
  "abc_completed_at",
  "common_completed_at",
] as const;

// ── Error code constants (AD-15 §4 typed envelope) ──────────────
export const ERROR_CODE_NON_CHRONOLOGICAL = "STAGE_NOT_CHRONOLOGICAL" as const;
export const ERROR_CODE_UNKNOWN_STAGE = "UNKNOWN_STAGE_NAME" as const;

// ── CloseSequenceOrderResult (mirror of Python NamedTuple) ──────
export interface CloseSequenceOrderResult {
  valid: boolean;
  violations: readonly string[];
  next_step: CloseSequenceStage | null;
  reject_reason_ko: string | null;
}

// ── validate_close_sequence_order (TS mirror) ───────────────────
// Mirrors Python `validate_close_sequence_order` pure kernel. AD-1/AD-11
// parity (pure-Python, no I/O, no clock). The TS version receives
// completion timestamps explicitly (no Date.now()).
export function validateCloseSequenceOrder(input: {
  divisions_completed_at: string | null; // ISO-8601 UTC string
  manufacturing_completed_at: string | null;
  abc_completed_at: string | null;
  common_completed_at: string | null;
}): CloseSequenceOrderResult {
  const timestamps: ReadonlyArray<readonly [string, string | null]> = [
    ["divisions", input.divisions_completed_at],
    ["manufacturing", input.manufacturing_completed_at],
    ["abc", input.abc_completed_at],
    ["common", input.common_completed_at],
  ];

  const violations: string[] = [];
  // Rule 1: forward-jump detection (chronological ordering).
  for (let i = 0; i < timestamps.length - 1; i++) {
    const [prevName, prevTs] = timestamps[i];
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [currName, currTs] = timestamps[i + 1];
    if (prevTs === null && currTs !== null) {
      violations.push(`${prevName} 단계 미완료`);
    } else if (
      prevTs !== null &&
      currTs !== null &&
      new Date(currTs).getTime() < new Date(prevTs).getTime()
    ) {
      violations.push(CHRONOLOGICAL_VIOLATION_KO);
    }
  }

  // Rule 2: next_step = first incomplete stage.
  let nextStep: CloseSequenceStage | null = null;
  for (const [stageName, ts] of timestamps) {
    if (ts === null) {
      nextStep = stageName as CloseSequenceStage;
      break;
    }
  }
  if (nextStep === null) {
    nextStep = "confirmed";
  }

  if (violations.length > 0) {
    return {
      valid: false,
      violations,
      next_step: nextStep,
      reject_reason_ko: ALL_STAGES_REQUIRED_KO,
    };
  }

  return {
    valid: true,
    violations: [],
    next_step: nextStep,
    reject_reason_ko: null,
  };
}

// ── AD-6 INSERT guard types + constants ─────────────────────────
// TargetTable (4 AD-6 locked tables) + TargetEventType (10 events).
export const AD6_LOCKED_TABLES = [
  "monthly_input_periods",
  "monthly_input_rows",
  "inventory_ledger",
  "fiscal_period_snapshots",
] as const;

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type TargetTable = (typeof AD6_LOCKED_TABLES)[number];

export const REVERSAL_TARGET_EVENT_TYPES = [
  "reversal_negating",
  "reversal_corrected",
] as const;

export type ReversalTargetEventType =
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  (typeof REVERSAL_TARGET_EVENT_TYPES)[number];

// ── Ad6InsertGuardResult (mirror of Python NamedTuple) ───────────
export interface Ad6InsertGuardResult {
  allowed: boolean;
  reject_reason_ko: string | null;
  guard_type: "ALLOWED" | "CLOSED_LOCK" | "REVERSAL_EXCEPTION";
}

// ── check_ad6_insert_allowed (TS mirror) ────────────────────────
// Mirrors Python `check_ad6_insert_allowed` from close_sequence_state.py.
// Decides whether an INSERT is permitted under AD-6 close lock.
export function checkAd6InsertAllowed(input: {
  close_sequence_state: CloseSequenceStage;
  target_table: string;
  target_event_type: string;
}): Ad6InsertGuardResult {
  // Non-confirmed state → allow (no lock active yet).
  if (input.close_sequence_state !== "confirmed") {
    return { allowed: true, reject_reason_ko: null, guard_type: "ALLOWED" };
  }

  // Confirmed state → AD-6 lock active.
  // AD-22 reversal/correction events pass through explicitly.
  if (
    (REVERSAL_TARGET_EVENT_TYPES as readonly string[]).includes(
      input.target_event_type,
    )
  ) {
    return {
      allowed: true,
      reject_reason_ko: null,
      guard_type: "REVERSAL_EXCEPTION",
    };
  }

  // Business-data tables in 'confirmed' state → BLOCKED.
  if ((AD6_LOCKED_TABLES as readonly string[]).includes(input.target_table)) {
    return {
      allowed: false,
      reject_reason_ko: "마감이 확정되어 입력이 거부됩니다 (AD-6)",
      guard_type: "CLOSED_LOCK",
    };
  }

  // Tables not in AD-6 lock set (audit_logs, verification_log, reversal_log)
  // are allowed even in 'confirmed' state — bookkeeping tables.
  return { allowed: true, reject_reason_ko: null, guard_type: "ALLOWED" };
}

// ── compute_close_sequence_state (TS mirror) ────────────────────
// Mirrors Python `compute_close_sequence_state` from close_sequence_state.py.
// Returns the close_sequence_state string given step timestamps.
export function computeCloseSequenceState(input: {
  divisions_completed_at: string | null;
  manufacturing_completed_at: string | null;
  abc_completed_at: string | null;
  common_completed_at: string | null;
  closed_at: string | null;
}): CloseSequenceStage {
  const completedCount = [
    input.divisions_completed_at,
    input.manufacturing_completed_at,
    input.abc_completed_at,
    input.common_completed_at,
  ].filter((ts) => ts !== null).length;

  if (completedCount === 0) return "divisions";
  if (completedCount === 1) return "manufacturing";
  if (completedCount === 2) return "abc";
  if (completedCount === 3) return "common";
  // 4 steps done.
  if (input.closed_at !== null) return "confirmed";
  return "common";
}

// ── Format helper for close sequence state display ───────────────
// Returns the Korean SSOT message for the given stage. Mirrors Python
// `format_close_sequence_state_ko` (if present) or the per-stage KO constants.
export function formatCloseSequenceStateKo(state: CloseSequenceStage): string {
  switch (state) {
    case "divisions":
      return DIVISIONS_MISSING_KO;
    case "manufacturing":
      return MANUFACTURING_MISSING_KO;
    case "abc":
      return ABC_MISSING_KO;
    case "common":
      return COMMON_MISSING_KO;
    case "confirmed":
      return "마감 확정";
  }
}