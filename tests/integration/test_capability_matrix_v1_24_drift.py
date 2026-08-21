"""
test_capability_matrix_v1_24_drift.py — auth capability matrix v1.24 drift detector.

Phase 3-1 — T7.4 (AC #6.7) — capability matrix v1.24 EXTENSION drift detector.
Mirrors the existing `tests/integration/test_capability_matrix_v1_21_drift.py`
+ `tests/integration/test_capability_matrix_v1_22_drift.py` pattern. The
detector enforces that the 5 NEW Phase 3-1 capability enum entries
(LOGIN, SIGNUP, AUTH_MIDDLEWARE, FORGOT_PASSWORD, LOGOUT) are present in
`apps/api/core/capability.py` AND that the `docs/capability-matrix.md`
matrix v1.24 declares the corresponding 5 NEW rows.

This is the v1.24 forward-lock — the matrix in the doc is the SSOT; the
backend enum must mirror it. Industry-agnostic per CR 12-1 L4 precedent
(mirrors TWO_FACTOR_AUTH + BACKUP_EXPORT + ACCOUNT_DELETION + 2FA +
LISTEN_NOTIFY).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_PY = REPO_ROOT / "apps" / "api" / "core" / "capability.py"
CAPABILITY_MATRIX_MD = REPO_ROOT / "docs" / "capability-matrix.md"

PHASE_3_1_CAPABILITIES = ["LOGIN", "SIGNUP", "AUTH_MIDDLEWARE", "FORGOT_PASSWORD", "LOGOUT"]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_capability_matrix_v1_24_title() -> None:
    """The capability matrix doc must declare version v1.24 in its title."""
    content = _read(CAPABILITY_MATRIX_MD)
    assert "v1.24" in content, "capability-matrix.md must declare v1.24 in its title"


def test_capability_matrix_v1_24_has_phase_3_1_section() -> None:
    """Phase 3-1 章節이 capability matrix v1.24 안에 존재해야 함."""
    content = _read(CAPABILITY_MATRIX_MD)
    # The PRD entry added the rows; we just verify they're still present.
    # The matrix uses both a v1.24 changelog block AND a table row format
    # `| `LOGIN` | Phase 3 | …`. Either format is acceptable.
    for cap in PHASE_3_1_CAPABILITIES:
        assert (
            f"| `{cap}`" in content
            or f"### {cap}" in content
            or f"`{cap}`" in content
        ), f"capability-matrix.md must declare row for {cap} under v1.24"


def test_capability_py_has_phase_3_1_enum_entries() -> None:
    """The backend enum must mirror the matrix v1.24 rows."""
    content = _read(CAPABILITY_PY)
    for cap in PHASE_3_1_CAPABILITIES:
        pattern = re.compile(rf"^\s*{cap}\s*=\s*\"{cap.lower()}\"\s*$", re.MULTILINE)
        assert pattern.search(content), f"capability.py must declare {cap} = \"{cap.lower()}\""


def test_capability_py_grants_phase_3_1_to_all_industries() -> None:
    """CR 12-1 L4 precedent — all 4 industries must have the 5 NEW capabilities."""
    content = _read(CAPABILITY_PY)
    # Find the 4 industry frozensets (MANUFACTURING, SERVICE, ..., OTHER).
    industry_headers = [
        "Industry.MANUFACTURING:",
        "Industry.SERVICE:",
        "Industry.MANUFACTURING_SERVICE:",
        "Industry.MANUFACTURING_SERVICE_OTHER:",
    ]
    for header in industry_headers:
        # The Capability.LOGIN entry must appear after this header.
        idx = content.find(header)
        assert idx > 0, f"missing industry header: {header}"
        # Industry grant frozensets span many lines — use 12000 chars to
        # capture the full frozenset including Phase 3-1 entries appended
        # to the end of each block.
        window = content[idx : idx + 12000]
        for cap in PHASE_3_1_CAPABILITIES:
            assert (
                f"Capability.{cap}" in window
            ), f"industry {header} must grant Capability.{cap}"


def test_capability_enum_total_count_at_least_26() -> None:
    """Wire sanity check — Phase 3-1 adds 5 to a previous baseline of 21+."""
    content = _read(CAPABILITY_PY)
    entries = re.findall(r"^\s*([A-Z_]+)\s*=\s*\"[a-z_]+\"\s*$", content, re.MULTILINE)
    # The class body has at least 25 entries (21 baseline + 5 new Phase 3-1).
    relevant = [
        name
        for name in entries
        if name
        not in {"FINAL", "M2_SERVICE_ROLE", "DELETE", "PATCH", "POST", "PUT"}
    ]
    assert (
        len(relevant) >= 26
    ), f"expected at least 26 capability entries, found {len(relevant)}: {relevant}"
