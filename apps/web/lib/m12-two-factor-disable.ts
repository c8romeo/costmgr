// apps/web/lib/m12-two-factor-disable.ts — Story 12.4 (Epic 12 carry-over sprint)
//
// M12 2FA disable TS projection (AD-15 §11 SSOT parity with
// `apps/api/modules/m12_account/services/two_factor_service.py::disable_totp`).
//
// Frontend mirror of the POST /api/v1/account/2fa/disable request body.
// Authorization rules (service-enforced):
//   1. current_code is a valid 6-digit TOTP code (user possession proof), OR
//   2. admin override: reason length ≥ 20 chars (handler enforces owner role).
//
// Drift caught by `apps/web/__tests__/lib/m12-two-factor-disable-parity.test.ts`.

// ── Constants (Korean SSOT for disable) ────────────────────────
export const TWO_FACTOR_DISABLE_INITIATED_KO = "2FA 비활성화 진행 중" as const;
export const TWO_FACTOR_DISABLE_COMPLETED_KO = "2FA 비활성화 완료" as const;
export const TWO_FACTOR_DISABLE_UNAUTHORIZED_KO =
  "현재 코드 또는 관리자 권한(20자 이상 사유)이 필요합니다" as const;

// RFC 6238 TOTP code: exactly 6 digits.
const TOTP_CODE_PATTERN = /^\d{6}$/;
const MIN_REASON_LENGTH_FOR_ADMIN_OVERRIDE = 20;
const MAX_REASON_LENGTH = 500;

// ── Disable result (TS view model) ─────────────────────────────
export interface TwoFactorDisableState {
  authorized: boolean;
  code_verified: boolean;
  admin_override: boolean;
  reason_valid: boolean;
  reject_reason_ko: string | null;
}

// ── Error codes (mirror Python ERROR_CODE_*)
export const ERROR_CODE_INVALID_CODE_FORMAT = "INVALID_TOTP_CODE_FORMAT" as const;
export const ERROR_CODE_REASON_TOO_SHORT = "ADMIN_REASON_TOO_SHORT" as const;
export const ERROR_CODE_REASON_TOO_LONG = "ADMIN_REASON_TOO_LONG" as const;

// ── buildTwoFactorDisableState (TS mirror) ─────────────────────
/**
 * Validate the POST /api/v1/account/2fa/disable request body and
 * project to a TS view model for the disable panel.
 *
 * Authorization rules (mirror service layer):
 *   - current_code is 6 digits (user possession proof), OR
 *   - actor is admin (owner role enforced by handler) AND reason ≥ 20 chars
 *
 * If neither condition holds, `authorized=false` and the service
 * raises TwoFactorDisableUnauthorizedError → 403 envelope.
 */
export function buildTwoFactorDisableState(input: {
  current_code: string | null;
  reason: string;
  is_owner: boolean;
}): TwoFactorDisableState {
  const code = input.current_code;
  const code_present = code !== null && code.length > 0;
  const code_verified = code_present && TOTP_CODE_PATTERN.test(code);

  // Reason length validation (only enforced for admin override path).
  let reason_valid = true;
  if (!code_verified) {
    // Admin override is required → reason must be ≥ 20 chars AND ≤ 500.
    reason_valid =
      input.is_owner &&
      input.reason.length >= MIN_REASON_LENGTH_FOR_ADMIN_OVERRIDE &&
      input.reason.length <= MAX_REASON_LENGTH;
  } else {
    // Code path: reason optional (default empty). Even if provided,
    // length bounds are not enforced for the code path.
    reason_valid =
      input.reason.length === 0 ||
      (input.reason.length >= 1 && input.reason.length <= MAX_REASON_LENGTH);
  }

  const admin_override = !code_verified && input.is_owner && reason_valid;
  const authorized = code_verified || admin_override;

  let reject_reason_ko: string | null = null;
  if (!authorized) {
    if (code_present && !code_verified) {
      reject_reason_ko = ERROR_CODE_INVALID_CODE_FORMAT;
    } else if (input.reason.length < MIN_REASON_LENGTH_FOR_ADMIN_OVERRIDE) {
      reject_reason_ko = ERROR_CODE_REASON_TOO_SHORT;
    } else if (input.reason.length > MAX_REASON_LENGTH) {
      reject_reason_ko = ERROR_CODE_REASON_TOO_LONG;
    } else {
      reject_reason_ko = TWO_FACTOR_DISABLE_UNAUTHORIZED_KO;
    }
  }

  return {
    authorized,
    code_verified,
    admin_override,
    reason_valid,
    reject_reason_ko,
  };
}
