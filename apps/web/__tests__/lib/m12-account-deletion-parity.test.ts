// apps/web/__tests__/lib/m12-account-deletion-parity.test.ts — Story 12.3
//
// Cross-language parity test (Python pure kernel ↔ TS mirror) for the
// M12 account deletion subsystem. The kernel SSOT is at
// `packages/services/m12_account/account_deletion.py`. The TS mirror
// at `apps/web/lib/m12-account-deletion.ts` MUST stay in lockstep —
// drift is caught by
// `tests/integration/test_m12_account_deletion_cross_language_drift.py`
// (D-13 + D-PARITY-01 pattern).
//
// Composition parity: buildDeletionEnvelope + canTransitionStatus +
// getStatusLabel + daysUntilHardDelete.
//
// Pattern mirrors `m12-two-factor-gate-parity.test.ts` (Story 12.5).
//
// 12 cases:
//   parity 1: TenantDeletionStatus enum (3 values)
//   parity 2: canTransitionStatus active→pending_deletion → true
//   parity 3: canTransitionStatus pending_deletion→active → true
//   parity 4: canTransitionStatus pending_deletion→deleted → true
//   parity 5: canTransitionStatus active→deleted → false (must go via PENDING)
//   parity 6: canTransitionStatus DELETED→ANY → false (terminal)
//   parity 7: buildDeletionEnvelope returns correct schema_version
//   parity 8: buildDeletionEnvelope tenant_id + status pass-through
//   parity 9: getStatusLabel active → "활성"
//   parity 10: getStatusLabel pending_deletion → "삭제 대기"
//   parity 11: getStatusLabel deleted → "삭제 완료"
//   parity 12: getStatusLabel unknown → throws (CR 11-4 D-005)

import { describe, expect, it } from "vitest";

import {
  DELETION_CHALLENGE_TOKEN_PURPOSE,
  DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
  DELETION_CONSENT_TEMPLATE_KO,
  DELETION_ENVELOPE_SCHEMA_VERSION,
  RETENTION_DAYS,
  TenantDeletionStatus,
  AccountDeletionAction,
  buildDeletionEnvelope,
  canTransitionStatus,
  daysUntilHardDelete,
  getStatusLabel,
} from "../../lib/m12-account-deletion";

describe("m12-account-deletion parity — TS mirror of Python kernel", () => {
  // ── 1. Constants parity (mirror packages/services/m12_account/account_deletion.py)
  it("parity 1: RETENTION_DAYS / DELETION_ENVELOPE_SCHEMA_VERSION / TTL / PURPOSE", () => {
    expect(RETENTION_DAYS).toBe(30);
    expect(DELETION_ENVELOPE_SCHEMA_VERSION).toBe("1.0");
    expect(DELETION_CHALLENGE_TOKEN_TTL_SECONDS).toBe(300);
    expect(DELETION_CHALLENGE_TOKEN_PURPOSE).toBe("account_deletion");
    expect(DELETION_CONSENT_TEMPLATE_KO).toBe(
      "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다",
    );
  });

  // ── 2. TenantDeletionStatus enum (3 values)
  it("parity 2: TenantDeletionStatus enum has 3 values", () => {
    expect(TenantDeletionStatus.ACTIVE).toBe("active");
    expect(TenantDeletionStatus.PENDING_DELETION).toBe("pending_deletion");
    expect(TenantDeletionStatus.DELETED).toBe("deleted");
    const keys = Object.keys(TenantDeletionStatus);
    expect(keys).toHaveLength(3);
  });

  // ── 3. canTransitionStatus FSM parity (Python: can_transition_status)
  it("parity 3: canTransitionStatus active → pending_deletion = true", () => {
    expect(
      canTransitionStatus(
        TenantDeletionStatus.ACTIVE,
        TenantDeletionStatus.PENDING_DELETION,
      ),
    ).toBe(true);
  });

  it("parity 4: canTransitionStatus pending_deletion → active = true", () => {
    expect(
      canTransitionStatus(
        TenantDeletionStatus.PENDING_DELETION,
        TenantDeletionStatus.ACTIVE,
      ),
    ).toBe(true);
  });

  it("parity 5: canTransitionStatus pending_deletion → deleted = true", () => {
    expect(
      canTransitionStatus(
        TenantDeletionStatus.PENDING_DELETION,
        TenantDeletionStatus.DELETED,
      ),
    ).toBe(true);
  });

  it("parity 6: canTransitionStatus active → deleted = false (must go via PENDING)", () => {
    expect(
      canTransitionStatus(
        TenantDeletionStatus.ACTIVE,
        TenantDeletionStatus.DELETED,
      ),
    ).toBe(false);
  });

  it("parity 7: canTransitionStatus DELETED is terminal (all transitions false)", () => {
    for (const target of Object.values(TenantDeletionStatus)) {
      expect(canTransitionStatus(TenantDeletionStatus.DELETED, target)).toBe(false);
    }
  });

  it("parity 8: canTransitionStatus FSM allows exactly 3 transitions (full grid)", () => {
    let allowedCount = 0;
    for (const current of Object.values(TenantDeletionStatus)) {
      for (const target of Object.values(TenantDeletionStatus)) {
        if (canTransitionStatus(current, target)) allowedCount++;
      }
    }
    expect(allowedCount).toBe(3);
  });

  // ── 4. buildDeletionEnvelope parity (Python: build_deletion_envelope)
  it("parity 9: buildDeletionEnvelope schema_version + envelope shape", () => {
    const env = buildDeletionEnvelope(
      "tenant-1",
      TenantDeletionStatus.PENDING_DELETION,
      "2026-08-15T10:00:00Z",
      "2026-09-14T10:00:00Z",
      "consent-1",
    );
    expect(env.schema_version).toBe("1.0");
    expect(env.tenant_id).toBe("tenant-1");
    expect(env.status).toBe("pending_deletion");
    expect(env.deletion_requested_at).toBe("2026-08-15T10:00:00Z");
    expect(env.deletion_scheduled_for).toBe("2026-09-14T10:00:00Z");
    expect(env.consent_id).toBe("consent-1");
  });

  it("parity 10: buildDeletionEnvelope active status passes through", () => {
    const env = buildDeletionEnvelope(
      "tenant-2",
      TenantDeletionStatus.ACTIVE,
      "",
      "",
      "",
    );
    expect(env.status).toBe("active");
  });

  // ── 5. getStatusLabel parity (Korean labels — exhaustiveness check CR 11-4 D-005)
  it("parity 11: getStatusLabel returns Korean label for each known status", () => {
    expect(getStatusLabel(TenantDeletionStatus.ACTIVE)).toBe("활성");
    expect(getStatusLabel(TenantDeletionStatus.PENDING_DELETION)).toBe("삭제 대기");
    expect(getStatusLabel(TenantDeletionStatus.DELETED)).toBe("삭제 완료");
  });

  it("parity 12: getStatusLabel throws on unknown status (CR 11-4 D-005)", () => {
    // Force a type-system bypass with `as` cast to simulate runtime unknown input
    const unknown = "unknown_state" as unknown as
      | typeof TenantDeletionStatus.ACTIVE
      | typeof TenantDeletionStatus.PENDING_DELETION
      | typeof TenantDeletionStatus.DELETED;
    expect(() => getStatusLabel(unknown)).toThrow(
      /Unknown TenantDeletionStatus/,
    );
  });

  // ── 6. daysUntilHardDelete + AccountDeletionAction sanity
  it("parity 13: daysUntilHardDelete returns null for null input", () => {
    expect(daysUntilHardDelete(null)).toBeNull();
  });

  it("parity 14: daysUntilHardDelete returns null for invalid date", () => {
    expect(daysUntilHardDelete("not-a-date")).toBeNull();
  });

  it("parity 15: AccountDeletionAction has 8 values", () => {
    const keys = Object.keys(AccountDeletionAction);
    expect(keys).toHaveLength(8);
    expect(AccountDeletionAction.DELETION_REQUESTED).toBe("deletion_requested");
    expect(AccountDeletionAction.DELETION_2FA_FAILED).toBe("deletion_2fa_failed");
  });
});