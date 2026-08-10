// apps/web/lib/m11-snapshot-persistence.ts — Story 11.4 (A13 sprint-up) TS mirror.
//
// M11 snapshot persistence TS projection (AD-15 §11 SSOT parity with
// `packages/services/m11_close/commit_snapshot_persistence.py`).
//
// Drift caught by `apps/web/lib/m11-snapshot-persistence-parity.ts`
// (vitest cross-language parity test).
//
// AD-20 state machine: draft → verified → committed → reversed.
//
// Korean message SSOT (single source of truth for ko-KR.json parity):
// - SNAPSHOT_COMMIT_OK_KO mirrors Python `SNAPSHOT_COMMIT_OK_KO`.
// - SNAPSHOT_COMMIT_IDEMPOTENT_KO mirrors Python `SNAPSHOT_COMMIT_IDEMPOTENT_KO`.
// - SNAPSHOT_COMMIT_DRAFT_REJECT_KO mirrors Python `SNAPSHOT_COMMIT_DRAFT_REJECT_KO`.
// - SNAPSHOT_COMMIT_REVERSED_REJECT_KO mirrors Python `SNAPSHOT_COMMIT_REVERSED_REJECT_KO`.

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const SNAPSHOT_COMMIT_OK_KO = "스냅샷 영구화 완료" as const;
export const SNAPSHOT_COMMIT_IDEMPOTENT_KO =
  "스냅샷 이미 영구화됨 — 멱등 처리" as const;
export const SNAPSHOT_COMMIT_DRAFT_REJECT_KO =
  "스냅샷이 검증 전 상태 — 영구화 불가" as const;
export const SNAPSHOT_COMMIT_REVERSED_REJECT_KO =
  "스냅샷이 이미 역분개됨 — 영구화 불가" as const;

// ── Snapshot state constants (AD-20 lifecycle) ──────────────────
export const SNAPSHOT_STATE_DRAFT = "draft" as const;
export const SNAPSHOT_STATE_VERIFIED = "verified" as const;
export const SNAPSHOT_STATE_COMMITTED = "committed" as const;
export const SNAPSHOT_STATE_REVERSED = "reversed" as const;

export const SNAPSHOT_STATES = [
  SNAPSHOT_STATE_DRAFT,
  SNAPSHOT_STATE_VERIFIED,
  SNAPSHOT_STATE_COMMITTED,
  SNAPSHOT_STATE_REVERSED,
] as const;

export type SnapshotState = (typeof SNAPSHOT_STATES)[number];

// ── State transition whitelist ──────────────────────────────────
export const VALID_COMMIT_FROM_STATE: ReadonlySet<SnapshotState> = new Set([
  SNAPSHOT_STATE_VERIFIED,
]);
export const IDEMPOTENT_NOOP_STATE: ReadonlySet<SnapshotState> = new Set([
  SNAPSHOT_STATE_COMMITTED,
]);
export const TERMINAL_STATE: ReadonlySet<SnapshotState> = new Set([
  SNAPSHOT_STATE_REVERSED,
]);
export const NON_COMMITTABLE_FROM_STATE: ReadonlySet<SnapshotState> = new Set([
  SNAPSHOT_STATE_DRAFT,
]);

// ── Error codes (mirror Python ERROR_CODE_*) ────────────────────
export const ERROR_CODE_INVALID_INPUT = "INVALID_COMMIT_INPUT" as const;
export const ERROR_CODE_DRAFT_NOT_COMMITTABLE =
  "SNAPSHOT_DRAFT_NOT_COMMITTABLE" as const;
export const ERROR_CODE_ALREADY_REVERSED = "SNAPSHOT_ALREADY_REVERSED" as const;

// ── SnapshotPersistenceState (TS view model) ────────────────────
// Frontend projection of the commit decision (commit_panel UI).
export interface SnapshotPersistenceState {
  authorized: boolean;
  idempotent_ok: boolean;
  terminal_rejected: boolean;
  commit_from_state: SnapshotState;
  snapshot_id: string;
  period_key: string;
  actor_id: string;
  tenant_id: string;
  reject_reason_ko: string | null;
}

// ── validate_commit_snapshot_persistence (TS mirror) ────────────
// Mirrors Python `validate_commit_snapshot_persistence` pure kernel.
// Decides whether AD-20 verified → committed transition is permitted.
export function buildSnapshotPersistenceState(input: {
  snapshot_id: string;
  period_key: string;
  current_state: SnapshotState;
  actor_id: string;
  tenant_id: string;
}): SnapshotPersistenceState {
  if (!input.snapshot_id) {
    return {
      authorized: false,
      idempotent_ok: false,
      terminal_rejected: false,
      commit_from_state: input.current_state,
      snapshot_id: input.snapshot_id,
      period_key: input.period_key,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
      reject_reason_ko: ERROR_CODE_INVALID_INPUT,
    };
  }
  if (!input.period_key) {
    return {
      authorized: false,
      idempotent_ok: false,
      terminal_rejected: false,
      commit_from_state: input.current_state,
      snapshot_id: input.snapshot_id,
      period_key: input.period_key,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
      reject_reason_ko: ERROR_CODE_INVALID_INPUT,
    };
  }

  // Idempotent no-op: snapshot already committed.
  if (IDEMPOTENT_NOOP_STATE.has(input.current_state)) {
    return {
      authorized: true,
      idempotent_ok: true,
      terminal_rejected: false,
      commit_from_state: input.current_state,
      snapshot_id: input.snapshot_id,
      period_key: input.period_key,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
      reject_reason_ko: null,
    };
  }

  // Terminal state: cannot re-commit a reversed snapshot.
  if (TERMINAL_STATE.has(input.current_state)) {
    return {
      authorized: false,
      idempotent_ok: false,
      terminal_rejected: true,
      commit_from_state: input.current_state,
      snapshot_id: input.snapshot_id,
      period_key: input.period_key,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
      reject_reason_ko: SNAPSHOT_COMMIT_REVERSED_REJECT_KO,
    };
  }

  // Non-committable state: 'draft'.
  if (NON_COMMITTABLE_FROM_STATE.has(input.current_state)) {
    return {
      authorized: false,
      idempotent_ok: false,
      terminal_rejected: false,
      commit_from_state: input.current_state,
      snapshot_id: input.snapshot_id,
      period_key: input.period_key,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
      reject_reason_ko: SNAPSHOT_COMMIT_DRAFT_REJECT_KO,
    };
  }

  // Valid: state='verified' → authorized commit transition.
  if (VALID_COMMIT_FROM_STATE.has(input.current_state)) {
    return {
      authorized: true,
      idempotent_ok: false,
      terminal_rejected: false,
      commit_from_state: input.current_state,
      snapshot_id: input.snapshot_id,
      period_key: input.period_key,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
      reject_reason_ko: null,
    };
  }

  // D-005 — explicit unknown state rejection (parity with Python).
  // Mirrors Python `validate_commit_snapshot_persistence` which raises
  // ERROR_CODE_INVALID_INPUT for any state not in IDEMPOTENT_NOOP /
  // TERMINAL / NON_COMMITTABLE_FROM / VALID_COMMIT_FROM. Defense-in-depth.
  return {
    authorized: false,
    idempotent_ok: false,
    terminal_rejected: false,
    commit_from_state: input.current_state,
    snapshot_id: input.snapshot_id,
    period_key: input.period_key,
    actor_id: input.actor_id,
    tenant_id: input.tenant_id,
    reject_reason_ko: ERROR_CODE_INVALID_INPUT,
  };
}

// ── isCommitAllowed (defense-in-depth gate) ─────────────────────
export function isCommitAllowed(state: SnapshotPersistenceState): boolean {
  return state.authorized;
}

// ── formatCommitResultKo (Korean SSOT for commit outcome) ───────
export function formatCommitResultKo(state: SnapshotPersistenceState): string {
  if (state.idempotent_ok) return SNAPSHOT_COMMIT_IDEMPOTENT_KO;
  if (!state.authorized) return state.reject_reason_ko ?? "";
  return SNAPSHOT_COMMIT_OK_KO;
}