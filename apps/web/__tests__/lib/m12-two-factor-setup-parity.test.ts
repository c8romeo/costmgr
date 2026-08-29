// apps/web/__tests__/lib/m12-two-factor-setup-parity.test.ts — Story 12.4
//
// Cross-language parity test for the 2FA setup payload validation.
// Mirrors `apps/api/modules/m12_account/services/two_factor_service.py::setup_totp`
// response shape: secret (base32), uri (otpauth://totp/...), recovery_codes (8 × 10 Crockford base32).

import { describe, expect, it } from "vitest";

import {
  CROCKFORD_BASE32_ALPHABET,
  ERROR_CODE_INVALID_RECOVERY_CODE,
  ERROR_CODE_INVALID_SECRET,
  ERROR_CODE_INVALID_URI,
  RECOVERY_CODE_COUNT,
  RECOVERY_CODE_LENGTH,
  TWO_FACTOR_SETUP_ALREADY_ENABLED_KO,
  buildTwoFactorSetupState,
} from "../../lib/m12-two-factor-setup";

const VALID_SECRET = "JBSWY3DPEHPK3PXP";
const VALID_URI = "otpauth://totp/costmgr:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=costmgr";

// eslint-disable-next-line @typescript-eslint/naming-convention
function _validRecoveryCode(): string {
  // Generate a 10-char Crockford base32 string.
  const alphabet = Array.from(CROCKFORD_BASE32_ALPHABET);
  let out = "";
  for (let i = 0; i < RECOVERY_CODE_LENGTH; i++) {
    out += alphabet[i % alphabet.length];
  }
  return out;
}

// eslint-disable-next-line @typescript-eslint/naming-convention
function _validRecoveryCodes(): string[] {
  return Array.from({ length: RECOVERY_CODE_COUNT }, () => _validRecoveryCode());
}

describe("m12-two-factor-setup parity — buildTwoFactorSetupState", () => {
  it("parity 1: valid setup payload → authorized=true + secret/uri/codes populated", () => {
    const state = buildTwoFactorSetupState({
      secret: VALID_SECRET,
      uri: VALID_URI,
      recovery_codes: _validRecoveryCodes(),
    });
    expect(state.authorized).toBe(true);
    expect(state.already_enabled).toBe(false);
    expect(state.secret).toBe(VALID_SECRET);
    expect(state.uri).toBe(VALID_URI);
    expect(state.recovery_codes).toHaveLength(RECOVERY_CODE_COUNT);
  });

  it("parity 2: already_enabled=true → authorized=false + ALREADY_ENABLED_KO", () => {
    const state = buildTwoFactorSetupState({
      secret: VALID_SECRET,
      uri: VALID_URI,
      recovery_codes: _validRecoveryCodes(),
      already_enabled: true,
    });
    expect(state.authorized).toBe(false);
    expect(state.already_enabled).toBe(true);
    expect(state.reject_reason_ko).toBe(TWO_FACTOR_SETUP_ALREADY_ENABLED_KO);
  });

  it("parity 3: invalid secret (lowercase) → INVALID_TOTP_SECRET", () => {
    const state = buildTwoFactorSetupState({
      secret: "jbswy3dpehpk3pxp", // lowercase
      uri: VALID_URI,
      recovery_codes: _validRecoveryCodes(),
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(ERROR_CODE_INVALID_SECRET);
  });

  it("parity 4: invalid uri (not otpauth) → INVALID_TOTP_URI", () => {
    const state = buildTwoFactorSetupState({
      secret: VALID_SECRET,
      uri: "https://example.com/totp",
      recovery_codes: _validRecoveryCodes(),
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(ERROR_CODE_INVALID_URI);
  });

  it("parity 5: wrong recovery_codes count (7 instead of 8) → INVALID_RECOVERY_CODE", () => {
    const state = buildTwoFactorSetupState({
      secret: VALID_SECRET,
      uri: VALID_URI,
      recovery_codes: _validRecoveryCodes().slice(0, 7),
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(ERROR_CODE_INVALID_RECOVERY_CODE);
  });

  it("parity 6: recovery code with non-Crockford char (e.g. 'U') → INVALID_RECOVERY_CODE", () => {
    const codes = _validRecoveryCodes();
    codes[0] = "U" + codes[0].slice(1); // U is NOT in Crockford base32
    const state = buildTwoFactorSetupState({
      secret: VALID_SECRET,
      uri: VALID_URI,
      recovery_codes: codes,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(ERROR_CODE_INVALID_RECOVERY_CODE);
  });

  it("RECOVERY_CODE_COUNT = 8 (matches Python kernel)", () => {
    expect(RECOVERY_CODE_COUNT).toBe(8);
  });

  it("RECOVERY_CODE_LENGTH = 10 (matches Python kernel)", () => {
    expect(RECOVERY_CODE_LENGTH).toBe(10);
  });
});
