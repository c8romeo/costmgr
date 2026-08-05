"""packages.services.m1_baseline.product_code — pure code generation (Story 2.1).

Pure-Python, stdlib-only module (AD-1 / AD-5). NO DB, NO clock, NO random.

The DB-level max-sequence query lives in `ProductService`. This module
holds the **pure** transformation: given the current per-tenant per-type
sequence numbers, compute the next code, parse a code back, or validate
its format.

Why this is a separate module (not inlined in ProductService):
- Tests can exercise every edge case (overflow, invalid prefix, zero pad)
  without a DB fixture (CR 1.1 lesson: pure-logic bugs use `xfail` cleanly).
- The TS mirror in `apps/web/lib/menu-config.ts` for the prefix map is
  trivial; the formatter / parser is the only place where string slicing
  and int parsing happen, so drift is bounded to one file per language.

Code format: `<PREFIX>-<SEQ>` where:
- PREFIX is one of `PRD | SEM | MAT | GDS | SVC` (3 uppercase ASCII).
- SEQ is `\\d{4,}` (4+ digit zero-padded; 10000+ is allowed but not clamped).
"""

from __future__ import annotations

import re

from packages.services.m1_baseline.schemas import (
    ProductType,
    prefix_to_type,
    type_to_prefix,
)

# ── Validation regex ──────────────────────────────────────────
# PREFIX-[0-9]{4,} — 4+ digits, no upper bound (clamping is a business
# decision deferred; see Story 2.3 territory).
# M12: explicit `[0-9]` instead of `\d` so Unicode decimal digits
# (Arabic-Indic, full-width, etc.) are rejected. The spec mandates ASCII.
_CODE_RE: re.Pattern[str] = re.compile(r"^([A-Z]{3})-([0-9]{4,})$")


# ── Error type ────────────────────────────────────────────────
class InvalidProductCodeError(ValueError):
    """Raised when a code string is malformed (unknown prefix, bad format).

    Mapped to HTTP 422 at the handler boundary (AD-15 §4 error contract).
    """

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(f"invalid product code {code!r}: {reason}")
        self.code = code
        self.reason = reason


# ── Public API ────────────────────────────────────────────────
def generate_next_code(
    tenant_code_sequences: dict[ProductType, int],
    product_type: ProductType,
) -> str:
    """Return the next code (e.g. `MAT-0042`) for a (tenant, type) pair.

    Pure function: does NOT mutate the input dict. The caller is responsible
    for committing the new sequence number to the DB afterwards
    (`ProductService._next_sequence()` handles this).

    Args:
        tenant_code_sequences: Per-type current max sequence for this
            tenant. Missing keys are treated as `0` (start at 0001).
        product_type: The type of product being created.

    Returns:
        A string `PREFIX-XXXX` where XXXX is the next 4-digit zero-padded
        sequence number. Overflow beyond 9999 → 5+ digit number (no clamp).

    Examples:
        >>> generate_next_code({}, ProductType.MATERIAL)
        'MAT-0001'
        >>> generate_next_code({ProductType.MATERIAL: 5}, ProductType.MATERIAL)
        'MAT-0006'
        >>> generate_next_code({ProductType.MATERIAL: 9999}, ProductType.MATERIAL)
        'MAT-10000'
    """
    current = int(tenant_code_sequences.get(product_type, 0))
    next_seq = current + 1
    return _format_code(product_type, next_seq)


def parse_code(code: str) -> tuple[ProductType, int]:
    """Reverse of `generate_next_code`: `MAT-0042` → (`ProductType.MATERIAL`, 42).

    Returns:
        Tuple of (product_type, sequence). Sequence is the int (NOT the
        formatted string — call sites that need display should re-format
        via `_format_code`).

    Raises:
        InvalidProductCodeError: When `code` doesn't match `<PREFIX>-<SEQ>`
            or the prefix is unknown. CR 1.1 lesson: typed errors only —
            do NOT leak `ValueError` / `KeyError` to callers. M11: also
            wraps `int(raw_seq)` failures as `InvalidProductCodeError`
            (out-of-range numeric suffix, etc.).
    """
    if not isinstance(code, str) or not code:
        raise InvalidProductCodeError(repr(code), "code must be a non-empty string")

    m = _CODE_RE.match(code)
    if not m:
        raise InvalidProductCodeError(code, "must match `<PREFIX>-<SEQ>` (e.g. MAT-0042)")

    prefix, raw_seq = m.group(1), m.group(2)
    try:
        product_type = prefix_to_type(prefix)
    except KeyError as err:
        raise InvalidProductCodeError(code, f"unknown prefix {prefix!r}") from err

    # M11: int() conversion can raise ValueError for out-of-range suffixes
    # (e.g. extremely long digit sequences). Wrap as typed exception.
    try:
        seq = int(raw_seq)
    except ValueError as err:
        raise InvalidProductCodeError(code, f"invalid numeric suffix {raw_seq!r}") from err

    return product_type, seq


def is_valid_code_format(code: str) -> bool:
    """Format check only — returns True/False without raising.

    For input validation in the handler / form where we want a soft check
    before the structured exception path. The handler maps invalid
    `code` strings to HTTP 422 via the InvalidProductCodeError path;
    this helper exists for the synchronous form layer.
    """
    if not isinstance(code, str) or not code:
        return False
    m = _CODE_RE.match(code)
    if not m:
        return False
    try:
        prefix_to_type(m.group(1))
    except KeyError:
        return False
    return True


# ── Internal ──────────────────────────────────────────────────
def _format_code(product_type: ProductType, sequence: int) -> str:
    """Format a (type, seq) tuple as `<PREFIX>-<SEQ>`.

    Zero-pad to 4 digits minimum. Numbers >= 10000 fall through to Python
    default int formatting (5+ digits). Negative sequences are impossible
    (caller computes `current + 1` where current >= 0), but we guard
    defensively.
    """
    if sequence < 0:
        raise ValueError(f"sequence must be non-negative, got {sequence}")
    prefix = type_to_prefix(product_type)
    return f"{prefix}-{sequence:04d}"
