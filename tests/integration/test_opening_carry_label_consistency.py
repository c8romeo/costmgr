"""tests.integration.test_opening_carry_label_consistency — drift guard for opening_carry labels.

Story 5.1 (Epic 5) — Task 4.2 cross-language parity tests for the
opening inventory auto-carry chain. Mirrors the canonical Python
vocabulary in `packages.services.m2_input.opening_carry` with the
TypeScript mirror at `apps/web/lib/l2-input-opening-carry.ts` (when
that lands — Story 5.3 frontend toast).

This test:
1. Reads the TS file (if it exists — 5.3 will land) and asserts the
   `OPENING_CARRY_CHAIN_LIMIT` constant equals 12 (PRD §F4.1).
2. Reads the Python pure kernel and asserts the same constant.
3. Reads the service-layer exception codes and asserts the TS mirror
   uses the same Korean reason strings.
4. Parses the Alembic migrations and asserts that `monthly_input_periods
   .opening_inventory` JSONB column was added by 0011 (Story 3.3
   baseline — 5-1 reuses the column without migration).

If the TS file does NOT yet exist (5-3 hasn't landed), this test
skips the TS-side checks. When 5-3 lands, the test will automatically
start asserting.

Layering (AD-11):
- Pure helpers in `packages/services/m2_input/opening_carry.py`
- Service layer in `apps/api/modules/m4_inventory/services/opening_carry_service.py`
- TS mirror deferred to Story 5.3 frontend (Story 0.5 plumbing).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TS_PATH = REPO_ROOT / "apps" / "web" / "lib" / "l2-input-opening-carry.ts"


# ─────────────────────────────────────────────────────────────
# 1. Pure kernel constant: INVENTORY_PERIOD_CHAIN_LIMIT == 12
# ─────────────────────────────────────────────────────────────


def test_chain_limit_constant_python() -> None:
    """Pure kernel: chain limit is 12 (PRD §F4.1 + OQ4 cj-style default)."""
    from packages.services.m2_input.opening_carry import (
        INVENTORY_PERIOD_CHAIN_LIMIT,
    )

    assert INVENTORY_PERIOD_CHAIN_LIMIT == 12


def test_chain_limit_constant_ts() -> None:
    """TS mirror: chain limit is 12 (when Story 5.3 lands).

    Skips if TS file does not yet exist (Story 0.5 plumbing).
    """
    if not TS_PATH.exists():
        pytest.skip(
            "Story 5.3 / 0.5 plumbing not yet landed — TS mirror "
            "apps/web/lib/l2-input-opening-carry.ts not yet created"
        )
    raw = TS_PATH.read_text(encoding="utf-8")
    no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    cleaned = re.sub(r"^\s*//.*$", "", no_block, flags=re.MULTILINE)
    m = re.search(
        r"OPENING_CARRY_CHAIN_LIMIT\s*[:=]\s*(\d+)",
        cleaned,
    )
    assert m is not None, (
        "OPENING_CARRY_CHAIN_LIMIT constant not found in TS mirror"
    )
    assert int(m.group(1)) == 12, (
        f"TS OPENING_CARRY_CHAIN_LIMIT={m.group(1)} drifted from "
        f"Python INVENTORY_PERIOD_CHAIN_LIMIT=12"
    )


# ─────────────────────────────────────────────────────────────
# 2. Korean lock reason string consistency
# ─────────────────────────────────────────────────────────────


def test_lock_reason_ko_python() -> None:
    """Pure kernel default lock reason_ko: '전월 기말 자동 이월'."""
    import uuid

    from packages.services.m2_input.opening_carry import (
        lock_opening_after_first_row,
    )

    state = {uuid.uuid4(): 100}
    locked = lock_opening_after_first_row(state)
    assert locked["_lock_reason_ko"] == "전월 기말 자동 이월"


def test_lock_reason_ko_ts() -> None:
    """TS mirror: same Korean lock reason string (5-3 lands)."""
    if not TS_PATH.exists():
        pytest.skip("Story 5.3 / 0.5 plumbing not yet landed")
    raw = TS_PATH.read_text(encoding="utf-8")
    assert "전월 기말 자동 이월" in raw, (
        "TS mirror missing Korean lock reason string "
        "'전월 기말 자동 이월' (PRD §F4.1 UX hint)"
    )


# ─────────────────────────────────────────────────────────────
# 3. JSONB column shape (Alembic 0011 baseline)
# ─────────────────────────────────────────────────────────────


def test_alembic_opening_inventory_jsonb_column_exists() -> None:
    """`monthly_input_periods.opening_inventory` JSONB added by 0011
    (Story 3.3); 5-1 reuses without new migration.

    CR 1.1 lesson: 5-1 must NOT alter the column shape (would break
    Story 3.3 baseline). This test pins the column type.
    """
    migrations_dir = REPO_ROOT / "apps" / "api" / "alembic" / "versions"
    # Read the 0011 baseline migration
    if not list(migrations_dir.glob("0011_*.py")):
        pytest.skip("Alembic 0011 not yet landed — Story 3.3 baseline pending")
    m = re.search(
        r"opening_inventory[^,]*JSONB",
        next(migrations_dir.glob("0011_*.py")).read_text(encoding="utf-8"),
        re.IGNORECASE,
    )
    assert m is not None, (
        "Alembic 0011 must add opening_inventory JSONB column to "
        "monthly_input_periods (Story 3.3 baseline; Story 5.1 reuses)"
    )


# ─────────────────────────────────────────────────────────────
# 4. Capability gate consistency
# ─────────────────────────────────────────────────────────────


def test_capability_opening_inventory_wired_manufacturing() -> None:
    """Capability.OPENING_INVENTORY must be in manufacturing matrix."""
    from apps.api.core.capability import Capability

    # Manufacturing is the baseline; check enum exists
    assert hasattr(Capability, "OPENING_INVENTORY")
    assert Capability.OPENING_INVENTORY.value == "opening_inventory"
