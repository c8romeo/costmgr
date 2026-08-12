"""tests.integration.test_capability_matrix_v1_12_drift — Story 11.3 capability pin.

Pins v1.12 capability additions (3 NEW) across the industry matrix:
- SNAPSHOT_PERSISTENCE  (POST /close/snapshots/commit + GET /close/snapshots/{period_key})
- REVERSAL_EXECUTE      (POST /close/snapshots/reverse)
- REOPEN_OPERATOR       (POST /close/sequence/reopen)

Industry matrix (per docs/capability-matrix.md v1.12):
- Manufacturing (3 variants) ✅ enabled for all 3 NEW capabilities
- Service-only ❌ disabled for all 3 NEW capabilities

Also verifies the docs file itself documents all 3 NEW rows
(drift detection between docs and Capability enum).

CR 1.1 lesson: capability drift across industry matrices is the #1
source of cross-tenant write leaks. Each capability addition needs a
3-matrix pin + a service-only exclusion pin + a docs-version pin.
"""

from __future__ import annotations

import re
from pathlib import Path

from apps.api.core.capability import (
    Capability,
    industry_supports,
)
from packages.services.m0_onboarding.industry_menu import Industry


# ── 3 NEW capabilities per v1.12 ─────────────────────────────
_NEW_V1_12_CAPABILITIES: tuple[Capability, ...] = (
    Capability.SNAPSHOT_PERSISTENCE,
    Capability.REVERSAL_EXECUTE,
    Capability.REOPEN_OPERATOR,
)


def _load_capability_matrix_docs() -> str:
    """Read the capability matrix docs for drift detection."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "docs" / "capability-matrix.md"
    ).read_text(encoding="utf-8")


# ── 1. SNAPSHOT_PERSISTENCE enum + 3-industry pin ─────────────
def test_capability_snapshot_persistence_enum_exists() -> None:
    """`Capability.SNAPSHOT_PERSISTENCE` enum value must exist (v1.12)."""
    assert hasattr(Capability, "SNAPSHOT_PERSISTENCE")
    assert Capability.SNAPSHOT_PERSISTENCE.value == "snapshot_persistence"


def test_capability_snapshot_persistence_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes SNAPSHOT_PERSISTENCE."""
    assert industry_supports(
        Industry.MANUFACTURING, Capability.SNAPSHOT_PERSISTENCE
    )


def test_capability_snapshot_persistence_wired_mfg_service() -> None:
    """mfg+service industry matrix includes SNAPSHOT_PERSISTENCE."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.SNAPSHOT_PERSISTENCE
    )


def test_capability_snapshot_persistence_wired_mixed() -> None:
    """Mixed industry matrix includes SNAPSHOT_PERSISTENCE."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.SNAPSHOT_PERSISTENCE
    )


def test_capability_snapshot_persistence_excluded_service_only() -> None:
    """Service-only industry does NOT have SNAPSHOT_PERSISTENCE.

    Service tenants have no fiscal_period_snapshots → the snapshot
    commit endpoint returns 403 INDUSTRY_NOT_SUPPORTED.
    """
    assert not industry_supports(
        Industry.SERVICE, Capability.SNAPSHOT_PERSISTENCE
    )


# ── 2. REVERSAL_EXECUTE enum + 3-industry pin ─────────────────
def test_capability_reversal_execute_enum_exists() -> None:
    """`Capability.REVERSAL_EXECUTE` enum value must exist (v1.12).

    Distinct from REVERSAL_REQUEST (v1.10) which gates the AD-22
    reversal REQUEST 11-1 wire. This gates the EXECUTE step (11-3
    AD-22 reversal 영구화 + 3-tier guard).
    """
    assert hasattr(Capability, "REVERSAL_EXECUTE")
    assert Capability.REVERSAL_EXECUTE.value == "reversal_execute"


def test_capability_reversal_execute_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes REVERSAL_EXECUTE."""
    assert industry_supports(
        Industry.MANUFACTURING, Capability.REVERSAL_EXECUTE
    )


def test_capability_reversal_execute_wired_mfg_service() -> None:
    """mfg+service industry matrix includes REVERSAL_EXECUTE."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.REVERSAL_EXECUTE
    )


def test_capability_reversal_execute_wired_mixed() -> None:
    """Mixed industry matrix includes REVERSAL_EXECUTE."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.REVERSAL_EXECUTE
    )


def test_capability_reversal_execute_excluded_service_only() -> None:
    """Service-only industry does NOT have REVERSAL_EXECUTE."""
    assert not industry_supports(
        Industry.SERVICE, Capability.REVERSAL_EXECUTE
    )


# ── 3. REOPEN_OPERATOR enum + 3-industry pin ─────────────────
def test_capability_reopen_operator_enum_exists() -> None:
    """`Capability.REOPEN_OPERATOR` enum value must exist (v1.12).

    W2 reopen flow — owner-only operator reopen with `operator_action`
    4-value enum + `reason` length 20-500. AD-10 owner-only is enforced
    separately at require_role layer; this capability gate is the
    industry-aware front.
    """
    assert hasattr(Capability, "REOPEN_OPERATOR")
    assert Capability.REOPEN_OPERATOR.value == "reopen_operator"


def test_capability_reopen_operator_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes REOPEN_OPERATOR."""
    assert industry_supports(Industry.MANUFACTURING, Capability.REOPEN_OPERATOR)


def test_capability_reopen_operator_wired_mfg_service() -> None:
    """mfg+service industry matrix includes REOPEN_OPERATOR."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.REOPEN_OPERATOR
    )


def test_capability_reopen_operator_wired_mixed() -> None:
    """Mixed industry matrix includes REOPEN_OPERATOR."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.REOPEN_OPERATOR
    )


def test_capability_reopen_operator_excluded_service_only() -> None:
    """Service-only industry does NOT have REOPEN_OPERATOR.

    Service tenants do NOT have fiscal_periods to reopen (no inventory
    ledger → no close sequence → no reopen path).
    """
    assert not industry_supports(Industry.SERVICE, Capability.REOPEN_OPERATOR)


# ── 4. Docs-version pin (drift detector) ─────────────────────
def test_capability_matrix_docs_pin_v1_12() -> None:
    """docs/capability-matrix.md must declare v1.12 changelog (Story 11.3 wire).

    Drift detector: if the docs version drifts from the Capability
    enum, this test fails so the team updates the docs in lockstep
    with the Capability enum.

    Note: the title row reflects the LATEST version (currently v1.14
    after Story 12.2 wire). This test pins the v1.12 CHANGELOG ENTRY
    specifically — not the title — so it survives version bumps.
    """
    docs = _load_capability_matrix_docs()
    # v1.12 changelog entry must reference Story 11.3 + the 3 NEW
    # capability names.
    assert "v1.12" in docs
    assert "Story 11.3" in docs
    for cap_name in (
        "SNAPSHOT_PERSISTENCE",
        "REVERSAL_EXECUTE",
        "REOPEN_OPERATOR",
    ):
        assert cap_name in docs, f"docs missing capability {cap_name!r}"


def test_capability_matrix_docs_table_has_3_new_rows() -> None:
    """docs capability table must list all 3 NEW v1.12 rows.

    Parses the markdown capability table rows for the 3 NEW entries.
    Drift detector: if a row is missing from the table, this test fails.
    """
    docs = _load_capability_matrix_docs()
    # Find each row by its capability name in the table.
    for cap_name in (
        "SNAPSHOT_PERSISTENCE",
        "REVERSAL_EXECUTE",
        "REOPEN_OPERATOR",
    ):
        # Match "| `CAP_NAME` | ..." with the row marker pattern.
        pattern = rf"\|\s*`{re.escape(cap_name)}`\s*\|"
        assert re.search(pattern, docs), (
            f"docs capability table missing row for {cap_name!r}"
        )


def test_capability_matrix_docs_industry_column_has_checkmarks() -> None:
    """The 3 NEW rows must show ✅ for manufacturing-kind and ❌ for service.

    Drift detector: pin the visible matrix layout. If a column is
    accidentally flipped (e.g., service-only granted), this test fails.
    """
    docs = _load_capability_matrix_docs()
    # Extract the table rows for the 3 NEW capabilities. Each row is
    # "| `CAP_NAME` | ... | manufacturing | service | mfg_service | mixed |"
    # We use a regex to capture the column pattern after the cap name.
    for cap_name in (
        "SNAPSHOT_PERSISTENCE",
        "REVERSAL_EXECUTE",
        "REOPEN_OPERATOR",
    ):
        # Find row: | `CAP` | <story> | ✅ | ❌ | ✅ | ✅ |
        pattern = rf"\|\s*`{re.escape(cap_name)}`\s*\|[^\n]*✅[^\n]*❌[^\n]*✅[^\n]*✅[^\n]*\|"
        assert re.search(pattern, docs), (
            f"docs row for {cap_name!r} must have ✅ ❌ ✅ ✅ columns "
            "(manufacturing / service / mfg+service / mfg+service+other)"
        )


# ── 5. Cross-pin: enum ↔ docs (drift detector) ────────────────
def test_capability_matrix_enum_count_matches_table_rows() -> None:
    """Capability enum count must match the docs table row count.

    Drift detector: a discrepancy means either the enum has values
    not documented, or the docs has rows for removed values. Either
    way the team must reconcile.
    """
    docs = _load_capability_matrix_docs()
    # Count the capability table rows: each row starts with "| `NAME` |"
    # and is in the Capabilities section.
    table_rows = re.findall(
        r"^\|\s*`([A-Z_]+)`\s*\|",
        docs,
        re.MULTILINE,
    )
    # The Capability enum has all rows in the table.
    enum_count = len(Capability)
    assert len(table_rows) == enum_count, (
        f"drift: docs table has {len(table_rows)} rows, "
        f"Capability enum has {enum_count} values. "
        f"Missing from docs: {set(c.name for c in Capability) - set(table_rows)}. "
        f"Extra in docs: {set(table_rows) - set(c.name for c in Capability)}"
    )