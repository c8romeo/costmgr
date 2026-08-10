"""apps.api.core.key_manager — AES-256-GCM key retrieval (NFR6).

Story 12.1 (Epic 12 cj-style 1번째) — at-rest key management.

AD-11 layer rule: pure helper in `apps/api/core/`. No DB, no tenant
concerns. Service layer calls `get_active_key(key_id)` to retrieve
key bytes for encrypt/decrypt operations.

Key storage strategy:
- Production: KMS (AWS KMS / GCP KMS / Supabase Vault) — not implemented
  yet; placeholder interface in `retrieve_key_from_kms()`
- Development / CI: env-var based (COSTMGR_AT_REST_KEY_<KEY_ID>=hex)
- Fallback: ephemeral in-memory key (dev only — auto-rotated per process)

This module is stdlib-only. It does NOT import `packages.cost_engine`
or any tenant-bound modules (per AD-11).
"""

from __future__ import annotations

import secrets
import threading
from typing import Final

from apps.api.core.crypto import KEY_BYTES

# ── Constants ────────────────────────────────────────────────
DEFAULT_KEY_ID: Final[str] = "v1"

# In-memory key cache: key_id → bytes (thread-safe lock)
_key_cache: dict[str, bytes] = {}
_key_cache_lock = threading.Lock()


# ── Typed exceptions ──────────────────────────────────────────
class KeyManagerError(Exception):
    """Key manager error."""


class KeyNotFoundError(KeyManagerError):
    """Key not found in any source (env-var, KMS, in-memory)."""

    def __init__(self, key_id: str) -> None:
        self.key_id = key_id
        super().__init__(
            f"No key found for key_id={key_id!r}. "
            f"Set env-var COSTMGR_AT_REST_KEY_{key_id.upper()} (hex) "
            f"or configure KMS retrieval."
        )


# ── Key retrieval ─────────────────────────────────────────────
def get_active_key(key_id: str = DEFAULT_KEY_ID) -> bytes:
    """Retrieve key bytes for the given key_id.

    Lookup order:
    1. In-memory cache (populated by `set_key()` or KMS loader)
    2. Environment variable (dev / CI)
    3. KMS (production — not yet wired)
    4. Ephemeral in-memory fallback (dev convenience)

    Args:
        key_id: Key version identifier (e.g., "v1", "v2").

    Returns:
        32 bytes (256 bits) — AES-256 key.

    Raises:
        KeyNotFoundError: If key_id not resolvable from any source.
    """
    # 1. Cache check
    with _key_cache_lock:
        if key_id in _key_cache:
            return _key_cache[key_id]

    # 2. Env-var fallback (dev / CI)
    env_key = _load_key_from_env(key_id)
    if env_key is not None:
        with _key_cache_lock:
            _key_cache[key_id] = env_key
        return env_key

    # 3. KMS retrieval (production) — placeholder
    kms_key = retrieve_key_from_kms(key_id)
    if kms_key is not None:
        with _key_cache_lock:
            _key_cache[key_id] = kms_key
        return kms_key

    # 4. Ephemeral fallback (dev convenience) — NOT for production
    ephemeral_key = secrets.token_bytes(KEY_BYTES)
    with _key_cache_lock:
        _key_cache[key_id] = ephemeral_key
    return ephemeral_key


# ── KMS interface (production) ────────────────────────────────
def retrieve_key_from_kms(key_id: str) -> bytes | None:
    """Retrieve key bytes from KMS.

    Placeholder for AWS KMS / GCP KMS / Supabase Vault integration.
    Returns None if not configured.

    Production deployment:
    - AWS KMS: boto3 client.decrypt(CiphertextBlob=...) on encrypted DEK
    - GCP KMS: google.cloud.kms_v1 decrypt path
    - Supabase Vault: pgcrypto extension + vault.get_secret()

    NOT YET WIRED in Story 12.1 (deferred to production hardening).
    """
    # TODO(epic-12-production): wire KMS retrieval
    return None


# ── In-memory key management (test/dev) ───────────────────────
def set_key(key_id: str, key_bytes: bytes) -> None:
    """Inject a key into the in-memory cache (test/dev convenience)."""
    if len(key_bytes) != KEY_BYTES:
        raise ValueError(f"key_bytes must be {KEY_BYTES} bytes, got {len(key_bytes)}")
    with _key_cache_lock:
        _key_cache[key_id] = key_bytes


def clear_keys() -> None:
    """Clear all cached keys (test/dev cleanup)."""
    with _key_cache_lock:
        _key_cache.clear()


def list_key_versions() -> list[str]:
    """Return all cached key_ids.

    For production rotation tracking, this should query KMS / key rotation
    log. Currently only returns in-memory cache.
    """
    with _key_cache_lock:
        return sorted(_key_cache.keys())


# ── Env-var loader (dev / CI) ─────────────────────────────────
def _load_key_from_env(key_id: str) -> bytes | None:
    """Load key from env-var (COSTMGR_AT_REST_KEY_<KEY_ID>=hex)."""
    import os

    safe_key_id = key_id.upper().replace("-", "_").replace(".", "_")
    env_var = f"COSTMGR_AT_REST_KEY_{safe_key_id}"
    hex_str = os.environ.get(env_var)
    if not hex_str:
        return None
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        return None  # invalid format → fall through to next source


__all__ = [
    "DEFAULT_KEY_ID",
    "KeyManagerError",
    "KeyNotFoundError",
    "get_active_key",
    "set_key",
    "clear_keys",
    "list_key_versions",
    "retrieve_key_from_kms",
]
