// apps/web/__tests__/lib/m12-two-factor-disable-parity.test.ts — Story 12.4
//
// Cross-language parity test for the 2FA disable payload validation.
// Mirrors `apps/api/modules/m12_account/services/two_factor_service.py::disable_totp`
// authorization rules: current_code (6 digits) OR admin override (owner + reason ≥ 20).

import { describe, expect, it } from "vitest";

import {
  ERROR_CODE_INVALID_CODE_FORMAT,
  ERROR_CODE_REASON_TOO_LONG,
  ERROR_CODE_REASON_TOO_SHORT,
  buildTwoFactorDisableState,
} from "../../lib/m12-two-factor-disable";

const VALID_CODE = "123456";
const VALID_REASON = "사용자 디바이스 분실로 인한 2FA 초기화 진행합니다";

describe("m12-two-factor-disable parity — buildTwoFactorDisableState", () => {
  it("parity 1: valid current_code → authorized=true + code_verified=true", () => {
    const state = buildTwoFactorDisableState({
      current_code: VALID_CODE,
      reason: "",
      is_owner: false,
    });
    expect(state.authorized).toBe(true);
    expect(state.code_verified).toBe(true);
    expect(state.admin_override).toBe(false);
  });

  it("parity 2: admin override (owner + reason ≥ 20) → authorized=true", () => {
    const state = buildTwoFactorDisableState({
      current_code: null,
      reason: VALID_REASON,
      is_owner: true,
    });
    expect(state.authorized).toBe(true);
    expect(state.code_verified).toBe(false);
    expect(state.admin_override).toBe(true);
    expect(state.reason_valid).toBe(true);
  });

  it("parity 3: invalid current_code format (5 digits) → INVALID_TOTP_CODE_FORMAT", () => {
    const state = buildTwoFactorDisableState({
      current_code: "12345",
      reason: "",
      is_owner: false,
    });
    expect(state.authorized).toBe(false);
    expect(state.code_verified).toBe(false);
    expect(state.reject_reason_ko).toBe(ERROR_CODE_INVALID_CODE_FORMAT);
  });

  it("parity 4: admin override reason too short (10 chars) → REASON_TOO_SHORT", () => {
    const state = buildTwoFactorDisableState({
      current_code: null,
      reason: "초기화 진행",
      is_owner: true,
    });
    expect(state.authorized).toBe(false);
    expect(state.admin_override).toBe(false);
    expect(state.reason_valid).toBe(false);
    expect(state.reject_reason_ko).toBe(ERROR_CODE_REASON_TOO_SHORT);
  });

  it("parity 5: admin override reason too long (>500 chars) → REASON_TOO_LONG", () => {
    const longReason = "가".repeat(501);
    const state = buildTwoFactorDisableState({
      current_code: null,
      reason: longReason,
      is_owner: true,
    });
    expect(state.authorized).toBe(false);
    expect(state.reason_valid).toBe(false);
    expect(state.reject_reason_ko).toBe(ERROR_CODE_REASON_TOO_LONG);
  });

  it("parity 6: no code + non-owner → unauthorized (handler gate catches first)", () => {
    const state = buildTwoFactorDisableState({
      current_code: null,
      reason: VALID_REASON,
      is_owner: false,
    });
    expect(state.authorized).toBe(false);
    expect(state.code_verified).toBe(false);
    expect(state.admin_override).toBe(false);
  });

  it("parity 7: valid code + owner (both paths valid) → authorized=true via code", () => {
    const state = buildTwoFactorDisableState({
      current_code: VALID_CODE,
      reason: "",
      is_owner: true,
    });
    expect(state.authorized).toBe(true);
    expect(state.code_verified).toBe(true);
    expect(state.admin_override).toBe(false);
  });
});
