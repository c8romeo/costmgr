// apps/web/lib/m12-two-factor-constants.ts — Story 12.4 Korean SSOT constants.
//
// Single source of truth for M12 2FA Korean strings. Mirrors Python
// `apps/api/modules/m12_account/services/audit_extension.py` *_KO constants
// for the subset consumed by the frontend (M2 entry gate + 2FA panel).
//
// AD-15 §11 SSOT: ko-KR.json is the canonical Korean SSOT (CR 11-4 D-002).
// These constants are exported separately so the TS mirrors can import
// them without pulling the entire i18n namespace into pure kernels.

export const M2_ENTRY_GATE_LOCKED_OUT_KO =
  "2FA 잠금 — {until} 이후 재시도" as const;
export const M2_ENTRY_GATE_ROLE_DENIED_KO =
  "owner/member role만 [월 입력] 화면 진입 가능" as const;
// Kernel SSOT parity (Story 12.5 D-GATE-01):
// `packages/services/m12_account/two_factor_gate.py::TWO_FACTOR_REQUIRED_KO`
// = "2FA 설정이 필요합니다 — [설정하기]".
// This is shown when `requires_two_factor=true` (user has NOT yet
// registered TOTP — i.e. setup is required, NOT challenge).
export const M2_ENTRY_GATE_REQUIRES_2FA_KO =
  "2FA 설정이 필요합니다 — [설정하기]" as const;
