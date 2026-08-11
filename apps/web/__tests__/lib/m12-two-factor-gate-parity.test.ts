// apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts — Story 12.4
//
// Cross-language parity test (Python pure kernel ↔ TS mirror) for the
// M2 entry gate decision (AD-10 role + 2FA enrollment + lockout).
//
// Drift caught between:
// - `packages/services/m12_account/two_factor_gate.py` (Python)
// - `apps/web/lib/m12-two-factor-gate.ts` (TS mirror)
//
// Run via: `pnpm exec vitest run m12-two-factor-gate-parity`

import { describe, expect, it } from "vitest";

import {
  ALLOWED_M2_ROLES,
  READONLY_M2_ROLES,
  buildM2EntryGateState,
} from "../../lib/m12-two-factor-gate";

describe("m12-two-factor-gate parity — buildM2EntryGateState", () => {
  it("parity 1: owner role + 2FA disabled → allowed=true + requires_2fa=false", () => {
    const state = buildM2EntryGateState({
      role: "owner",
      totp_enabled: false,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(true);
    expect(state.requires_two_factor).toBe(false);
    expect(state.requires_challenge).toBe(false);
    expect(state.role_allowed).toBe(true);
    expect(state.locked_out).toBe(false);
  });

  it("parity 2: owner role + 2FA enabled → allowed=true + requires_2fa=true", () => {
    const state = buildM2EntryGateState({
      role: "owner",
      totp_enabled: true,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(true);
    expect(state.requires_two_factor).toBe(true);
    expect(state.requires_challenge).toBe(true);
    expect(state.message_ko).toContain("2FA 인증 필요");
  });

  it("parity 3: viewer role → allowed=false + role_denied message", () => {
    const state = buildM2EntryGateState({
      role: "viewer",
      totp_enabled: false,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(false);
    expect(state.role_allowed).toBe(false);
    expect(state.message_ko).toContain("owner/member");
  });

  it("parity 4: consultant_proxy role → allowed=false + role_denied", () => {
    const state = buildM2EntryGateState({
      role: "consultant_proxy",
      totp_enabled: true,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(false);
    expect(state.role_allowed).toBe(false);
  });

  it("parity 5: owner + 2FA + locked_out → allowed=false + lockout message", () => {
    const until = "2026-08-11T12:30:00+09:00";
    const state = buildM2EntryGateState({
      role: "owner",
      totp_enabled: true,
      locked_out: true,
      lockout_until: until,
    });
    expect(state.allowed).toBe(false);
    expect(state.locked_out).toBe(true);
    expect(state.message_ko).toContain("잠금");
    expect(state.message_ko).toContain(until);
  });

  it("parity 6: member role + 2FA disabled → allowed=true (member is in allowlist)", () => {
    const state = buildM2EntryGateState({
      role: "member",
      totp_enabled: false,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(true);
    expect(state.role_allowed).toBe(true);
  });

  it("ALLOWED_M2_ROLES contains owner + member (parity with Python kernel)", () => {
    expect(ALLOWED_M2_ROLES.has("owner")).toBe(true);
    expect(ALLOWED_M2_ROLES.has("member")).toBe(true);
    expect(ALLOWED_M2_ROLES.size).toBe(2);
  });

  it("READONLY_M2_ROLES contains viewer + consultant_proxy", () => {
    expect(READONLY_M2_ROLES.has("viewer")).toBe(true);
    expect(READONLY_M2_ROLES.has("consultant_proxy")).toBe(true);
    expect(READONLY_M2_ROLES.size).toBe(2);
  });
});
