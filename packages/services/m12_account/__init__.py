"""packages.services.m12_account — Story 12.1 pure kernel subtree.

Epic 12 (Account & Security Operations) cj-style 3-story 분할 1번째
(Epic 11 retro §7 A14 권장안). 본 subtree는 M12 module authority의
pure-Python 계층 — RFC 6238 TOTP + bcrypt-style recovery code hashing
+ 2FA gate validation.

AD-11 layer rule: pure-Python, stdlib-only (hmac, hashlib, base64,
secrets, struct, time). NO DB, NO clock dependency at module level
(caller passes timestamp explicitly), NO random at module level
(caller invokes secrets module).

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m12-two-factor-setup.ts`.
"""

from __future__ import annotations

from packages.services.m12_account.totp import (
    ERROR_CODE_INVALID_TOTP,
    ERROR_CODE_LOCKOUT_ACTIVE,
    LOCKOUT_DURATION_SECONDS,
    MAX_FAILED_ATTEMPTS,
    RECOVERY_CODE_COUNT,
    RECOVERY_CODE_LENGTH,
    TOTP_CODE_LENGTH,
    TOTP_PERIOD_SECONDS,
    TOTP_WINDOW_TOLERANCE,
    TotpInvalidCodeError,
    TotpLockoutError,
    compute_totp_code,
    generate_recovery_code_hashes,
    generate_recovery_codes,
    generate_totp_secret,
    generate_totp_uri,
    hash_recovery_code,
    verify_recovery_code,
    verify_totp_code,
)
from packages.services.m12_account.two_factor_gate import (
    ERROR_CODE_FORBIDDEN_ROLE,
    ERROR_CODE_TWO_FACTOR_REQUIRED,
    ForbiddenRoleError,
    TwoFactorRequiredError,
    check_two_factor_required,
    enforce_role_gate,
    enforce_two_factor_gate,
    lockout_status,
)

__all__ = [
    # totp.py exports
    "compute_totp_code",
    "verify_totp_code",
    "generate_totp_secret",
    "generate_totp_uri",
    "generate_recovery_codes",
    "hash_recovery_code",
    "verify_recovery_code",
    "generate_recovery_code_hashes",
    "TotpInvalidCodeError",
    "TotpLockoutError",
    "TOTP_CODE_LENGTH",
    "TOTP_PERIOD_SECONDS",
    "TOTP_WINDOW_TOLERANCE",
    "RECOVERY_CODE_COUNT",
    "RECOVERY_CODE_LENGTH",
    "MAX_FAILED_ATTEMPTS",
    "LOCKOUT_DURATION_SECONDS",
    "ERROR_CODE_INVALID_TOTP",
    "ERROR_CODE_LOCKOUT_ACTIVE",
    # two_factor_gate.py exports
    "check_two_factor_required",
    "enforce_two_factor_gate",
    "enforce_role_gate",
    "lockout_status",
    "TwoFactorRequiredError",
    "ForbiddenRoleError",
    "ERROR_CODE_TWO_FACTOR_REQUIRED",
    "ERROR_CODE_FORBIDDEN_ROLE",
]
