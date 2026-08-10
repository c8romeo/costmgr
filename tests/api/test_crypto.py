"""tests.api.test_crypto — T5 AES-256-GCM crypto helper tests.

Coverage:
- Round-trip encrypt/decrypt (aad=None + aad=set)
- Decryption failure paths (wrong key, tampered ciphertext, too short)
- Key rotation (rotate_key)
- generate_key_bytes + key_id_to_env_var + load_key_bytes_from_env
"""

from __future__ import annotations

import os

import pytest

from apps.api.core.crypto import (
    DEFAULT_KEY_ID,
    KEY_BYTES,
    NONCE_BYTES,
    TAG_BYTES,
    CryptoError,
    DecryptionFailedError,
    decrypt_at_rest,
    encrypt_at_rest,
    generate_key_bytes,
    key_id_to_env_var,
    load_key_bytes_from_env,
    rotate_key,
)
from apps.api.core.key_manager import (
    clear_keys,
    get_active_key,
    list_key_versions,
    set_key,
)


# ── Fixtures ────────────────────────────────────────────────
@pytest.fixture
def fixed_key_bytes() -> bytes:
    """Deterministic 32-byte key for test reproducibility."""
    return bytes.fromhex("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")


@pytest.fixture
def alt_key_bytes() -> bytes:
    """Alternative 32-byte key for rotation tests."""
    return bytes.fromhex("fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210")


@pytest.fixture(autouse=True)
def reset_key_cache() -> None:
    """Clear key cache before each test (test isolation)."""
    clear_keys()
    yield
    clear_keys()


# ── Test #1: Round-trip encrypt/decrypt ─────────────────────
class TestRoundTrip:
    """AES-256-GCM encrypt + decrypt cycle."""

    def test_roundtrip_basic(
        self, fixed_key_bytes: bytes
    ) -> None:
        """encrypt(plaintext) → decrypt(ciphertext) → plaintext."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        plaintext = b"hello world"
        ciphertext = encrypt_at_rest(plaintext)
        assert decrypt_at_rest(ciphertext) == plaintext

    def test_roundtrip_binary(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Binary plaintext (e.g., TOTP secret bytes)."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        plaintext = bytes(range(32))  # arbitrary 32 bytes
        ciphertext = encrypt_at_rest(plaintext)
        assert decrypt_at_rest(ciphertext) == plaintext

    def test_roundtrip_with_aad(
        self, fixed_key_bytes: bytes
    ) -> None:
        """AAD-bound ciphertext: decrypt with matching AAD succeeds."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        plaintext = b"aad-bound payload"
        aad = b"totp_secret"
        ciphertext = encrypt_at_rest(plaintext, aad=aad)
        assert decrypt_at_rest(ciphertext, aad=aad) == plaintext

    def test_roundtrip_with_aad_wrong_aad_fails(
        self, fixed_key_bytes: bytes
    ) -> None:
        """AAD mismatch → DecryptionFailedError (auth tag verification fails)."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        plaintext = b"aad-bound payload"
        ciphertext = encrypt_at_rest(plaintext, aad=b"totp_secret")
        with pytest.raises(DecryptionFailedError):
            decrypt_at_rest(ciphertext, aad=b"different_column")

    def test_roundtrip_large_payload(
        self, fixed_key_bytes: bytes
    ) -> None:
        """1 MB plaintext."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        plaintext = b"X" * (1024 * 1024)
        ciphertext = encrypt_at_rest(plaintext)
        assert decrypt_at_rest(ciphertext) == plaintext

    def test_ciphertext_includes_nonce_and_tag(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Ciphertext = nonce (12) + ct + tag (16). Length = plaintext + 28."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        plaintext = b"x" * 100
        ciphertext = encrypt_at_rest(plaintext)
        assert len(ciphertext) == 100 + NONCE_BYTES + TAG_BYTES

    def test_each_encryption_uses_random_nonce(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Same plaintext + same key → different ciphertexts (nonce randomness)."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        plaintext = b"same plaintext"
        ct1 = encrypt_at_rest(plaintext)
        ct2 = encrypt_at_rest(plaintext)
        assert ct1 != ct2
        # Both should decrypt to same plaintext
        assert decrypt_at_rest(ct1) == plaintext
        assert decrypt_at_rest(ct2) == plaintext


# ── Test #2: Decryption failure paths ────────────────────────
class TestDecryptionFailures:
    """Failure modes — wrong key, tampered ciphertext, too short."""

    def test_decrypt_with_wrong_key_fails(
        self, fixed_key_bytes: bytes, alt_key_bytes: bytes
    ) -> None:
        """Ciphertext encrypted with key1 cannot decrypt with key2."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        ciphertext = encrypt_at_rest(b"payload")
        # Switch to alt key
        set_key(DEFAULT_KEY_ID, alt_key_bytes)
        with pytest.raises(DecryptionFailedError):
            decrypt_at_rest(ciphertext)

    def test_decrypt_tampered_ciphertext_fails(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Flipping a ciphertext byte → authentication tag fails."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        ciphertext = bytearray(encrypt_at_rest(b"payload"))
        ciphertext[len(ciphertext) // 2] ^= 0xFF  # tamper
        with pytest.raises(DecryptionFailedError):
            decrypt_at_rest(bytes(ciphertext))

    def test_decrypt_tampered_nonce_fails(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Tampering nonce → decryption fails (different keystream)."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        ciphertext = bytearray(encrypt_at_rest(b"payload"))
        ciphertext[0] ^= 0xFF  # tamper nonce
        with pytest.raises(DecryptionFailedError):
            decrypt_at_rest(bytes(ciphertext))

    def test_decrypt_too_short_fails(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Ciphertext < 28 bytes (nonce + tag min) → DecryptionFailedError."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        with pytest.raises(DecryptionFailedError, match="too short"):
            decrypt_at_rest(b"short")

    def test_decrypt_empty_fails(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Empty ciphertext → DecryptionFailedError."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        with pytest.raises(DecryptionFailedError, match="too short"):
            decrypt_at_rest(b"")


# ── Test #3: Encrypt validation ──────────────────────────────
class TestEncryptValidation:
    """encrypt_at_rest() input validation."""

    def test_encrypt_empty_plaintext_fails(
        self, fixed_key_bytes: bytes
    ) -> None:
        """Empty plaintext → ValueError."""
        set_key(DEFAULT_KEY_ID, fixed_key_bytes)
        with pytest.raises(ValueError, match="non-empty"):
            encrypt_at_rest(b"")


# ── Test #4: Key rotation ───────────────────────────────────
class TestKeyRotation:
    """rotate_key — re-encrypt with new key."""

    def test_rotate_key_basic(
        self, fixed_key_bytes: bytes, alt_key_bytes: bytes
    ) -> None:
        """rotate(v1 → v2) → ciphertext decrypts with v2."""
        set_key("v1", fixed_key_bytes)
        set_key("v2", alt_key_bytes)
        plaintext = b"rotation test"
        ct_v1 = encrypt_at_rest(plaintext, key_id="v1")
        # Rotate
        ct_v2 = rotate_key(ct_v1, old_key_id="v1", new_key_id="v2")
        # Verify v2 key can decrypt
        assert decrypt_at_rest(ct_v2, key_id="v2") == plaintext

    def test_rotate_key_with_aad(
        self, fixed_key_bytes: bytes, alt_key_bytes: bytes
    ) -> None:
        """Rotation preserves AAD context."""
        set_key("v1", fixed_key_bytes)
        set_key("v2", alt_key_bytes)
        ct_v1 = encrypt_at_rest(b"payload", key_id="v1", aad=b"my_column")
        ct_v2 = rotate_key(ct_v1, old_key_id="v1", new_key_id="v2", aad=b"my_column")
        assert decrypt_at_rest(ct_v2, key_id="v2", aad=b"my_column") == b"payload"
        # Wrong AAD fails
        with pytest.raises(DecryptionFailedError):
            decrypt_at_rest(ct_v2, key_id="v2", aad=b"different")


# ── Test #5: Key generation + env-var ────────────────────────
class TestKeyGeneration:
    """generate_key_bytes + env-var helpers."""

    def test_generate_key_bytes_length(self) -> None:
        """32 bytes (256 bits)."""
        key = generate_key_bytes()
        assert len(key) == KEY_BYTES == 32

    def test_generate_key_bytes_unique(self) -> None:
        """Random + cryptographically strong."""
        keys = [generate_key_bytes() for _ in range(10)]
        assert len(set(keys)) == 10

    def test_key_id_to_env_var(self) -> None:
        """COSTMGR_AT_REST_KEY_<KEY_ID> (uppercase + sanitized)."""
        assert key_id_to_env_var("v1") == "COSTMGR_AT_REST_KEY_V1"
        assert key_id_to_env_var("v2") == "COSTMGR_AT_REST_KEY_V2"
        assert key_id_to_env_var("with-dash") == "COSTMGR_AT_REST_KEY_WITH_DASH"
        assert key_id_to_env_var("with.dot") == "COSTMGR_AT_REST_KEY_WITH_DOT"

    def test_load_key_bytes_from_env(self) -> None:
        """Read hex-encoded key from env-var."""
        os.environ["COSTMGR_AT_REST_KEY_V1"] = (
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        )
        key = load_key_bytes_from_env("v1")
        assert key is not None
        assert len(key) == 32
        assert key == bytes.fromhex(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        )

    def test_load_key_bytes_from_env_missing(self) -> None:
        """Env-var not set → None."""
        os.environ.pop("COSTMGR_AT_REST_KEY_MISSING", None)
        assert load_key_bytes_from_env("missing") is None

    def test_load_key_bytes_from_env_invalid_hex(self) -> None:
        """Invalid hex → CryptoError."""
        os.environ["COSTMGR_AT_REST_KEY_BAD"] = "not-hex-data"
        with pytest.raises(CryptoError, match="Invalid hex"):
            load_key_bytes_from_env("bad")


# ── Test #6: Key manager ────────────────────────────────────
class TestKeyManager:
    """set_key + list_key_versions + get_active_key cache."""

    def test_set_key_length_validation(self) -> None:
        """Wrong key length → ValueError."""
        with pytest.raises(ValueError, match="32 bytes"):
            set_key("v1", b"too_short")

    def test_set_key_and_get_active_key(self, fixed_key_bytes: bytes) -> None:
        """set_key → get_active_key returns same bytes."""
        set_key("v1", fixed_key_bytes)
        assert get_active_key("v1") == fixed_key_bytes

    def test_get_active_key_ephemeral_fallback(self) -> None:
        """No env-var + no cache → ephemeral key (different per call)."""
        # clear_keys already done by autouse fixture
        key1 = get_active_key("nonexistent")
        # Second call should return same ephemeral key (cached)
        key2 = get_active_key("nonexistent")
        assert len(key1) == 32
        assert key1 == key2  # cached

    def test_list_key_versions(self, fixed_key_bytes: bytes) -> None:
        """set_key adds to list."""
        set_key("v1", fixed_key_bytes)
        set_key("v2", fixed_key_bytes)
        versions = list_key_versions()
        assert "v1" in versions
        assert "v2" in versions

    def test_clear_keys(self, fixed_key_bytes: bytes) -> None:
        """clear_keys empties cache."""
        set_key("v1", fixed_key_bytes)
        clear_keys()
        assert list_key_versions() == []
