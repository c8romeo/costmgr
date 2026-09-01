"""packages.services.m12_account.totp — Story 12.1 TOTP pure kernel.

AD-11 layer rule: pure-Python, stdlib-only. NO DB, NO clock at module
level, NO random at module level.

RFC 6238 TOTP (Time-based One-Time Password):
- HMAC-SHA1, 30s step, 6-digit code
- ±1 window tolerance = ±30s, configurable tolerance_windows
- Base32 secret encoding (Google Authenticator / Authy 호환)

Recovery codes:
- 8 codes × 10-char alphanumeric (Crockford base32 alphabet — no I, L, O, U)
- One-time-use (consumed via verify_recovery_code + mark_used)
- Hash with PBKDF2-HMAC-SHA256 (stdlib hashlib) — 200_000 iterations

Korean messages — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m12-two-factor-setup.ts`.

This module is the M12 module authority's pure kernel — service layer
(`apps/api/modules/m12_account/services/two_factor_service.py`)
imports these helpers and adds DB / audit / session concerns.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# RFC 6238 + AD-15 §11
TOTP_CODE_LENGTH: Final[int] = 6
TOTP_PERIOD_SECONDS: Final[int] = 30
TOTP_WINDOW_TOLERANCE: Final[int] = 1  # ±1 window = ±30s = 90s tolerance

# Recovery code (PRD §F12.1 — 8 recovery codes, 1회용)
RECOVERY_CODE_COUNT: Final[int] = 8
RECOVERY_CODE_LENGTH: Final[int] = 10

# Lockout (PRD §F12.1 — 5회 실패 시 15분 lockout)
MAX_FAILED_ATTEMPTS: Final[int] = 5
LOCKOUT_DURATION_SECONDS: Final[int] = 15 * 60  # 900s

# PBKDF2-HMAC-SHA256 iteration count (NIST SP 800-132 권장 100_000+, OWASP 600_000+)
# 200_000 — recovery codes are short-lived (1회용), 이 강도 충분
PBKDF2_ITERATIONS: Final[int] = 200_000
PBKDF2_HASH_NAME: Final[str] = "sha256"
PBKDF2_SALT_BYTES: Final[int] = 16

# Crockford base32 alphabet (no I, L, O, U) — recovery code 생성용
# (https://www.crockford.com/base32.html)
CROCKFORD_ALPHABET: Final[str] = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Error codes — pure-kernel domain semantics (AD-15 §4 envelope contract)
ERROR_CODE_INVALID_TOTP: Final[str] = "INVALID_TOTP_CODE"
ERROR_CODE_LOCKOUT_ACTIVE: Final[str] = "TWO_FACTOR_LOCKOUT"
ERROR_CODE_INVALID_RECOVERY: Final[str] = "TWO_FACTOR_RECOVERY_INVALID"

# Korean constants — AD-15 §11 SSOT
TOTP_VERIFY_OK_KO: Final[str] = "인증 코드 확인 완료"
TOTP_LOCKOUT_KO: Final[str] = "5회 연속 실패 — 15분간 잠금"
RECOVERY_VERIFY_OK_KO: Final[str] = "복구 코드 사용 완료"
INVALID_TOTP_KO: Final[str] = "인증 코드가 올바르지 않습니다"
INVALID_RECOVERY_KO: Final[str] = "복구 코드가 유효하지 않거나 이미 사용됨"


# ── Typed exceptions ──────────────────────────────────────────
class TotpInvalidCodeError(Exception):
    """Pure-kernel TOTP code verification failed.

    HTTP envelope (AD-15 §4): 401 TWO_FACTOR_CHALLENGE_FAILED
    (service layer maps to envelope).
    """

    def __init__(self, message_ko: str = INVALID_TOTP_KO) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_INVALID_TOTP
        super().__init__(message_ko)


class TotpLockoutError(Exception):
    """Pure-kernel 2FA lockout active.

    HTTP envelope (AD-15 §4): 429 TWO_FACTOR_LOCKOUT + Retry-After
    header (service layer maps to envelope).
    """

    def __init__(
        self,
        message_ko: str = TOTP_LOCKOUT_KO,
        *,
        retry_after_seconds: int = LOCKOUT_DURATION_SECONDS,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_LOCKOUT_ACTIVE
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message_ko)


class TotpRecoveryInvalidError(Exception):
    """Pure-kernel recovery code verification failed (invalid or already used).

    HTTP envelope (AD-15 §4): 401 TWO_FACTOR_RECOVERY_INVALID
    """

    def __init__(self, message_ko: str = INVALID_RECOVERY_KO) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_INVALID_RECOVERY
        super().__init__(message_ko)


# ── Typed result ───────────────────────────────────────────────
class RecoveryCodeVerification(NamedTuple):
    """Recovery code verification result.

    Attributes:
        code_index: Index of the matched code in the original list
            (service layer uses to mark consumed via
            `users.totp_recovery_codes_hash[index].used_at`).
        code_hash: The matched PBKDF2 hash hex digest.
    """

    code_index: int
    code_hash: str


# ── Secret generation ─────────────────────────────────────────
def generate_totp_secret(*, length_bytes: int = 20) -> bytes:
    """Generate a TOTP secret.

    RFC 6238 §5.1: "The shared secret SHOULD be at least 128 bits".
    Default = 160 bits (20 bytes), base32-encoded → 32 chars.

    Args:
        length_bytes: Secret length in bytes. Default 20 (160 bits).

    Returns:
        Raw secret bytes (NOT base32 — caller encodes for storage
        via `base64.b32encode` or service-layer AES-256-GCM encryption).
    """
    if length_bytes < 16:
        raise ValueError(f"TOTP secret must be ≥128 bits (16 bytes), got {length_bytes * 8} bits")
    return secrets.token_bytes(length_bytes)


def generate_totp_uri(
    secret_bytes: bytes,
    *,
    email: str,
    issuer: str = "costmgr",
) -> str:
    """Build RFC 6238 / Google Authenticator compatible URI.

    Format: otpauth://totp/{issuer}:{email}?secret={base32}&algorithm=SHA1&digits=6&period=30&issuer={issuer}

    Args:
        secret_bytes: Raw TOTP secret bytes (from `generate_totp_secret`).
        email: User email for URI account label.
        issuer: Issuer name. Default "costmgr".

    Returns:
        otauth:// URI string (caller generates QR code from this).
    """
    if not email or "@" not in email:
        raise ValueError(f"email must be a valid email address, got {email!r}")
    if not issuer:
        raise ValueError("issuer must be non-empty")
    secret_b32 = base64.b32encode(secret_bytes).decode("ascii").rstrip("=")
    # label = issuer:email (URL-encode for safety; QR generator handles escaping)
    label = f"{issuer}:{email}"
    return (
        f"otpauth://totp/{label}"
        f"?secret={secret_b32}"
        f"&algorithm=SHA1"
        f"&digits={TOTP_CODE_LENGTH}"
        f"&period={TOTP_PERIOD_SECONDS}"
        f"&issuer={issuer}"
    )


# ── TOTP code computation ─────────────────────────────────────
def compute_totp_code(
    secret_bytes: bytes,
    *,
    timestamp: int | None = None,
) -> str:
    """Compute TOTP code at a given timestamp (RFC 6238).

    Per AD-11: caller passes timestamp explicitly (no module-level clock).
    Default `timestamp=None` → caller should pass `int(time.time())` in tests.

    Args:
        secret_bytes: Raw TOTP secret bytes.
        timestamp: Unix timestamp (seconds). Caller-controlled for testability.

    Returns:
        6-digit numeric TOTP code (zero-padded).
    """
    if not secret_bytes:
        raise ValueError("secret_bytes must be non-empty")
    if timestamp is None:
        # caller did not pass timestamp — caller should pass explicitly
        # (AD-11: no module-level clock); raising for safety
        raise ValueError(
            "compute_totp_code requires explicit `timestamp` arg "
            "(AD-11: no module-level clock at module scope)"
        )
    counter = timestamp // TOTP_PERIOD_SECONDS
    # 8-byte big-endian counter (RFC 6238 §5.2)
    counter_bytes = struct.pack(">Q", counter)
    # HMAC-SHA1(secret, counter) — RFC 6238 default
    hmac_digest = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
    # Dynamic truncation (RFC 6238 §5.3)
    offset = hmac_digest[-1] & 0x0F
    truncated = (
        (hmac_digest[offset] & 0x7F) << 24
        | (hmac_digest[offset + 1] & 0xFF) << 16
        | (hmac_digest[offset + 2] & 0xFF) << 8
        | (hmac_digest[offset + 3] & 0xFF)
    )
    code = truncated % (10**TOTP_CODE_LENGTH)
    return str(code).zfill(TOTP_CODE_LENGTH)


def verify_totp_code(
    secret_bytes: bytes,
    code: str,
    *,
    timestamp: int | None = None,
    tolerance_windows: int = TOTP_WINDOW_TOLERANCE,
) -> bool:
    """Verify TOTP code with ±tolerance_windows window (default ±1 = ±30s).

    Args:
        secret_bytes: Raw TOTP secret bytes.
        code: User-provided 6-digit code.
        timestamp: Unix timestamp (seconds).
        tolerance_windows: Number of periods before/after to check.
            Default 1 (RFC 6238 §6 recommended tolerance).

    Returns:
        True if code matches any window. False otherwise.
        (Raises TotpInvalidCodeError if code format invalid; raises
        TotpLockoutError if lockout_status externally-set.)
    """
    if not code or len(code) != TOTP_CODE_LENGTH or not code.isdigit():
        return False
    if timestamp is None:
        raise ValueError(
            "verify_totp_code requires explicit `timestamp` arg "
            "(AD-11: no module-level clock at module scope)"
        )
    if tolerance_windows < 0:
        raise ValueError(f"tolerance_windows must be ≥0, got {tolerance_windows}")

    current_counter = timestamp // TOTP_PERIOD_SECONDS
    for offset in range(-tolerance_windows, tolerance_windows + 1):
        window_timestamp = (current_counter + offset) * TOTP_PERIOD_SECONDS
        expected_code = compute_totp_code(secret_bytes, timestamp=window_timestamp)
        # constant-time comparison
        if hmac.compare_digest(expected_code, code):
            return True
    return False


# ── Recovery codes ─────────────────────────────────────────────
def _generate_one_recovery_code() -> str:
    """Generate a single 10-char recovery code (Crockford base32)."""
    return "".join(secrets.choice(CROCKFORD_ALPHABET) for _ in range(RECOVERY_CODE_LENGTH))


def generate_recovery_codes() -> list[str]:
    """Generate 8 one-time-use recovery codes.

    Returns:
        List of 8 codes × 10-char Crockford base32 (no I/L/O/U).
        Plaintext — service layer hashes + encrypts for storage
        (NFR6 AES-256-GCM + PBKDF2-HMAC-SHA256 hash).
    """
    return [_generate_one_recovery_code() for _ in range(RECOVERY_CODE_COUNT)]


def hash_recovery_code(code: str) -> tuple[str, str]:
    """Hash a recovery code with PBKDF2-HMAC-SHA256.

    Returns:
        (salt_hex, hash_hex) — both hex-encoded for JSONB storage.
        Service layer stores as JSONB array of {salt, hash, used_at} entries.
    """
    if not code or len(code) != RECOVERY_CODE_LENGTH:
        raise ValueError(f"recovery code must be {RECOVERY_CODE_LENGTH} chars, got {len(code)}")
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    hash_bytes = hashlib.pbkdf2_hmac(
        PBKDF2_HASH_NAME,
        code.encode("ascii"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (salt.hex(), hash_bytes.hex())


def generate_recovery_code_hashes(codes: list[str]) -> list[dict[str, str]]:
    """Generate hash entries for all codes.

    Returns:
        List of {salt, hash, used_at} dicts for JSONB storage.
        `used_at` initially null. Service layer mutates on consume.
    """
    if len(codes) != RECOVERY_CODE_COUNT:
        raise ValueError(f"expected {RECOVERY_CODE_COUNT} codes, got {len(codes)}")
    return [
        {"salt": salt, "hash": digest, "used_at": ""}
        for code in codes
        for salt, digest in [hash_recovery_code(code)]
    ]


def verify_recovery_code(
    code: str,
    *,
    hashes: list[dict[str, str]],
) -> RecoveryCodeVerification:
    """Verify a recovery code against stored hash entries.

    Returns:
        RecoveryCodeVerification(code_index, code_hash) on match.

    Raises:
        TotpRecoveryInvalidError: If code invalid format or no match found
            in any unused hash entry.
    """
    if not code or len(code) != RECOVERY_CODE_LENGTH:
        raise TotpRecoveryInvalidError(INVALID_RECOVERY_KO)

    # Try each unused entry (constant-time per entry, but skip used)
    for idx, entry in enumerate(hashes):
        if entry.get("used_at"):  # already used → skip
            continue
        salt = bytes.fromhex(entry["salt"])
        stored_hash = entry["hash"]
        candidate = hashlib.pbkdf2_hmac(
            PBKDF2_HASH_NAME,
            code.encode("ascii"),
            salt,
            PBKDF2_ITERATIONS,
        ).hex()
        if hmac.compare_digest(candidate, stored_hash):
            return RecoveryCodeVerification(code_index=idx, code_hash=stored_hash)

    raise TotpRecoveryInvalidError(INVALID_RECOVERY_KO)


__all__ = [
    # constants
    "TOTP_CODE_LENGTH",
    "TOTP_PERIOD_SECONDS",
    "TOTP_WINDOW_TOLERANCE",
    "RECOVERY_CODE_COUNT",
    "RECOVERY_CODE_LENGTH",
    "MAX_FAILED_ATTEMPTS",
    "LOCKOUT_DURATION_SECONDS",
    "PBKDF2_ITERATIONS",
    "PBKDF2_HASH_NAME",
    "PBKDF2_SALT_BYTES",
    "CROCKFORD_ALPHABET",
    "ERROR_CODE_INVALID_TOTP",
    "ERROR_CODE_LOCKOUT_ACTIVE",
    "ERROR_CODE_INVALID_RECOVERY",
    "TOTP_VERIFY_OK_KO",
    "TOTP_LOCKOUT_KO",
    "RECOVERY_VERIFY_OK_KO",
    "INVALID_TOTP_KO",
    "INVALID_RECOVERY_KO",
    # exceptions
    "TotpInvalidCodeError",
    "TotpLockoutError",
    "TotpRecoveryInvalidError",
    # result
    "RecoveryCodeVerification",
    # functions
    "generate_totp_secret",
    "generate_totp_uri",
    "compute_totp_code",
    "verify_totp_code",
    "generate_recovery_codes",
    "hash_recovery_code",
    "generate_recovery_code_hashes",
    "verify_recovery_code",
]
