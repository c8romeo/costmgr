"""apps.api.modules.m12_account.services.audit_extension — Story 12.1 helper.

CR 1.1 / A5 forward-lock — `apps.api.core.audit_action` already has
the 6 NEW TWO_FACTOR_AUTH values registered (T7 in dev-story). This
module is a thin facade that documents the patterns for the 6
emit_audit_typed calls + provides Korean SSOT constants for
downstream handlers (per CR 6-2/6-3 cross-language parity).

Story 12.1 emits:
  - `two_factor_setup_initiated`     → setup_totp
  - `two_factor_setup_completed`     → verify_and_enable_totp
  - `two_factor_challenge_passed`    → verify_totp_challenge (success)
  - `two_factor_challenge_failed`    → verify_totp_challenge (failure)
                                       + verify_recovery_code invalid
  - `two_factor_recovery_consumed`   → verify_recovery_code (success)
  - `two_factor_disabled`            → disable_totp

Korean SSOT (AD-15 §11) — handlers in `apps/api/main.py` use these
constants. Mirrored verbatim in `apps/web/lib/m12-two-factor-messages.ts`.
"""

from __future__ import annotations

# ── Korean SSOT constants ─────────────────────────────────────
# Setup
SETUP_INITIATED_KO: str = "2단계 인증 설정 시작"
SETUP_COMPLETED_KO: str = "2단계 인증 설정 완료"
SETUP_ALREADY_ENABLED_KO: str = "2단계 인증이 이미 활성화되어 있습니다"
SETUP_NOT_ENABLED_KO: str = "2단계 인증이 설정되어 있지 않습니다"

# Challenge
CHALLENGE_PASSED_KO: str = "2단계 인증 통과"
CHALLENGE_FAILED_KO: str = "인증 코드가 올바르지 않습니다"
CHALLENGE_LOCKED_OUT_KO: str = "5회 연속 실패 — 15분간 잠금"

# Recovery
RECOVERY_CONSUMED_KO: str = "복구 코드 사용 완료"
RECOVERY_INVALID_KO: str = "복구 코드가 유효하지 않거나 이미 사용됨"
RECOVERY_EXHAUSTED_KO: str = "모든 복구 코드가 사용되었습니다 — 관리자에게 문의하세요"

# Disable
DISABLED_KO: str = "2단계 인증 비활성화 완료"
DISABLE_UNAUTHORIZED_KO: str = "2단계 인증 비활성화 권한이 없습니다"

# Encryption / system
ENCRYPTION_FAILED_KO: str = "암호화 처리 중 오류가 발생했습니다"
KEY_MISSING_KO: str = "암호화 키를 찾을 수 없습니다 — 시스템 관리자에게 문의하세요"
AUDIT_EMIT_FAILED_KO: str = "감사 로그 기록 중 일시적 오류가 발생했습니다 — 재시도해 주세요"
USER_NOT_FOUND_KO: str = "사용자를 찾을 수 없습니다"

# Challenge token
CHALLENGE_TOKEN_EXPIRED_KO: str = "인증 토큰이 만료되었습니다 — 다시 시도해 주세요"
CHALLENGE_TOKEN_INVALID_KO: str = "인증 토큰이 유효하지 않습니다"
CHALLENGE_TOKEN_PURPOSE_MISMATCH_KO: str = "인증 토큰 용도가 일치하지 않습니다"
CHALLENGE_TOKEN_ALREADY_CONSUMED_KO: str = "이미 사용된 인증 토큰입니다 — 재사용 불가"
TWO_FACTOR_CHALLENGE_FAILED_KO: str = "2FA 인증에 실패했습니다 — 코드를 확인해 주세요"


# ── Error code aliases (envelope contract) ───────────────────
ERROR_CODE_NOT_ENABLED: str = "TWO_FACTOR_NOT_ENABLED"
ERROR_CODE_ALREADY_ENABLED: str = "TWO_FACTOR_ALREADY_ENABLED"
ERROR_CODE_AUDIT_EMIT_FAILED: str = "TWO_FACTOR_AUDIT_EMIT_FAILED"
ERROR_CODE_ENCRYPTION_FAILED: str = "TWO_FACTOR_ENCRYPTION_FAILED"
ERROR_CODE_KEY_MISSING: str = "TWO_FACTOR_KEY_MISSING"
ERROR_CODE_RECOVERY_EXHAUSTED: str = "TWO_FACTOR_RECOVERY_EXHAUSTED"
ERROR_CODE_DISABLE_UNAUTHORIZED: str = "TWO_FACTOR_DISABLE_UNAUTHORIZED"
ERROR_CODE_USER_NOT_FOUND: str = "TWO_FACTOR_USER_NOT_FOUND"

# Challenge token
ERROR_CODE_CHALLENGE_TOKEN_EXPIRED: str = "CHALLENGE_TOKEN_EXPIRED"
ERROR_CODE_CHALLENGE_TOKEN_INVALID: str = "CHALLENGE_TOKEN_INVALID"
ERROR_CODE_CHALLENGE_TOKEN_PURPOSE_MISMATCH: str = "CHALLENGE_TOKEN_PURPOSE_MISMATCH"

# ── Story 12.2 backup export (CR 12-5 D-14 envelope) ───────
BACKUP_SERVICE_ERROR_KO: str = "백업 서비스 오류가 발생했습니다"
BACKUP_PAYLOAD_TOO_LARGE_KO: str = "백업 페이로드가 50MB 제한을 초과했습니다"
BACKUP_NOT_FOUND_KO: str = "백업을 찾을 수 없습니다"
BACKUP_RETENTION_CUTOFF_INVALID_KO: str = "잘못된 보관 기간 설정입니다"
BACKUP_AUDIT_EMIT_FAILED_KO: str = "백업 감사 로그 저장에 실패했습니다"

ERROR_CODE_BACKUP_SERVICE_ERROR: str = "BACKUP_SERVICE_ERROR"
ERROR_CODE_BACKUP_PAYLOAD_TOO_LARGE: str = "BACKUP_PAYLOAD_TOO_LARGE"
ERROR_CODE_BACKUP_NOT_FOUND: str = "BACKUP_NOT_FOUND"
ERROR_CODE_BACKUP_RETENTION_CUTOFF_INVALID: str = "BACKUP_RETENTION_CUTOFF_INVALID"
ERROR_CODE_BACKUP_AUDIT_EMIT_FAILED: str = "BACKUP_AUDIT_EMIT_FAILED"


__all__ = [
    # Korean constants (handlers in main.py use these)
    "SETUP_INITIATED_KO",
    "SETUP_COMPLETED_KO",
    "SETUP_ALREADY_ENABLED_KO",
    "SETUP_NOT_ENABLED_KO",
    "CHALLENGE_PASSED_KO",
    "CHALLENGE_FAILED_KO",
    "CHALLENGE_LOCKED_OUT_KO",
    "RECOVERY_CONSUMED_KO",
    "RECOVERY_INVALID_KO",
    "RECOVERY_EXHAUSTED_KO",
    "DISABLED_KO",
    "DISABLE_UNAUTHORIZED_KO",
    "ENCRYPTION_FAILED_KO",
    "KEY_MISSING_KO",
    "AUDIT_EMIT_FAILED_KO",
    "USER_NOT_FOUND_KO",
    "CHALLENGE_TOKEN_EXPIRED_KO",
    "CHALLENGE_TOKEN_INVALID_KO",
    "CHALLENGE_TOKEN_PURPOSE_MISMATCH_KO",
    "CHALLENGE_TOKEN_ALREADY_CONSUMED_KO",
    "TWO_FACTOR_CHALLENGE_FAILED_KO",
    # ── Story 12.2 backup export SSOT (CR 12-5 D-14 envelope) ──
    "BACKUP_SERVICE_ERROR_KO",
    "BACKUP_PAYLOAD_TOO_LARGE_KO",
    "BACKUP_NOT_FOUND_KO",
    "BACKUP_RETENTION_CUTOFF_INVALID_KO",
    "BACKUP_AUDIT_EMIT_FAILED_KO",
    # Error codes (envelope contract)
    "ERROR_CODE_NOT_ENABLED",
    "ERROR_CODE_ALREADY_ENABLED",
    "ERROR_CODE_AUDIT_EMIT_FAILED",
    "ERROR_CODE_ENCRYPTION_FAILED",
    "ERROR_CODE_KEY_MISSING",
    "ERROR_CODE_RECOVERY_EXHAUSTED",
    "ERROR_CODE_DISABLE_UNAUTHORIZED",
    "ERROR_CODE_USER_NOT_FOUND",
    "ERROR_CODE_CHALLENGE_TOKEN_EXPIRED",
    "ERROR_CODE_CHALLENGE_TOKEN_INVALID",
    "ERROR_CODE_CHALLENGE_TOKEN_PURPOSE_MISMATCH",
    "ERROR_CODE_BACKUP_SERVICE_ERROR",
    "ERROR_CODE_BACKUP_PAYLOAD_TOO_LARGE",
    "ERROR_CODE_BACKUP_NOT_FOUND",
    "ERROR_CODE_BACKUP_RETENTION_CUTOFF_INVALID",
    "ERROR_CODE_BACKUP_AUDIT_EMIT_FAILED",
]
