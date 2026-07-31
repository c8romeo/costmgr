"""packages.common.uuid7 — stdlib-only UUID v7 generator (Story 1.3 — Task 1).

Implements RFC 9562 UUID v7 (time-ordered, sortable, 128-bit) using only
the Python standard library. Used as the default value for business
entity IDs (`document_id`, `draft_id`) per AD-15 + the new
`AD-7-ai-extraction-table-naming.md`.

Why v7 (not v4):
- Time-ordered: better B-tree locality on inserts at high write volume.
- Sortable by creation time without exposing the timestamp.
- Same 128-bit width as v4; no schema migration needed for existing v4
  columns. Existing tenants/users rows stay v4; new business rows are v7.

Why not the `uuid6` / `uuid_extensions` package:
- We keep the dep tree minimal (AD-8 — money/types cross-language parity).
- This is ~30 lines of stdlib. Adding a third-party dep for one function
  adds a security review surface for no functional gain.

Layout (RFC 9562 §5.7):
  bits  0..47 : unix_ts_ms (48 bits, big-endian)
  bits 48..51 : version (0b0111 = 7)
  bits 52..63 : rand_a (12 bits)
  bits 64..65 : variant (0b10)
  bits 66..127: rand_b (62 bits)
"""

from __future__ import annotations

import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Generate a UUID v7 (time-ordered) using stdlib only.

    Returns:
        A `uuid.UUID` instance with `version == 7` and `variant == RFC 4122`.

    Example:
        >>> u = uuid7()
        >>> u.version
        7
        >>> u.variant
        'specified in RFC 4122'
    """
    # 48-bit unix timestamp in milliseconds — sortable across processes.
    unix_ts_ms = time.time_ns() // 1_000_000
    # 80 bits of randomness. `os.urandom(10)` is 80 bits; we use it twice
    # so the version + variant nibbles can be OR'd in between.
    rand = int.from_bytes(os.urandom(10), "big")  # 80 bits
    rand_a = rand >> 64  # top 16 bits → take 12 (low 4 are version)
    rand_b = rand & ((1 << 64) - 1)  # bottom 64 bits → take 62 (top 2 are variant)

    # Assemble per RFC 9562 §5.7:
    #   field        bits   position
    #   unix_ts_ms    48     [0..47]
    #   ver            4     [48..51]
    #   rand_a        12     [52..63]
    #   variant        2     [64..65]
    #   rand_b        62     [66..127]
    value = (unix_ts_ms & ((1 << 48) - 1)) << 80
    value |= (0x7 << 76)  # version 7 at bits 76..79 of the 128-bit int
    value |= (rand_a & ((1 << 12) - 1)) << 64
    value |= (0b10 << 62)  # RFC 4122 variant at bits 62..63
    value |= rand_b & ((1 << 62) - 1)
    return uuid.UUID(int=value)
