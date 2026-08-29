// apps/web/lib/m12-two-factor-setup.ts — Story 12.4 (Epic 12 carry-over sprint)
//
// M12 2FA setup TS projection (AD-15 §11 SSOT parity with
// `apps/api/modules/m12_account/services/two_factor_service.py::setup_totp`
// response).
//
// Frontend mirror of the POST /api/v1/account/2fa/setup response.
// The setup panel renders the secret + URI + 8 recovery codes
// (shown ONCE per CR 12-1 NFR5 TLS in transit contract — caller
// MUST persist these immediately).
//
// Drift caught by `apps/web/__tests__/lib/m12-two-factor-setup-parity.test.ts`.

// ── Constants (Korean SSOT for setup) ──────────────────────────
export const TWO_FACTOR_SETUP_INITIATED_KO = "2FA 설정 시작" as const;
export const TWO_FACTOR_SETUP_COMPLETED_KO = "2FA 설정 완료" as const;
export const TWO_FACTOR_SETUP_ALREADY_ENABLED_KO = "이미 2FA가 설정되어 있습니다" as const;

// Crockford base32 character set (no I, L, O, U — disambiguation).
// Mirrors Python `packages/services/m12_account/totp.py::_generate_one_recovery_code`.
export const CROCKFORD_BASE32_ALPHABET: ReadonlySet<string> = new Set(
  "0123456789ABCDEFGHJKMNPQRSTVWXYZ".split(""),
);
export const RECOVERY_CODE_LENGTH = 10;
export const RECOVERY_CODE_COUNT = 8;

// ── Setup result (TS view model) ───────────────────────────────
export interface TwoFactorSetupState {
  authorized: boolean;
  already_enabled: boolean;
  secret: string | null;
  uri: string | null;
  recovery_codes: string[];
  reject_reason_ko: string | null;
}

// ── Error codes (mirror Python ERROR_CODE_*)
export const ERROR_CODE_INVALID_SECRET = "INVALID_TOTP_SECRET" as const;
export const ERROR_CODE_INVALID_URI = "INVALID_TOTP_URI" as const;
export const ERROR_CODE_INVALID_RECOVERY_CODE = "INVALID_RECOVERY_CODE" as const;

// ── buildTwoFactorSetupState (TS mirror) ───────────────────────
/**
 * Validate the POST /api/v1/account/2fa/setup response payload and
 * project to a TS view model for the setup panel.
 *
 * Validation rules:
 * 1. secret must be valid base32 (alphabet from RFC 4648)
 * 2. uri must be an otpauth:// URL with totp scheme
 * 3. recovery_codes must be exactly RECOVERY_CODE_COUNT entries,
 *    each RECOVERY_CODE_LENGTH chars from CROCKFORD_BASE32_ALPHABET
 *
 * The caller MUST persist recovery_codes immediately (1회만 응답).
 */
export function buildTwoFactorSetupState(input: {
  secret: string;
  uri: string;
  recovery_codes: string[];
  already_enabled?: boolean;
}): TwoFactorSetupState {
  // eslint-disable-next-line camelcase
  const already_enabled = input.already_enabled ?? false;
  // eslint-disable-next-line camelcase
  if (already_enabled) {
    return {
      authorized: false,
      already_enabled: true,
      secret: null,
      uri: null,
      recovery_codes: [],
      reject_reason_ko: TWO_FACTOR_SETUP_ALREADY_ENABLED_KO,
    };
  }

  // Validate secret (base32 — uppercase + digits 2-7, RFC 4648).
  // Length 16-64 (TOTP spec floor 16 chars = 80 bits of entropy).
  // Strict case-sensitive check: lowercase letters are rejected.
  // eslint-disable-next-line camelcase
  const secret_is_valid = /^[A-Z2-7]{16,64}=*$/.test(input.secret);
  // eslint-disable-next-line camelcase
  if (!secret_is_valid) {
    return {
      authorized: false,
      already_enabled: false,
      secret: null,
      uri: null,
      recovery_codes: [],
      reject_reason_ko: ERROR_CODE_INVALID_SECRET,
    };
  }

  // Validate uri (otpauth://totp/...).
  // eslint-disable-next-line camelcase
  const uri_is_valid = input.uri.startsWith("otpauth://totp/");
  // eslint-disable-next-line camelcase
  if (!uri_is_valid) {
    return {
      authorized: false,
      already_enabled: false,
      secret: null,
      uri: null,
      recovery_codes: [],
      reject_reason_ko: ERROR_CODE_INVALID_URI,
    };
  }

  // Validate recovery_codes (8 entries × 10 Crockford base32 chars).
  if (input.recovery_codes.length !== RECOVERY_CODE_COUNT) {
    return {
      authorized: false,
      already_enabled: false,
      secret: null,
      uri: null,
      recovery_codes: [],
      reject_reason_ko: ERROR_CODE_INVALID_RECOVERY_CODE,
    };
  }
  for (const code of input.recovery_codes) {
    if (code.length !== RECOVERY_CODE_LENGTH) {
      return {
        authorized: false,
        already_enabled: false,
        secret: null,
        uri: null,
        recovery_codes: [],
        reject_reason_ko: ERROR_CODE_INVALID_RECOVERY_CODE,
      };
    }
    for (const ch of code.toUpperCase()) {
      if (!CROCKFORD_BASE32_ALPHABET.has(ch)) {
        return {
          authorized: false,
          already_enabled: false,
          secret: null,
          uri: null,
          recovery_codes: [],
          reject_reason_ko: ERROR_CODE_INVALID_RECOVERY_CODE,
        };
      }
    }
  }

  return {
    authorized: true,
    already_enabled: false,
    secret: input.secret,
    uri: input.uri,
    recovery_codes: [...input.recovery_codes],
    reject_reason_ko: null,
  };
}
