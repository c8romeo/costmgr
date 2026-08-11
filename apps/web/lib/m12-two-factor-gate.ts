// apps/web/lib/m12-two-factor-gate.ts — Story 12.4 (Epic 12 carry-over sprint)
//
// M12 2FA gate TS projection (AD-15 §11 SSOT parity with
// `packages/services/m12_account/two_factor_gate.py` + `m12_account.handlers`).
//
// Frontend mirror of the GET /api/v1/m2-entry-gate response. The
// M2 ([월 입력]) page renders a `<TwoFactorGuard>` block whose visible
// state is decided entirely from this projection — no further backend
// round-trip required for the static gate conditions.
//
// Drift caught by `apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts`
// (vitest cross-language parity test).
//
// AD-10 4-role allowlist: owner / member = ALLOWED, viewer / consultant_proxy = DENIED.
// 2FA enrollment: when `requires_two_factor=true`, user MUST complete
// challenge before M2 entry. Lockout state blocks all entry until expiry.

import {
  M2_ENTRY_GATE_LOCKED_OUT_KO,
  M2_ENTRY_GATE_REQUIRES_2FA_KO,
  M2_ENTRY_GATE_ROLE_DENIED_KO,
} from "./m12-two-factor-constants";

// ── Constants ────────────────────────────────────────────────────
// AD-10 4-role allowlist for M2 entry (PRD §M12-a).
// Mirrors Python `packages/services/m12_account/two_factor_gate.py::ALLOWED_M2_ROLES`.
export const ALLOWED_M2_ROLES: ReadonlySet<string> = new Set([
  "owner",
  "member",
]);

// READONLY_ROLES — explicitly denied at the gate (parity with Python kernel).
export const READONLY_M2_ROLES: ReadonlySet<string> = new Set([
  "viewer",
  "consultant_proxy",
]);

// ── Gate state (TS view model) ──────────────────────────────────
export interface M2EntryGateState {
  allowed: boolean;
  requires_two_factor: boolean;
  requires_challenge: boolean;
  role_allowed: boolean;
  locked_out: boolean;
  lockout_until: string | null;
  message_ko: string;
}

// ── buildM2EntryGateState (TS mirror) ───────────────────────────
/**
 * Mirror of Python `enforce_role_gate` + `enforce_two_factor_gate` +
 * `lockout_status` composed decision. All inputs are sourced from
 * `GET /api/v1/m2-entry-gate` response (or computed locally for tests).
 *
 * The pure-kernel `check_two_factor_required` / `enforce_role_gate`
 * use the same role allowlist (AD-10 owner/member). This function
 * NEVER raises — the gate is a UI signal, not a hard block; the
 * server enforces the same conditions on every M2 entry request.
 */
export function buildM2EntryGateState(input: {
  role: string;
  totp_enabled: boolean;
  locked_out: boolean;
  lockout_until: string | null;
}): M2EntryGateState {
  // Role gate (AD-10).
  const role_allowed = ALLOWED_M2_ROLES.has(input.role);

  // 2FA gate.
  const requires_two_factor = input.totp_enabled;
  const requires_challenge = input.totp_enabled && !input.locked_out;

  // Lockout gate (5-fail → 15-min, mirrors Python LOCKOUT_DURATION_SECONDS).
  const locked_out = input.locked_out;

  // Compose decision. M2 entry is allowed iff:
  // 1. role allowed (owner/member)
  // 2. NOT locked out
  // (2FA challenge is a separate flow — user calls /challenge to obtain a token.)
  const allowed = role_allowed && !locked_out;

  // Compose message (Korean SSOT).
  let message_ko: string;
  if (locked_out && input.lockout_until) {
    message_ko = M2_ENTRY_GATE_LOCKED_OUT_KO.replace("{until}", input.lockout_until);
  } else if (!role_allowed) {
    message_ko = M2_ENTRY_GATE_ROLE_DENIED_KO;
  } else if (requires_two_factor) {
    message_ko = M2_ENTRY_GATE_REQUIRES_2FA_KO;
  } else {
    message_ko = "M2 진입 가능";
  }

  return {
    allowed,
    requires_two_factor,
    requires_challenge,
    role_allowed,
    locked_out,
    lockout_until: input.lockout_until,
    message_ko,
  };
}
