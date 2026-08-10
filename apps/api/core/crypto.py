"""apps.api.core.crypto — NFR6 AES-256-GCM column-level encryption helper.

Story 12.1 (Epic 12 cj-style 1번째) — 2FA secret column encryption.

AD-11 layer rule: pure helper in `apps/api/core/` (infra layer). Service
layer (`apps/api/modules/m12_account/services/`) imports `encrypt_at_rest`
+ `decrypt_at_rest` to wrap `users.totp_secret` BYTEA storage.

NFR6 AES-256-GCM column-level encryption:
- 96-bit (12-byte) nonce (NIST SP 800-38D recommended for GCM)
- 256-bit (32-byte) key
- 128-bit (16-byte) authentication tag (GCM default)
- Output format: nonce (12 bytes) || ciphertext || tag (16 bytes)
- Total overhead: 28 bytes

Key management: via `apps/api/core/key_manager.py` — `get_active_key()`
returns key bytes from env-var (COSTMGR_AT_REST_KEY_ID + matching key bytes)
or KMS-managed key.

Production key rotation:
- `rotate_key(old_key_id, new_key_id)` re-encrypts a value with the new key
- Service layer invokes this via background job
- `key_manager.list_key_versions()` returns rotation history

This module is stdlib-only + `cryptography` library (PyPI). It does NOT
import `packages.cost_engine` or any tenant-bound modules (per AD-11).
"""

from __future__ import annotations

import os
import secrets
from typing import Final

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Constants ────────────────────────────────────────────────
# AES-256-GCM parameters (NIST SP 800-38D)
NONCE_BYTES: Final[int] = 12  # 96 bits
KEY_BYTES: Final[int] = 32  # 256 bits
TAG_BYTES: Final[int] = 16  # 128 bits (AES-GCM default)


# Lazy import to break circular dependency (crypto ↔ key_manager)
def _get_active_key(key_id: str) -> bytes:
    """Lazy import wrapper for key_manager.get_active_key."""
    from apps.api.core.key_manager import get_active_key as _get

    return _get(key_id)

# Default key_id (env-var overridable)
DEFAULT_KEY_ID: Final[str] = "v1"


# ── Typed exceptions ──────────────────────────────────────────
class CryptoError(Exception):
    """Base crypto helper error."""


class DecryptionFailedError(CryptoError):
    """Decryption failed — invalid ciphertext / wrong key / tampered data.

    Raised when AES-GCM authentication tag verification fails.
    Indicates either:
    - Key mismatch (rotated without re-encrypting)
    - Ciphertext corruption
    - Tampering attempt
    """

    def __init__(self, message: str = "Decryption failed — invalid key or tampered ciphertext") -> None:
        super().__init__(message)


class KeyNotFoundError(CryptoError):
    """Key not found in key_manager."""

    def __init__(self, key_id: str) -> None:
        self.key_id = key_id
        super().__init__(f"Crypto key not found: key_id={key_id!r}")


# ── Encrypt ──────────────────────────────────────────────────
def encrypt_at_rest(
    plaintext: bytes,
    *,
    key_id: str = DEFAULT_KEY_ID,
    aad: bytes | None = None,
) -> bytes:
    """Encrypt plaintext at rest using AES-256-GCM.

    Args:
        plaintext: Data to encrypt (e.g., raw TOTP secret bytes).
        key_id: Key version identifier (rotation key). Default "v1".
        aad: Additional Authenticated Data (AAD). Optional context bytes
            bound to ciphertext (e.g., b"totp_secret" for column binding).
            Service layer should pass distinct AAD per column.

    Returns:
        Ciphertext blob (nonce 12 bytes || ciphertext || tag 16 bytes).
        Service layer stores as BYTEA.
    """
    if not plaintext:
        raise ValueError("plaintext must be non-empty")

    key = _get_active_key(key_id)
    nonce = secrets.token_bytes(NONCE_BYTES)
    cipher = AESGCM(key)
    # AESGCM.encrypt() returns ciphertext || tag (16 bytes)
    ct_with_tag = cipher.encrypt(nonce, plaintext, aad or b"")
    # Return nonce || ciphertext || tag (28-byte overhead)
    return nonce + ct_with_tag


# ── Decrypt ──────────────────────────────────────────────────
def decrypt_at_rest(
    ciphertext_blob: bytes,
    *,
    key_id: str = DEFAULT_KEY_ID,
    aad: bytes | None = None,
) -> bytes:
    """Decrypt ciphertext at rest using AES-256-GCM.

    Args:
        ciphertext_blob: nonce (12 bytes) || ciphertext || tag (16 bytes).
        key_id: Key version identifier. Default "v1".
        aad: Additional Authenticated Data. Must match encrypt_at_rest call.

    Returns:
        Plaintext bytes.

    Raises:
        DecryptionFailedError: If ciphertext invalid (tag mismatch / wrong key).
    """
    if not ciphertext_blob or len(ciphertext_blob) < NONCE_BYTES + TAG_BYTES:
        raise DecryptionFailedError(
            f"ciphertext_blob too short: {len(ciphertext_blob) if ciphertext_blob else 0} bytes "
            f"(min {NONCE_BYTES + TAG_BYTES})"
        )

    key = _get_active_key(key_id)
    nonce = ciphertext_blob[:NONCE_BYTES]
    ct_with_tag = ciphertext_blob[NONCE_BYTES:]
    cipher = AESGCM(key)
    try:
        plaintext = cipher.decrypt(nonce, ct_with_tag, aad or b"")
    except Exception as exc:  # cryptography raises generic Exception on tag mismatch
        raise DecryptionFailedError(str(exc)) from exc
    return plaintext


# ── Rotate ──────────────────────────────────────────────────
def rotate_key(
    ciphertext_blob: bytes,
    *,
    old_key_id: str,
    new_key_id: str,
    aad: bytes | None = None,
) -> bytes:
    """Re-encrypt ciphertext_blob with new_key_id.

    Args:
        ciphertext_blob: Encrypted with old_key_id.
        old_key_id: Source key version.
        new_key_id: Target key version.
        aad: AAD context bytes (must match original encryption).

    Returns:
        New ciphertext_blob encrypted with new_key_id.

    Raises:
        DecryptionFailedError: If old_key_id cannot decrypt.
    """
    plaintext = decrypt_at_rest(ciphertext_blob, key_id=old_key_id, aad=aad)
    return encrypt_at_rest(plaintext, key_id=new_key_id, aad=aad)


# ── Key generation helper ────────────────────────────────────
def generate_key_bytes() -> bytes:
    """Generate a new 256-bit AES key (for KMS upload or env-var setup).

    Returns:
        32 random bytes (256 bits).
    """
    return secrets.token_bytes(KEY_BYTES)


# ── Key bytes ↔ hex (env-var format) ──────────────────────────
def key_id_to_env_var(key_id: str) -> str:
    """Build env-var name for a key_id (COSTMGR_AT_REST_KEY_<KEY_ID>)."""
    safe_key_id = key_id.upper().replace("-", "_").replace(".", "_")
    return f"COSTMGR_AT_REST_KEY_{safe_key_id}"


def load_key_bytes_from_env(key_id: str = DEFAULT_KEY_ID) -> bytes | None:
    """Load key bytes from env-var. Returns None if env-var not set.

    Env-var format: COSTMGR_AT_REST_KEY_<KEY_ID> = hex (64 chars).
    Production: Use KMS-managed key retrieval instead.
    """
    env_var = key_id_to_env_var(key_id)
    hex_str = os.environ.get(env_var)
    if not hex_str:
        return None
    try:
        return bytes.fromhex(hex_str)
    except ValueError as exc:
        raise CryptoError(f"Invalid hex in env-var {env_var}: {exc}") from exc


__all__ = [
    "NONCE_BYTES",
    "KEY_BYTES",
    "TAG_BYTES",
    "DEFAULT_KEY_ID",
    "CryptoError",
    "DecryptionFailedError",
    "KeyNotFoundError",
    "encrypt_at_rest",
    "decrypt_at_rest",
    "rotate_key",
    "generate_key_bytes",
    "key_id_to_env_var",
    "load_key_bytes_from_env",
]
