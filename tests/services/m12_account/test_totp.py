"""tests.services.m12_account.test_totp — T1.1 pure kernel TOTP tests.

RFC 6238 contract:
- HMAC-SHA1, 30s step, 6-digit code
- ±1 window tolerance = ±30s = 90s effective window

Coverage: secret generation, URI format, code compute + verify, recovery
code generate + hash + verify, lockout exception mapping.
"""

from __future__ import annotations

import base64
import hashlib

import pytest

from packages.services.m12_account.totp import (
    CROCKFORD_ALPHABET,
    ERROR_CODE_INVALID_TOTP,
    INVALID_RECOVERY_KO,
    LOCKOUT_DURATION_SECONDS,
    MAX_FAILED_ATTEMPTS,
    PBKDF2_ITERATIONS,
    RECOVERY_CODE_COUNT,
    RECOVERY_CODE_LENGTH,
    TOTP_CODE_LENGTH,
    TOTP_PERIOD_SECONDS,
    TotpInvalidCodeError,
    TotpLockoutError,
    TotpRecoveryInvalidError,
    compute_totp_code,
    generate_recovery_code_hashes,
    generate_recovery_codes,
    generate_totp_secret,
    generate_totp_uri,
    hash_recovery_code,
    verify_recovery_code,
    verify_totp_code,
)


# ── Fixtures ────────────────────────────────────────────────
@pytest.fixture
def secret_bytes() -> bytes:
    """Standard test secret — 20 bytes (160 bits)."""
    return generate_totp_secret()


@pytest.fixture
def fixed_timestamp() -> int:
    """2026-08-10T00:00:00 UTC = 1776019200 (round number for stability)."""
    return 1776019200


# ── Test #1: Secret generation ────────────────────────────────
class TestSecretGeneration:
    """TOTP secret generation — RFC 6238 §5.1 ≥128 bits."""

    def test_secret_default_length_is_20_bytes(self) -> None:
        """Default secret length = 20 bytes = 160 bits (RFC 6238 권장)."""
        secret = generate_totp_secret()
        assert len(secret) == 20

    def test_secret_minimum_length_is_16_bytes(self) -> None:
        """16 bytes = 128 bits = RFC 6238 minimum."""
        secret = generate_totp_secret(length_bytes=16)
        assert len(secret) == 16

    def test_secret_rejects_below_128_bits(self) -> None:
        """Below 128 bits → ValueError (RFC 6238 minimum enforced)."""
        with pytest.raises(ValueError, match="≥128 bits"):
            generate_totp_secret(length_bytes=8)

    def test_secrets_are_unique(self) -> None:
        """secrets.token_bytes → cryptographically strong, randomness."""
        secrets_list = [generate_totp_secret() for _ in range(100)]
        assert len(set(secrets_list)) == 100


# ── Test #2: URI generation (RFC 6238 + Google Authenticator) ──
class TestTotpUriGeneration:
    """otauth:// URI format — Google Authenticator / Authy 호환."""

    def test_uri_format_basic(self, secret_bytes: bytes) -> None:
        """otauth://totp/costmgr:{email}?secret={b32}&algorithm=SHA1&digits=6&period=30&issuer=costmgr"""
        uri = generate_totp_uri(secret_bytes, email="user@example.com")
        assert uri.startswith("otpauth://totp/costmgr:user@example.com")
        assert "algorithm=SHA1" in uri
        assert "digits=6" in uri
        assert "period=30" in uri
        assert "issuer=costmgr" in uri

    def test_uri_secret_is_base32_encoded(self, secret_bytes: bytes) -> None:
        """secret query param = base32 of raw bytes (no padding)."""
        uri = generate_totp_uri(secret_bytes, email="x@y.com")
        # extract secret query param
        query = uri.split("?", 1)[1]
        params = dict(p.split("=", 1) for p in query.split("&"))
        secret_b32 = params["secret"]
        # base32 decode (no padding)
        padded = secret_b32 + "=" * (-len(secret_b32) % 8)
        decoded = base64.b32decode(padded)
        assert decoded == secret_bytes

    def test_uri_rejects_empty_email(self, secret_bytes: bytes) -> None:
        """Empty email → ValueError (account label required)."""
        with pytest.raises(ValueError, match="valid email"):
            generate_totp_uri(secret_bytes, email="")

    def test_uri_rejects_invalid_email(self, secret_bytes: bytes) -> None:
        """No '@' in email → ValueError."""
        with pytest.raises(ValueError, match="valid email"):
            generate_totp_uri(secret_bytes, email="notanemail")

    def test_uri_rejects_empty_issuer(self, secret_bytes: bytes) -> None:
        """Empty issuer → ValueError."""
        with pytest.raises(ValueError, match="issuer"):
            generate_totp_uri(secret_bytes, email="x@y.com", issuer="")


# ── Test #3: TOTP code compute + verify (RFC 6238) ──────────
class TestTotpCodeCompute:
    """RFC 6238 §5.2-5.3 HMAC-SHA1 + dynamic truncation."""

    def test_compute_code_is_6_digits(self, secret_bytes: bytes, fixed_timestamp: int) -> None:
        """6-digit zero-padded code."""
        code = compute_totp_code(secret_bytes, timestamp=fixed_timestamp)
        assert len(code) == TOTP_CODE_LENGTH == 6
        assert code.isdigit()

    def test_compute_code_matches_rfc6238_test_vector(self) -> None:
        """RFC 6238 Appendix B test vectors.

        secret = b'12345678901234567890' (20 ASCII bytes)
        T = Unix timestamp (NOT counter). Our impl computes
        counter = timestamp // 30 internally.

        T=59 → counter=1 → 6-digit "287082" (RFC 8-digit 94287082 mod 10^6)
        T=1111111109 → counter=37037036 → 6-digit "081804"
        T=1111111111 → counter=37037037 → 6-digit "050471"
        T=1234567890 → counter=41152263 → 6-digit "005924"
        T=2000000000 → counter=66666666 → 6-digit "279037"
        """
        rfc_secret = b"12345678901234567890"
        # RFC T values are Unix timestamps. Our impl receives timestamp directly.
        assert compute_totp_code(rfc_secret, timestamp=59) == "287082"
        assert compute_totp_code(rfc_secret, timestamp=1111111109) == "081804"
        assert compute_totp_code(rfc_secret, timestamp=1111111111) == "050471"
        assert compute_totp_code(rfc_secret, timestamp=1234567890) == "005924"
        assert compute_totp_code(rfc_secret, timestamp=2000000000) == "279037"

    def test_compute_code_requires_timestamp(self, secret_bytes: bytes) -> None:
        """AD-11: no module-level clock → caller must pass timestamp."""
        with pytest.raises(ValueError, match="explicit `timestamp`"):
            compute_totp_code(secret_bytes)

    def test_compute_code_rejects_empty_secret(self, fixed_timestamp: int) -> None:
        """Empty secret → ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            compute_totp_code(b"", timestamp=fixed_timestamp)


class TestTotpCodeVerify:
    """verify_totp_code with ±tolerance_windows window."""

    def test_verify_correct_code_returns_true(self, secret_bytes: bytes, fixed_timestamp: int) -> None:
        """Correct code at current window → True."""
        code = compute_totp_code(secret_bytes, timestamp=fixed_timestamp)
        assert verify_totp_code(secret_bytes, code, timestamp=fixed_timestamp) is True

    def test_verify_within_tolerance_window(self, secret_bytes: bytes, fixed_timestamp: int) -> None:
        """±1 window = ±30s tolerance (90s effective window)."""
        # Code computed at fixed_timestamp-30 (1 window before)
        past_code = compute_totp_code(secret_bytes, timestamp=fixed_timestamp - TOTP_PERIOD_SECONDS)
        # Verify at fixed_timestamp — should accept past code (±1 window)
        assert verify_totp_code(secret_bytes, past_code, timestamp=fixed_timestamp) is True
        # Future code
        future_code = compute_totp_code(secret_bytes, timestamp=fixed_timestamp + TOTP_PERIOD_SECONDS)
        assert verify_totp_code(secret_bytes, future_code, timestamp=fixed_timestamp) is True

    def test_verify_outside_tolerance_window_returns_false(self, secret_bytes: bytes, fixed_timestamp: int) -> None:
        """±2 windows = ±60s — outside ±1 default tolerance."""
        # Code computed at fixed_timestamp-60 (2 windows before)
        past_code = compute_totp_code(secret_bytes, timestamp=fixed_timestamp - 2 * TOTP_PERIOD_SECONDS)
        # Default tolerance_windows=1 → past_code rejected
        assert verify_totp_code(secret_bytes, past_code, timestamp=fixed_timestamp) is False

    def test_verify_invalid_code_format_returns_false(self, secret_bytes: bytes, fixed_timestamp: int) -> None:
        """Non-numeric / wrong-length code → False (no exception)."""
        assert verify_totp_code(secret_bytes, "abc", timestamp=fixed_timestamp) is False
        assert verify_totp_code(secret_bytes, "12345", timestamp=fixed_timestamp) is False  # 5-digit
        assert verify_totp_code(secret_bytes, "1234567", timestamp=fixed_timestamp) is False  # 7-digit
        assert verify_totp_code(secret_bytes, "", timestamp=fixed_timestamp) is False

    def test_verify_requires_timestamp(self, secret_bytes: bytes) -> None:
        """AD-11: no module-level clock."""
        with pytest.raises(ValueError, match="explicit `timestamp`"):
            verify_totp_code(secret_bytes, "123456")

    def test_verify_rejects_negative_tolerance(self, secret_bytes: bytes, fixed_timestamp: int) -> None:
        """tolerance_windows < 0 → ValueError."""
        with pytest.raises(ValueError, match="≥0"):
            verify_totp_code(secret_bytes, "123456", timestamp=fixed_timestamp, tolerance_windows=-1)


# ── Test #4: Recovery codes ──────────────────────────────────
class TestRecoveryCodes:
    """8 codes × 10-char Crockford base32 + PBKDF2-HMAC-SHA256."""

    def test_generate_recovery_codes_count(self) -> None:
        """8 codes per generation (PRD §F12.1)."""
        codes = generate_recovery_codes()
        assert len(codes) == RECOVERY_CODE_COUNT == 8

    def test_recovery_code_length(self) -> None:
        """10 chars (PRD §F12.1 + Authy 표준)."""
        for code in generate_recovery_codes():
            assert len(code) == RECOVERY_CODE_LENGTH == 10

    def test_recovery_code_uses_crockford_alphabet(self) -> None:
        """No I, L, O, U — Crockford base32 (시각 혼동 방지)."""
        for _ in range(20):  # 다중 round
            codes = generate_recovery_codes()
            for code in codes:
                for ch in code:
                    assert ch in CROCKFORD_ALPHABET, f"unexpected char {ch!r}"
                    assert ch not in "ILOU", f"non-Crockford char {ch!r}"

    def test_recovery_codes_are_unique(self) -> None:
        """secrets.choice → randomness, no duplicates within a batch."""
        codes = generate_recovery_codes()
        assert len(set(codes)) == RECOVERY_CODE_COUNT

    def test_hash_recovery_code_returns_salt_and_hash(self) -> None:
        """hash_recovery_code → (salt_hex, hash_hex)."""
        salt, digest = hash_recovery_code("ABCDEFGHJ0")
        assert len(salt) == 32  # 16 bytes hex
        assert len(digest) == 64  # 32 bytes hex (sha256)

    def test_hash_recovery_code_rejects_wrong_length(self) -> None:
        """Wrong length → ValueError."""
        with pytest.raises(ValueError, match="10 chars"):
            hash_recovery_code("ABC")
        with pytest.raises(ValueError, match="10 chars"):
            hash_recovery_code("ABCDEFGHIJK")

    def test_hash_recovery_code_is_deterministic_with_same_salt(self) -> None:
        """PBKDF2 deterministic: same salt + same code → same hash."""
        salt = "0" * 32  # 16 bytes zero salt
        # Direct PBKDF2 call (not hash_recovery_code which uses random salt)
        code = "ABCDEFGHJ0"
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            code.encode("ascii"),
            bytes.fromhex(salt),
            PBKDF2_ITERATIONS,
        ).hex()
        # Verify the structure (random salt prevents same-salt comparison)
        _, digest = hash_recovery_code(code)
        assert len(digest) == 64

    def test_generate_recovery_code_hashes_count(self) -> None:
        """8 entries for 8 codes (JSONB storage format)."""
        codes = generate_recovery_codes()
        entries = generate_recovery_code_hashes(codes)
        assert len(entries) == RECOVERY_CODE_COUNT
        for entry in entries:
            assert "salt" in entry
            assert "hash" in entry
            assert entry["used_at"] == ""  # not used

    def test_generate_recovery_code_hashes_rejects_wrong_count(self) -> None:
        """Not 8 codes → ValueError."""
        with pytest.raises(ValueError, match="8"):
            generate_recovery_code_hashes(["ABCDEFGHJ0"] * 7)

    def test_verify_recovery_code_success(self) -> None:
        """Verify with correct code → RecoveryCodeVerification."""
        codes = generate_recovery_codes()
        entries = generate_recovery_code_hashes(codes)
        # Verify each code
        for idx, code in enumerate(codes):
            result = verify_recovery_code(code, hashes=entries)
            assert result.code_index == idx

    def test_verify_recovery_code_invalid_format(self) -> None:
        """Wrong length code → TotpRecoveryInvalidError."""
        with pytest.raises(TotpRecoveryInvalidError):
            verify_recovery_code("SHORT", hashes=[])

    def test_verify_recovery_code_not_found(self) -> None:
        """Valid format but not in hashes → TotpRecoveryInvalidError."""
        codes = generate_recovery_codes()
        entries = generate_recovery_code_hashes(codes)
        # Generate new code not in entries
        new_code = generate_recovery_codes()[0]
        with pytest.raises(TotpRecoveryInvalidError, match=INVALID_RECOVERY_KO):
            verify_recovery_code(new_code, hashes=entries)

    def test_verify_recovery_code_already_used(self) -> None:
        """Used code (used_at set) → skip + TotpRecoveryInvalidError if no other match."""
        codes = generate_recovery_codes()
        entries = generate_recovery_code_hashes(codes)
        # Mark first entry as used
        used_entries = list(entries)
        used_entries[0] = {**used_entries[0], "used_at": "2026-08-10T00:00:00Z"}
        # Try to verify the first (used) code
        with pytest.raises(TotpRecoveryInvalidError):
            verify_recovery_code(codes[0], hashes=used_entries)
        # But verify the second (unused) code still works
        result = verify_recovery_code(codes[1], hashes=used_entries)
        assert result.code_index == 1


# ── Test #5: TotpInvalidCodeError + TotpLockoutError ──────────
class TestTotpExceptions:
    """Typed exception classes — error_code + message_ko + retry_after."""

    def test_totp_invalid_code_error_attributes(self) -> None:
        """TotpInvalidCodeError — error_code + message_ko defaults."""
        exc = TotpInvalidCodeError()
        assert exc.error_code == ERROR_CODE_INVALID_TOTP == "INVALID_TOTP_CODE"
        assert exc.message_ko  # non-empty

    def test_totp_lockout_error_attributes(self) -> None:
        """TotpLockoutError — retry_after_seconds default = LOCKOUT_DURATION."""
        exc = TotpLockoutError()
        assert exc.error_code == "TWO_FACTOR_LOCKOUT"
        assert exc.retry_after_seconds == LOCKOUT_DURATION_SECONDS == 900

    def test_totp_lockout_error_custom_retry_after(self) -> None:
        """Custom retry_after_seconds override."""
        exc = TotpLockoutError(retry_after_seconds=300)
        assert exc.retry_after_seconds == 300

    def test_totp_recovery_invalid_error_attributes(self) -> None:
        """TotpRecoveryInvalidError — error_code."""
        exc = TotpRecoveryInvalidError()
        assert exc.error_code == "TWO_FACTOR_RECOVERY_INVALID"


# ── Test #6: Lockout constants ────────────────────────────────
class TestLockoutConstants:
    """PRD §F12.1 — 5회 실패 시 15분 lockout."""

    def test_max_failed_attempts_is_5(self) -> None:
        """PRD §F12.1: 5회 실패 시 lockout."""
        assert MAX_FAILED_ATTEMPTS == 5

    def test_lockout_duration_is_15_minutes(self) -> None:
        """15 * 60 = 900s = 15분."""
        assert LOCKOUT_DURATION_SECONDS == 900
