// apps/web/lib/m11-snapshot-persistence-parity.ts — Story 11.4 (A13 sprint-up) vitest parity.
//
// Cross-language parity test (Python pure kernel ↔ TS mirror) for snapshot
// persistence (AD-20 verified → committed transition).
//
// Drift caught between:
// - `packages/services/m11_close/commit_snapshot_persistence.py` (Python)
// - `apps/web/lib/m11-snapshot-persistence.ts` (TS mirror)
//
// Run via: `pnpm exec vitest run m11-snapshot-persistence-parity`

import { describe, expect, it } from "vitest";

import {
  SNAPSHOT_COMMIT_DRAFT_REJECT_KO,
  SNAPSHOT_COMMIT_IDEMPOTENT_KO,
  SNAPSHOT_COMMIT_OK_KO,
  SNAPSHOT_COMMIT_REVERSED_REJECT_KO,
  buildSnapshotPersistenceState,
  formatCommitResultKo,
  isCommitAllowed,
} from "../../lib/m11-snapshot-persistence";

const SNAPSHOT_ID = "11111111-1111-4111-8111-111111111111";
const TENANT_ID = "22222222-2222-4222-8222-222222222222";
const ACTOR_ID = "33333333-3333-4333-8333-333333333333";
const PERIOD_KEY = "2026-08";

describe("m11-snapshot-persistence parity — buildSnapshotPersistenceState", () => {
  it("parity 1: state='verified' → authorized + idempotent_ok=false + ok KO", () => {
    const state = buildSnapshotPersistenceState({
      snapshot_id: SNAPSHOT_ID,
      period_key: PERIOD_KEY,
      current_state: "verified",
      actor_id: ACTOR_ID,
      tenant_id: TENANT_ID,
    });
    expect(state.authorized).toBe(true);
    expect(state.idempotent_ok).toBe(false);
    expect(state.terminal_rejected).toBe(false);
    expect(state.reject_reason_ko).toBeNull();
    expect(formatCommitResultKo(state)).toBe(SNAPSHOT_COMMIT_OK_KO);
    expect(isCommitAllowed(state)).toBe(true);
  });

  it("parity 2: state='committed' → authorized + idempotent_ok=true + IDEMPOTENT_KO", () => {
    const state = buildSnapshotPersistenceState({
      snapshot_id: SNAPSHOT_ID,
      period_key: PERIOD_KEY,
      current_state: "committed",
      actor_id: ACTOR_ID,
      tenant_id: TENANT_ID,
    });
    expect(state.authorized).toBe(true);
    expect(state.idempotent_ok).toBe(true);
    expect(state.terminal_rejected).toBe(false);
    expect(formatCommitResultKo(state)).toBe(SNAPSHOT_COMMIT_IDEMPOTENT_KO);
  });

  it("parity 3: state='reversed' → terminal_rejected + REVERSED_REJECT_KO", () => {
    const state = buildSnapshotPersistenceState({
      snapshot_id: SNAPSHOT_ID,
      period_key: PERIOD_KEY,
      current_state: "reversed",
      actor_id: ACTOR_ID,
      tenant_id: TENANT_ID,
    });
    expect(state.authorized).toBe(false);
    expect(state.terminal_rejected).toBe(true);
    expect(state.reject_reason_ko).toBe(SNAPSHOT_COMMIT_REVERSED_REJECT_KO);
  });

  it("parity 4: state='draft' → not authorized + DRAFT_REJECT_KO", () => {
    const state = buildSnapshotPersistenceState({
      snapshot_id: SNAPSHOT_ID,
      period_key: PERIOD_KEY,
      current_state: "draft",
      actor_id: ACTOR_ID,
      tenant_id: TENANT_ID,
    });
    expect(state.authorized).toBe(false);
    expect(state.terminal_rejected).toBe(false);
    expect(state.reject_reason_ko).toBe(SNAPSHOT_COMMIT_DRAFT_REJECT_KO);
  });

  it("parity 5: empty snapshot_id → INVALID_COMMIT_INPUT error_code", () => {
    const state = buildSnapshotPersistenceState({
      snapshot_id: "",
      period_key: PERIOD_KEY,
      current_state: "verified",
      actor_id: ACTOR_ID,
      tenant_id: TENANT_ID,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe("INVALID_COMMIT_INPUT");
  });
});