"""tests.integration.test_capability_matrix_v1_15_drift — Story 12.3 capability pin.

Pins v1.15 capability addition (1 NEW):
- ACCOUNT_DELETION  (POST /account/deletion/challenge-token +
                    POST /account/deletion/request +
                    POST /account/deletion/cancel +
                    GET  /account/deletion/status)

Industry matrix (per docs/capability-matrix.md v1.15):
- Manufacturing (3 variants) ✅ enabled
- Service-only ✅ enabled (industry-agnostic security baseline — CR 12-1 L4)

CR 12-1 L4 precedent: ACCOUNT_DELETION is documented as industry-agnostic
(not enforced in 3 of 4 routes — `require_role("owner")` per AD-10).
The `require_capability(ACCOUNT_DELETION)` gate is enforced ONLY on the
destructive /request route (CR 12-5 L3 3-layer TOTP defense target).
The "all 4 industries" pin here is for auditability — confirms the doc
matches the Capability enum for drift detection.

Also verifies the docs file itself documents the ACCOUNT_DELETION row
(drift detection between docs and Capability enum).

CR 11-3 lesson: capability drift across industry matrices is the #1
source of cross-tenant write leaks. Each capability addition needs a
4-industry pin + a docs-version pin + a table-row pin.
"""

from __future__ import annotations

import re
from pathlib import Path

from apps.api.core.capability import (
    Capability,
    industry_supports,
)
from packages.services.m0_onboarding.industry_menu import Industry

# ── 1 NEW capability per v1.15 ─────────────────────────────
_NEW_V1_15_CAPABILITIES: tuple[Capability, ...] = (
    Capability.ACCOUNT_DELETION,
)


def _load_capability_matrix_docs() -> str:
    """Read the capability matrix docs for drift detection."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "docs" / "capability-matrix.md"
    ).read_text(encoding="utf-8")


# ── 1. ACCOUNT_DELETION enum + 4-industry pin (industry-agnostic) ──
def test_capability_account_deletion_enum_exists() -> None:
    """`Capability.ACCOUNT_DELETION` enum value must exist (v1.15)."""
    assert hasattr(Capability, "ACCOUNT_DELETION")
    assert Capability.ACCOUNT_DELETION.value == "account_deletion"


def test_capability_account_deletion_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes ACCOUNT_DELETION (v1.15)."""
    assert industry_supports(Industry.MANUFACTURING, Capability.ACCOUNT_DELETION)


def test_capability_account_deletion_wired_service_only() -> None:
    """Service-only industry matrix INCLUDES ACCOUNT_DELETION (industry-agnostic).

    CR 12-1 L4 precedent: deletion is operational infrastructure, granted
    to all 4 industries including service-only. This mirrors BACKUP_EXPORT
    (12-2) and TWO_FACTOR_AUTH (12-1) industry-agnostic security baseline
    patterns.
    """
    assert industry_supports(Industry.SERVICE, Capability.ACCOUNT_DELETION)


def test_capability_account_deletion_wired_mfg_service() -> None:
    """mfg+service industry matrix includes ACCOUNT_DELETION (v1.15)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.ACCOUNT_DELETION
    )


def test_capability_account_deletion_wired_mixed() -> None:
    """Mixed industry matrix includes ACCOUNT_DELETION (v1.15)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.ACCOUNT_DELETION
    )


# ── 2. Docs-version pin (drift detector) ─────────────────────
def test_capability_matrix_docs_pin_v1_15() -> None:
    """docs/capability-matrix.md must declare v1.15 (Story 12.3 wire).

    Drift detector: if the docs version drifts from the Capability
    enum, this test fails so the team updates the docs in lockstep
    with the Capability enum.
    """
    docs = _load_capability_matrix_docs()
    # Title row must be v1.15.
    assert "# Capability Matrix (v1.15)" in docs, (
        "docs/capability-matrix.md title must be v1.15 (Story 12.3)"
    )
    # v1.15 history entry must reference Story 12.3 + the NEW capability.
    assert "v1.15" in docs
    assert "Story 12.3" in docs
    assert "ACCOUNT_DELETION" in docs


def test_capability_matrix_docs_table_has_account_deletion_row() -> None:
    """docs capability table must list the NEW v1.15 ACCOUNT_DELETION row.

    Drift detector: if the table row is missing, this test fails.
    """
    docs = _load_capability_matrix_docs()
    pattern = r"\|\s*`ACCOUNT_DELETION`\s*\|"
    assert re.search(pattern, docs), (
        "docs capability table missing row for ACCOUNT_DELETION"
    )


def test_capability_matrix_docs_account_deletion_all_industries_checkmarks() -> None:
    """The ACCOUNT_DELETION row must show ✅ for ALL 4 industries (industry-agnostic).

    Drift detector: pin the visible matrix layout. If a column is
    accidentally flipped, this test fails.
    """
    docs = _load_capability_matrix_docs()
    # Row pattern: | `ACCOUNT_DELETION` | <story> | ✅ | ✅ | ✅ | ✅ |
    # All 4 industries must show ✅ (industry-agnostic security baseline).
    pattern = (
        r"\|\s*`ACCOUNT_DELETION`\s*\|"
        r"[^\n]*✅[^\n]*✅[^\n]*✅[^\n]*✅[^\n]*\|"
    )
    assert re.search(pattern, docs), (
        "docs ACCOUNT_DELETION row must have ✅ ✅ ✅ ✅ columns "
        "(manufacturing / service / mfg+service / mfg+service+other — "
        "industry-agnostic per CR 12-1 L4)"
    )


# ── 3. Cross-pin: enum ↔ docs (drift detector) ────────────────
def test_capability_matrix_enum_count_matches_table_rows_v1_15() -> None:
    """Capability enum count must match the docs table row count.

    Drift detector: a discrepancy means either the enum has values
    not documented, or the docs has rows for removed values. Either
    way the team must reconcile.
    """
    docs = _load_capability_matrix_docs()
    table_rows = re.findall(
        r"^\|\s*`([A-Z_]+)`\s*\|",
        docs,
        re.MULTILINE,
    )
    enum_count = len(Capability)
    cap_names = {c.name for c in Capability}
    table_name_set = set(table_rows)
    assert len(table_rows) == enum_count, (
        f"drift: docs table has {len(table_rows)} rows, "
        f"Capability enum has {enum_count} values. "
        f"Missing from docs: {cap_names - table_name_set}. "
        f"Extra in docs: {table_name_set - cap_names}"
    )
