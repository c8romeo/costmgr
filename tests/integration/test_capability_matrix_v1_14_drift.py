"""tests.integration.test_capability_matrix_v1_14_drift — Story 12.2 capability pin.

Pins v1.14 capability addition (1 NEW):
- BACKUP_EXPORT  (GET /account/backups/recent + GET /backups/{id}/download
                  + POST /account/backups/trigger)

Industry matrix (per docs/capability-matrix.md v1.14):
- Manufacturing (3 variants) ✅ enabled
- Service-only ✅ enabled (industry-agnostic security baseline)

CR 12-1 L4 precedent: BACKUP_EXPORT is documented as industry-agnostic
(not enforced in any route — owner-only via AD-10 require_role). The
"all 4 industries" pin here is for auditability — confirms the doc
matches the Capability enum for drift detection.

Also verifies the docs file itself documents the BACKUP_EXPORT row
(drift detection between docs and Capability enum).

CR 11.3 lesson: capability drift across industry matrices is the #1
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

# ── 1 NEW capability per v1.14 ─────────────────────────────
_NEW_V1_14_CAPABILITIES: tuple[Capability, ...] = (
    Capability.BACKUP_EXPORT,
)


def _load_capability_matrix_docs() -> str:
    """Read the capability matrix docs for drift detection."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "docs" / "capability-matrix.md"
    ).read_text(encoding="utf-8")


# ── 1. BACKUP_EXPORT enum + 4-industry pin (industry-agnostic) ──
def test_capability_backup_export_enum_exists() -> None:
    """`Capability.BACKUP_EXPORT` enum value must exist (v1.14)."""
    assert hasattr(Capability, "BACKUP_EXPORT")
    assert Capability.BACKUP_EXPORT.value == "backup_export"


def test_capability_backup_export_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes BACKUP_EXPORT (v1.14)."""
    assert industry_supports(Industry.MANUFACTURING, Capability.BACKUP_EXPORT)


def test_capability_backup_export_wired_service_only() -> None:
    """Service-only industry matrix INCLUDES BACKUP_EXPORT (industry-agnostic).

    CR 12-1 L4 precedent: backup is operational infrastructure, granted
    to all 4 industries including service-only. This is the distinguishing
    feature of v1.14 vs v1.12 — service-only tenants also get backup.
    """
    assert industry_supports(Industry.SERVICE, Capability.BACKUP_EXPORT)


def test_capability_backup_export_wired_mfg_service() -> None:
    """mfg+service industry matrix includes BACKUP_EXPORT (v1.14)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.BACKUP_EXPORT
    )


def test_capability_backup_export_wired_mixed() -> None:
    """Mixed industry matrix includes BACKUP_EXPORT (v1.14)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.BACKUP_EXPORT
    )


# ── 2. Docs-version pin (drift detector) ─────────────────────
def test_capability_matrix_docs_pin_v1_14() -> None:
    """docs/capability-matrix.md must declare v1.14 (Story 12.2 wire).

    Drift detector: if the docs version drifts from the Capability
    enum, this test fails so the team updates the docs in lockstep
    with the Capability enum.

    Note: Story 12.3 wire bumps the docs to v1.15. The v1.14 history
    entry remains — this test only verifies the history entry is
    present (not the title which advances to v1.15).
    """
    docs = _load_capability_matrix_docs()
    # v1.14 history entry must reference Story 12.2 + the NEW capability.
    assert "v1.14" in docs
    assert "Story 12.2" in docs
    assert "BACKUP_EXPORT" in docs


def test_capability_matrix_docs_table_has_backup_export_row() -> None:
    """docs capability table must list the NEW v1.14 BACKUP_EXPORT row.

    Drift detector: if the table row is missing, this test fails.
    """
    docs = _load_capability_matrix_docs()
    pattern = r"\|\s*`BACKUP_EXPORT`\s*\|"
    assert re.search(pattern, docs), (
        "docs capability table missing row for BACKUP_EXPORT"
    )


def test_capability_matrix_docs_backup_export_all_industries_checkmarks() -> None:
    """The BACKUP_EXPORT row must show ✅ for ALL 4 industries (industry-agnostic).

    Drift detector: pin the visible matrix layout. If a column is
    accidentally flipped, this test fails.
    """
    docs = _load_capability_matrix_docs()
    # Row pattern: | `BACKUP_EXPORT` | <story> | ✅ | ✅ | ✅ | ✅ |
    # All 4 industries must show ✅ (industry-agnostic security baseline).
    pattern = (
        r"\|\s*`BACKUP_EXPORT`\s*\|"
        r"[^\n]*✅[^\n]*✅[^\n]*✅[^\n]*✅[^\n]*\|"
    )
    assert re.search(pattern, docs), (
        "docs BACKUP_EXPORT row must have ✅ ✅ ✅ ✅ columns "
        "(manufacturing / service / mfg+service / mfg+service+other — "
        "industry-agnostic per CR 12-1 L4)"
    )


# ── 3. Cross-pin: enum ↔ docs (drift detector) ────────────────
def test_capability_matrix_enum_count_matches_table_rows() -> None:
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
