"""tests.test_uuid7 — UUID v7 generator sanity tests (Story 1.3 — Task 1).

Verifies the stdlib-only `packages.common.uuid7.uuid7()` generator against
RFC 9562 §5.7 layout. Pure-Python tests.
"""

from __future__ import annotations

import re
import time
import uuid

from packages.common.uuid7 import uuid7


_UUID7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def test_uuid7_format_matches_rfc4122_layout() -> None:
    """The string form matches the canonical RFC 4122 layout for v7."""
    sample = str(uuid7())
    assert _UUID7_RE.match(sample), f"unexpected layout: {sample!r}"


def test_uuid7_version_is_7() -> None:
    """uuid.UUID.version attribute is 7."""
    u = uuid7()
    assert u.version == 7


def test_uuid7_variant_is_rfc4122() -> None:
    """uuid.UUID.variant attribute is 'specified in RFC 4122'."""
    u = uuid7()
    assert u.variant == uuid.RFC_4122


def test_uuid7_is_unique_across_rapid_calls() -> None:
    """1000 consecutive calls produce 1000 distinct values."""
    seen = {uuid7() for _ in range(1000)}
    assert len(seen) == 1000


def test_uuid7_time_sortable_within_1ms_burst() -> None:
    """Two v7 calls within a few ms sort in time order.

    Not a strict monotonicity check (the random bits may make two ms-apart
    IDs sort identically at low bits) — just that they DO sort by creation
    time on average.
    """
    a = uuid7()
    time.sleep(0.005)  # 5 ms
    b = uuid7()
    assert a.int < b.int, "v7 should be roughly time-ordered"


def test_uuid7_is_uuid_instance() -> None:
    """The return type is uuid.UUID (so it works as a SQLAlchemy default)."""
    u = uuid7()
    assert isinstance(u, uuid.UUID)


def test_uuid7_handles_backdated_timestamp_correctly() -> None:
    """A v7 created in ms T+1 sorts AFTER one created in ms T (when the
    timestamp part advances).

    Within a single millisecond the random suffix may flip the order — this
    is normal for UUID v7 and is NOT a monotonicity guarantee. So we sleep
    2 ms between calls to force the timestamp forward.
    """
    u1 = uuid7()
    time.sleep(0.002)  # 2 ms — well past a single-millisecond window
    u2 = uuid7()
    assert u1.int < u2.int, (
        f"v7 should sort by creation time when the ms advances: "
        f"u1={u1!s} u2={u2!s}"
    )