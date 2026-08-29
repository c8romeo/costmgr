// apps/web/lib/m12-account-deletion.ts — Story 12.3 TS mirror.
//
// Pure kernel SSOT parity for the M12 account deletion subsystem.
// Mirrors the Python pure kernel `packages/services/m12_account/account_deletion.py`.
// This file MUST stay in lockstep with the Python kernel — drift is
// caught by `tests/integration/test_m12_account_deletion_cross_language_drift.py`
// (cross-language drift detector, Story 12.3 T7 + CR 12-5 D-13 + D-PARITY-01 pattern).
//
// AD-15 §11 SSOT: ko-KR.json is the canonical Korean SSOT for user-visible
// strings (CR 11-4 D-002). These constants are the **non-i18n** numeric
// and enum constants that need to match Python 1:1.
//
// CR 11-4 D-005 fix: TS mirror uses `default: throw new Error(...)` for
// unknown state fall-through (NO silent `default: return 'unknown'`).

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::DELETION_ENVELOPE_SCHEMA_VERSION`.
 * Schema version for the deletion envelope (JSON serialization).
 */
export const DELETION_ENVELOPE_SCHEMA_VERSION = "1.0" as const;

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::RETENTION_DAYS`.
 * 30-day hard-delete retention anchor (NFR4 2절).
 */
export const RETENTION_DAYS = 30 as const;

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::DELETION_CHALLENGE_TOKEN_TTL_SECONDS`.
 * 5-minute TTL for the HS256 challenge token (destructive endpoint CR 12-5 L3 Layer 2).
 */
export const DELETION_CHALLENGE_TOKEN_TTL_SECONDS = 300 as const;

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::DELETION_CHALLENGE_TOKEN_PURPOSE`.
 * Single-purpose JWT claim value.
 */
export const DELETION_CHALLENGE_TOKEN_PURPOSE = "account_deletion" as const;

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::DELETION_CONSENT_TEMPLATE_KO`.
 * Verbatim Korean consent template that the user MUST type to proceed.
 * UX locked: 격식체 종결 (AD-15 §11).
 */
export const DELETION_CONSENT_TEMPLATE_KO =
  "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다" as const;

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::TenantDeletionStatus`.
 *
 * Tenant lifecycle FSM (active → pending_deletion → deleted).
 * 3-value enum — drift detector pins against Python `TenantDeletionStatus`.
 */
export const TenantDeletionStatus = {
  ACTIVE: "active",
  PENDING_DELETION: "pending_deletion",
  DELETED: "deleted",
} as const;

export type TenantDeletionStatusValue =
  (typeof TenantDeletionStatus)[keyof typeof TenantDeletionStatus];

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::can_transition_status` FSM.
 *
 * Allowed transitions:
 * - active → pending_deletion (request_deletion succeeds)
 * - pending_deletion → active (cancel_deletion succeeds)
 * - pending_deletion → deleted (cron hard_delete_expired_tenants succeeds)
 *
 * NO other transitions allowed (FSM invariant — drift detector pins).
 */
export function canTransitionStatus(
  from: TenantDeletionStatusValue,
  to: TenantDeletionStatusValue,
): boolean {
  if (from === TenantDeletionStatus.ACTIVE && to === TenantDeletionStatus.PENDING_DELETION) {
    return true;
  }
  if (from === TenantDeletionStatus.PENDING_DELETION && to === TenantDeletionStatus.ACTIVE) {
    return true;
  }
  if (from === TenantDeletionStatus.PENDING_DELETION && to === TenantDeletionStatus.DELETED) {
    return true;
  }
  return false;
}

/**
 * Mirrors `packages/services/m12_account/account_deletion.py::build_deletion_envelope`.
 *
 * Build the deletion envelope (JSON-serializable) for an audit dump.
 *
 * @param tenantId — tenant UUID
 * @param status — current FSM status
 * @param deletionRequestedAt — when the owner requested deletion
 * @param deletionScheduledFor — 30-day retention anchor
 * @param consentId — deletion_consents.consent_id (UUID)
 * @returns DeletionEnvelope object (JSON-ready)
 */
export interface DeletionEnvelope {
  schema_version: typeof DELETION_ENVELOPE_SCHEMA_VERSION;
  tenant_id: string;
  status: TenantDeletionStatusValue;
  deletion_requested_at: string;
  deletion_scheduled_for: string;
  consent_id: string;
}

export function buildDeletionEnvelope(
  tenantId: string,
  status: TenantDeletionStatusValue,
  deletionRequestedAt: string,
  deletionScheduledFor: string,
  consentId: string,
): DeletionEnvelope {
  return {
    schema_version: DELETION_ENVELOPE_SCHEMA_VERSION,
    tenant_id: tenantId,
    status,
    deletion_requested_at: deletionRequestedAt,
    deletion_scheduled_for: deletionScheduledFor,
    consent_id: consentId,
  };
}

/**
 * Mirrors `apps/api/modules/m12_account/services/account_deletion_service.py::DeletionStatusResponse`.
 *
 * Response shape returned by `GET /api/v1/account/deletion/status`.
 */
export interface DeletionStatusResponse {
  tenant_id: string;
  status: TenantDeletionStatusValue;
  deletion_requested_at: string | null;
  deletion_requested_by_user_id: string | null;
  deletion_consent_id: string | null;
  deletion_scheduled_for: string | null;
  trace_id: string;
}

/**
 * Mirrors `apps/api/modules/m12_account/services/account_deletion_service.py::DeletionChallengeTokenIssued`.
 *
 * Response shape returned by `POST /api/v1/account/deletion/challenge-token`.
 */
export interface DeletionChallengeTokenResponse {
  token: string;
  expires_at: string;
  trace_id: string;
}

/**
 * Mirrors `apps/api/modules/m12_account/services/account_deletion_service.py::DeletionResult`.
 *
 * Response shape returned by `POST /api/v1/account/deletion/request` +
 * `POST /api/v1/account/deletion/cancel`.
 */
export interface DeletionEnvelopeResponse {
  tenant_id: string;
  status: TenantDeletionStatusValue;
  deletion_scheduled_for: string;
  trace_id: string;
}

/**
 * 8 audit action labels (mirrors `AccountDeletionAction` Literal in
 * `apps/api/core/audit_action.py`). Drift detector pins enum ↔ Python.
 */
export const AccountDeletionAction = {
  DELETION_REQUESTED: "deletion_requested",
  DELETION_CONSENT_GIVEN: "deletion_consent_given",
  DELETION_CANCELLED: "deletion_cancelled",
  DELETION_ANONYMIZED: "deletion_anonymized",
  TENANT_HARD_DELETED: "tenant_hard_deleted",
  DELETION_FAILED: "deletion_failed",
  DELETION_2FA_FAILED: "deletion_2fa_failed",
  TWO_FACTOR_VERIFIED: "two_factor_verified",
} as const;

export type AccountDeletionActionValue =
  (typeof AccountDeletionAction)[keyof typeof AccountDeletionAction];

/**
 * Human-readable status label for the dashboard (Korean).
 * Used by `DeletionStatusPanel.tsx`. i18n strings live in ko-KR.json —
 * these are the ENUM → label mapping (NOT i18n strings).
 */
export function getStatusLabel(status: TenantDeletionStatusValue): string {
  // CR 11-4 D-005 fix: NO silent fall-through — unknown state throws.
  switch (status) {
    case TenantDeletionStatus.ACTIVE:
      return "활성";
    case TenantDeletionStatus.PENDING_DELETION:
      return "삭제 대기";
    case TenantDeletionStatus.DELETED:
      return "삭제 완료";
    default: {
      // Exhaustiveness check — TS will error here if a new status is added
      // without updating this switch (CR 11-4 D-005).
      const _exhaustive: never = status;
      throw new Error(
        `Unknown TenantDeletionStatus: ${_exhaustive as string}. ` +
          "Update apps/web/lib/m12-account-deletion.ts (CR 11-4 D-005).",
      );
    }
  }
}

/**
 * Compute the days-remaining-until-hard-delete for a pending deletion.
 * Returns null if not pending_deletion or anchor is null.
 */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function daysUntilHardDelete(scheduledForIso: string | null): number | null {
  if (!scheduledForIso) {
    return null;
  }
  const scheduledMs = new Date(scheduledForIso).getTime();
  if (Number.isNaN(scheduledMs)) {
    return null;
  }
  const nowMs = Date.now();
  const diffMs = scheduledMs - nowMs;
  return Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
}
