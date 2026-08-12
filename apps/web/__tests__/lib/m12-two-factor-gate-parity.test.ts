// apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts — Story 12.5
//
// Cross-language parity test (Python pure kernel ↔ TS mirror) for the
// M2 entry gate decision (AD-10 role + 2FA enrollment + lockout).
//
// D-PARITY-01 fix: previous parity test enshrined inversion (`owner + 2FA
// disabled → allowed=true`). Per AC #5 + kernel SSOT
// `packages/services/m12_account/two_factor_gate.py::check_two_factor_required`
// returns True when `totp_secret_set` is False. So 2FA-disabled ⇒
// `requires_two_factor=true` ⇒ `allowed=false`.
//
// 8 NEW corrected cases replace 8 old cases (which all asserted the
// inverted gate). The new cases match Python kernel parity EXACTLY
// (kernel helper `packages/services/m12_account/two_factor_gate.py` is
// the SSOT — `apps/web/lib/m12-two-factor-gate.ts` mirrors its semantics).
//
// Composition priority: setup-required > lockout > role_denied.
// Therefore parity_5 (viewer + 2FA disabled) and parity_8 (auditor +
// 2FA disabled) would technically see "2FA 설정이 필요합니다" message
// (priority #1) — so we set `totp_enabled=true` to exercise the
// role_denied message instead.
//
// Drift detector across Python↔TS: `tests/integration/test_m12_two_factor_gate_cross_language_drift.py`
// (NEW). This file is the per-language test bed only.

import { describe, expect, it } from "vitest";

import {
  ALLOWED_M2_ROLES,
  READONLY_M2_ROLES,
  buildM2EntryGateState,
} from "../../lib/m12-two-factor-gate";

describe("m12-two-factor-gate parity — buildM2EntryGateState (D-PARITY-01 fix)", () => {
  // ── Corrected case 1: owner + 2FA disabled → requires_two_factor=true → blocked
  it("parity 1 (corrected): owner role + 2FA disabled → blocked, requires setup", () => {
    const state = buildM2EntryGateState({
      role: "owner",
      totp_enabled: false,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(false); // NOT true (D-PARITY-01 inversion fix)
    expect(state.requires_two_factor).toBe(true);
    expect(state.requires_challenge).toBe(false);
    expect(state.role_allowed).toBe(true);
    expect(state.message_ko).toContain("2FA 설정이 필요합니다");
  });

  // ── Corrected case 2: owner + 2FA enabled → setup complete, entry allowed
  it("parity 2 (corrected): owner role + 2FA enabled → allowed=true", () => {
    const state = buildM2EntryGateState({
      role: "owner",
      totp_enabled: true,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(true);
    expect(state.requires_two_factor).toBe(false);
    expect(state.requires_challenge).toBe(true);
  });

  // ── Corrected case 3: member + 2FA disabled → setup required
  it("parity 3 (corrected): member role + 2FA disabled → blocked, requires setup", () => {
    const state = buildM2EntryGateState({
      role: "member",
      totp_enabled: false,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(false);
    expect(state.requires_two_factor).toBe(true);
    expect(state.role_allowed).toBe(true);
  });

  // ── Corrected case 4: member + 2FA enabled → entry allowed
  it("parity 4 (corrected): member role + 2FA enabled → allowed=true", () => {
    const state = buildM2EntryGateState({
      role: "member",
      totp_enabled: true,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(true);
    expect(state.requires_two_factor).toBe(false);
    expect(state.role_allowed).toBe(true);
  });

  // ── Corrected case 5: viewer (2FA enabled) → role denied message wins
  // When 2FA is fully enabled, role_denied message priority #3 wins
  // (over setup-required priority #1, which is moot when totp_enabled=true).
  it("parity 5 (corrected): viewer role + 2FA enabled → blocked, role_denied", () => {
    const state = buildM2EntryGateState({
      role: "viewer",
      totp_enabled: true,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(false);
    expect(state.role_allowed).toBe(false);
    expect(state.message_ko).toContain("owner/member");
  });

  // ── Corrected case 6: consultant_proxy → role denied
  it("parity 6 (corrected): consultant_proxy role → blocked, role_denied", () => {
    const state = buildM2EntryGateState({
      role: "consultant_proxy",
      totp_enabled: true,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(false);
    expect(state.role_allowed).toBe(false);
    expect(state.message_ko).toContain("owner/member");
  });

  // ── Corrected case 7: locked_out user → blocked, lockout message
  it("parity 7 (corrected): locked_out owner → blocked, lockout message", () => {
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

  // ── Corrected case 8: unknown role "auditor" (2FA enabled) → role denied
  // (CR 11-4 D-005). When 2FA is fully enabled, role_denied message wins
  // and unknown role → fail-closed path returns the generic FORBIDDEN_ROLE_KO.
  it("parity 8 (corrected): unknown role 'auditor' + 2FA enabled → blocked, role_denied", () => {
    const state = buildM2EntryGateState({
      role: "auditor",
      totp_enabled: true,
      locked_out: false,
      lockout_until: null,
    });
    expect(state.allowed).toBe(false);
    expect(state.role_allowed).toBe(false);
    expect(state.message_ko).toContain("owner/member");
  });

  // ── Role allowlist parity (Python ALLOWED_M2_ROLES)
  it("ALLOWED_M2_ROLES = {'owner', 'member'} (kernel SSOT parity)", () => {
    expect(ALLOWED_M2_ROLES.has("owner")).toBe(true);
    expect(ALLOWED_M2_ROLES.has("member")).toBe(true);
    expect(ALLOWED_M2_ROLES.size).toBe(2);
  });

  // ── Role denylist parity (Python READONLY_ROLES)
  it("READONLY_M2_ROLES = {'viewer', 'consultant_proxy'} (kernel SSOT parity)", () => {
    expect(READONLY_M2_ROLES.has("viewer")).toBe(true);
    expect(READONLY_M2_ROLES.has("consultant_proxy")).toBe(true);
    expect(READONLY_M2_ROLES.size).toBe(2);
  });
});
