"""A18 audit_action 3-way extension drift detector.

Epic 11 close-out retro §7 A18 결정 — "A5 audit_action drift detector
3-way extension (11-1/11-2/11-3 4 ActionClass × 15 values fill) +
MONTHLY_INPUT_PERIOD extension (11-1 `opening_inventory_unlocked`).

This file EXTENDS the existing 3-way drift detector
(`tests/integration/test_audit_action_consistency.py`) with 17 NEW
test cases for the 4 ActionClass inventory:

| ActionClass | Values | Source |
|---|---|---|
| REVERSAL_LOG | 5 | audit_action.py:204-210 (Story 11.1) |
| MONTHLY_CLOSING | 4 | audit_action.py:265-270 (Story 11.2) |
| SNAPSHOT_PERSISTENCE | 4 | audit_action.py:297-302 (Story 11.3) |
| REOPEN_OPERATOR | 2 | audit_action.py:311-314 (Story 11.3) |

Plus:
- 1 MONTHLY_INPUT_PERIOD.opening_unlocked case (11-1 sweep missed)
- 1 service-layer scan EXTENSION (3 NEW service files
  scan for `action_class=ActionClass.X` presence — both
  `emit_audit_typed()` and `_ActionRegistry.validate()` patterns
  count as A5 forward-lock-compliant)

DB CHECK parity for these 4 ActionClass:
- REVERSAL_LOG routes to `reversal_log` table which has NO
  `action` CHECK constraint per alembic 0019 comment
  ("AD-22 reversal_log info only (NO action CHECK)").
- MONTHLY_CLOSING, SNAPSHOT_PERSISTENCE, REOPEN_OPERATOR all
  route to `audit_logs` which has NO action CHECK constraint per
  AD-2 invariant + conventions.md §10.1.

So 3-way extension = registry ↔ call sites (2-way effective,
explicit DB-N/A documented in test docstrings).

Per AD-15 cross-language parity: Python pure kernel ↔ TS mirror.
Per CR 1.1 zero-drift enforcement: if any test fails, the
contributor MUST update registry (audit_action.py) AND call sites
in lockstep.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalize_ws(src: str) -> str:
    """Collapse whitespace for multi-line-call detection."""
    return re.sub(r"\s+", " ", src)


def _find_action_class_call_sites(src: str, action_class_name: str) -> list[str]:
    """Find all `action_class=ActionClass.X, action=<value>` patterns.

    Catches BOTH forms:
    - `_ActionRegistry.validate(..., action_class=ActionClass.X, action=...)`
    - `emit_audit_typed(..., action_class=ActionClass.X, action=...)`

    Returns the list of `action=` values (variable names or quoted
    string literals, e.g. `"m11_reversal_handler_invoked"`).

    Whitespace normalization is applied first so multi-line calls
    collapse into a single line for regex matching.
    """
    normalized = _normalize_ws(src)
    pattern = re.compile(
        rf"action_class=ActionClass\.{action_class_name}\s*,\s*action="
        rf"(?:\"(\w+)\"|(\w+))"
    )
    results: list[str] = []
    for m in pattern.finditer(normalized):
        # Use whichever capture group matched.
        results.append(m.group(1) or m.group(2))
    return results


# ─────────────────────────────────────────────────────────────
# 1. REVERSAL_LOG — 5 values (Story 11.1 wire)
# ─────────────────────────────────────────────────────────────


_REVERSAL_LOG_VALUES = (
    "reversal_negating_inserted",
    "reversal_corrected_inserted",
    "reversal_rejected",
    "reversal_unauthorized",
    "m11_reversal_handler_invoked",
)


@pytest.mark.engine
def test_reversal_log_registry_present() -> None:
    """A18 3-way (1/17): ActionClass.REVERSAL_LOG is in _ActionRegistry."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    assert ActionClass.REVERSAL_LOG in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.REVERSAL_LOG]
    assert log_type == "reversal_log"
    assert accepted == frozenset(_REVERSAL_LOG_VALUES)


@pytest.mark.engine
@pytest.mark.parametrize("action_value", list(_REVERSAL_LOG_VALUES))
def test_reversal_log_validate_succeeds(action_value: str) -> None:
    """A18 3-way (2/17): each REVERSAL_LOG literal validates via registry."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    result = _ActionRegistry.validate(
        action_class=ActionClass.REVERSAL_LOG, action=action_value
    )
    assert result == "reversal_log"


@pytest.mark.engine
def test_reversal_log_call_sites_use_registry() -> None:
    """A18 3-way (3/17): reversal_service.py uses action_class=ActionClass.REVERSAL_LOG.

    Scans `apps/api/modules/m11_close/services/reversal_service.py` for
    `action_class=ActionClass.REVERSAL_LOG` presence — required for A5
    forward-lock. Catches BOTH `_ActionRegistry.validate(...)` and
    `emit_audit_typed(...)` patterns.
    """
    reversal_service = (
        ROOT
        / "apps"
        / "api"
        / "modules"
        / "m11_close"
        / "services"
        / "reversal_service.py"
    )
    if not reversal_service.exists():
        pytest.skip("reversal_service.py not found")

    matches = _find_action_class_call_sites(
        _read(reversal_service), "REVERSAL_LOG"
    )
    # All 5 REVERSAL_LOG values must appear as action= literals.
    for value in _REVERSAL_LOG_VALUES:
        assert value in matches, (
            f"reversal_service.py: missing action={value!r} "
            f"for action_class=ActionClass.REVERSAL_LOG"
        )


# ─────────────────────────────────────────────────────────────
# 2. MONTHLY_CLOSING — 4 values (Story 11.2 wire)
# ─────────────────────────────────────────────────────────────


_MONTHLY_CLOSING_VALUES = (
    "closing_sequence_initiated",
    "closing_sequence_step_completed",
    "closing_sequence_blocked",
    "closing_sequence_confirmed",
)


@pytest.mark.engine
def test_monthly_closing_registry_present() -> None:
    """A18 3-way (4/17): ActionClass.MONTHLY_CLOSING is in _ActionRegistry."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    assert ActionClass.MONTHLY_CLOSING in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.MONTHLY_CLOSING]
    assert log_type == "audit_logs"
    assert accepted == frozenset(_MONTHLY_CLOSING_VALUES)


@pytest.mark.engine
@pytest.mark.parametrize("action_value", list(_MONTHLY_CLOSING_VALUES))
def test_monthly_closing_validate_succeeds(action_value: str) -> None:
    """A18 3-way (5/17): each MONTHLY_CLOSING literal validates."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    result = _ActionRegistry.validate(
        action_class=ActionClass.MONTHLY_CLOSING, action=action_value
    )
    assert result == "audit_logs"


@pytest.mark.engine
def test_monthly_closing_call_sites_use_registry() -> None:
    """A18 3-way (6/17): close_sequence_service.py uses MONTHLY_CLOSING values.

    Two wire patterns:
    (a) `_emit_sequence_audit(action="closing_sequence_<value>", ...)` —
        helper method that calls `emit_audit_typed(action_class=
        ActionClass.MONTHLY_CLOSING, action=action, ...)` internally.
        Used for initiated / step_completed / confirmed.
    (b) `emit_audit_typed(..., action="closing_sequence_blocked", ...)` —
        direct typed emit. Used for the BLOCKED failure path.

    Both routes invoke the registry transitively. This test verifies
    all 4 values are referenced in the service file.
    """
    close_sequence_service = (
        ROOT
        / "apps"
        / "api"
        / "modules"
        / "m11_close"
        / "services"
        / "close_sequence_service.py"
    )
    if not close_sequence_service.exists():
        pytest.skip("close_sequence_service.py not found")

    src = _read(close_sequence_service)
    # Pattern (a): helper-method invocations.
    helper_matches = re.findall(
        r'_emit_sequence_audit\(\s*action="(closing_sequence_\w+)"',
        src,
    )
    # Pattern (b): direct emit_audit_typed invocations.
    direct_matches = _find_action_class_call_sites(src, "MONTHLY_CLOSING")
    all_matches = set(helper_matches) | set(direct_matches)

    # All 4 MONTHLY_CLOSING values must appear via EITHER pattern.
    for value in _MONTHLY_CLOSING_VALUES:
        assert value in all_matches, (
            f"close_sequence_service.py: missing action={value!r} "
            f"(checked _emit_sequence_audit + direct emit_audit_typed)"
        )


# ─────────────────────────────────────────────────────────────
# 3. SNAPSHOT_PERSISTENCE — 4 values (Story 11.3 wire)
# ─────────────────────────────────────────────────────────────


_SNAPSHOT_PERSISTENCE_VALUES = (
    "snapshot_persistence_committed",
    "snapshot_persistence_reversed",
    "snapshot_persistence_blocked",
    "snapshot_persistence_reopened",
)


@pytest.mark.engine
def test_snapshot_persistence_registry_present() -> None:
    """A18 3-way (7/17): ActionClass.SNAPSHOT_PERSISTENCE is in _ActionRegistry."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    assert ActionClass.SNAPSHOT_PERSISTENCE in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.SNAPSHOT_PERSISTENCE]
    assert log_type == "audit_logs"
    assert accepted == frozenset(_SNAPSHOT_PERSISTENCE_VALUES)


@pytest.mark.engine
@pytest.mark.parametrize("action_value", list(_SNAPSHOT_PERSISTENCE_VALUES))
def test_snapshot_persistence_validate_succeeds(action_value: str) -> None:
    """A18 3-way (8/17): each SNAPSHOT_PERSISTENCE literal validates."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    result = _ActionRegistry.validate(
        action_class=ActionClass.SNAPSHOT_PERSISTENCE, action=action_value
    )
    assert result == "audit_logs"


@pytest.mark.engine
def test_snapshot_persistence_call_sites_use_registry() -> None:
    """A18 3-way (9/17): both snapshot_persistence_service.py + reversal_execute_service.py use action_class=ActionClass.SNAPSHOT_PERSISTENCE.

    Scans BOTH files. snapshot_persistence_committed + reversed must
    have ≥1 call site each. The `blocked` + `reopened` values may be
    emitted at handler-level (not yet wired in service layer) — they
    are still verified by `test_snapshot_persistence_validate_succeeds`
    parametrized cases above.
    """
    services_dir = ROOT / "apps" / "api" / "modules" / "m11_close" / "services"
    snapshot_persistence_service = services_dir / "snapshot_persistence_service.py"
    reversal_execute_service = services_dir / "reversal_execute_service.py"
    if not (snapshot_persistence_service.exists() and reversal_execute_service.exists()):
        pytest.skip("One or both SNAPSHOT_PERSISTENCE service files not found")

    # Union of matches across both files.
    all_matches: list[str] = []
    for service_file in (snapshot_persistence_service, reversal_execute_service):
        all_matches.extend(
            _find_action_class_call_sites(_read(service_file), "SNAPSHOT_PERSISTENCE")
        )

    # At minimum, snapshot_persistence_committed + reversed must each
    # have ≥1 call site.
    assert "snapshot_persistence_committed" in all_matches, (
        "SNAPSHOT_PERSISTENCE: missing 'snapshot_persistence_committed' call site"
    )
    assert "snapshot_persistence_reversed" in all_matches, (
        "SNAPSHOT_PERSISTENCE: missing 'snapshot_persistence_reversed' call site"
    )


# ─────────────────────────────────────────────────────────────
# 4. REOPEN_OPERATOR — 2 values (Story 11.3 wire)
# ─────────────────────────────────────────────────────────────


_REOPEN_OPERATOR_VALUES = (
    "reopen_authorized",
    "reopen_completed",
)


@pytest.mark.engine
def test_reopen_operator_registry_present() -> None:
    """A18 3-way (10/17): ActionClass.REOPEN_OPERATOR is in _ActionRegistry."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    assert ActionClass.REOPEN_OPERATOR in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.REOPEN_OPERATOR]
    assert log_type == "audit_logs"
    assert accepted == frozenset(_REOPEN_OPERATOR_VALUES)


@pytest.mark.engine
@pytest.mark.parametrize("action_value", list(_REOPEN_OPERATOR_VALUES))
def test_reopen_operator_validate_succeeds(action_value: str) -> None:
    """A18 3-way (11/17): each REOPEN_OPERATOR literal validates."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    result = _ActionRegistry.validate(
        action_class=ActionClass.REOPEN_OPERATOR, action=action_value
    )
    assert result == "audit_logs"


@pytest.mark.engine
def test_reopen_operator_call_sites_use_registry() -> None:
    """A18 3-way (12/17): reopen_service.py uses action_class=ActionClass.REOPEN_OPERATOR."""
    reopen_service = (
        ROOT
        / "apps"
        / "api"
        / "modules"
        / "m11_close"
        / "services"
        / "reopen_service.py"
    )
    if not reopen_service.exists():
        pytest.skip("reopen_service.py not found")

    matches = _find_action_class_call_sites(_read(reopen_service), "REOPEN_OPERATOR")
    # reopen_completed MUST be present (post-UPDATE emit per A5 forward-lock).
    assert "reopen_completed" in matches, (
        "reopen_service.py: missing action='reopen_completed' "
        "for action_class=ActionClass.REOPEN_OPERATOR"
    )


# ─────────────────────────────────────────────────────────────
# 5. MONTHLY_INPUT_PERIOD extension — opening_unlocked (11-1)
# ─────────────────────────────────────────────────────────────


@pytest.mark.engine
def test_monthly_input_period_opening_unlocked_registry_present() -> None:
    """A18 3-way (13/17): MONTHLY_INPUT_PERIOD.opening_unlocked (11-1 sweep miss).

    Story 11.1 added `monthly_input_period_opening_unlocked` to the
    registry but the 11-1 sweep drift detector missed this case. The
    registry slot MUST contain this value (5 values total: mode_changed +
    opening_carried + opening_locked + opening_unlocked).
    """
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    assert ActionClass.MONTHLY_INPUT_PERIOD in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.MONTHLY_INPUT_PERIOD]
    assert log_type == "audit_logs"
    assert "monthly_input_period_opening_unlocked" in accepted, (
        "MONTHLY_INPUT_PERIOD registry must include 'monthly_input_period_opening_unlocked'"
    )


@pytest.mark.engine
def test_monthly_input_period_opening_unlocked_validates() -> None:
    """A18 3-way (14/17): validate succeeds for opening_unlocked."""
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    result = _ActionRegistry.validate(
        action_class=ActionClass.MONTHLY_INPUT_PERIOD,
        action="monthly_input_period_opening_unlocked",
    )
    assert result == "audit_logs"


@pytest.mark.engine
def test_monthly_input_period_opening_unlocked_call_site_uses_registry() -> None:
    """A18 3-way (15/17): reversal_service.py uses action=opening_unlocked for MONTHLY_INPUT_PERIOD."""
    reversal_service = (
        ROOT
        / "apps"
        / "api"
        / "modules"
        / "m11_close"
        / "services"
        / "reversal_service.py"
    )
    if not reversal_service.exists():
        pytest.skip("reversal_service.py not found")

    matches = _find_action_class_call_sites(
        _read(reversal_service), "MONTHLY_INPUT_PERIOD"
    )
    assert "monthly_input_period_opening_unlocked" in matches, (
        "reversal_service.py: missing action='monthly_input_period_opening_unlocked' "
        "for action_class=ActionClass.MONTHLY_INPUT_PERIOD"
    )


# ─────────────────────────────────────────────────────────────
# 6. Service-layer scan EXTENSION (3 NEW service files)
# ─────────────────────────────────────────────────────────────


@pytest.mark.engine
def test_service_layer_writers_use_registry_validate_extension() -> None:
    """A18 3-way (16/17): 3 NEW m11_close service files all use action_class=ActionClass.X.

    EXTENSION of existing
    `tests/integration/test_audit_action_consistency.py
    ::test_service_layer_writers_use_registry_validate` — the existing
    test only scans `calc_orchestrator.py`. This case ALSO scans the
    3 NEW m11_close service files (introduced by 11-1 / 11-2 / 11-3):

    - reopen_service.py (11-3)
    - close_sequence_service.py (11-2)
    - snapshot_persistence_service.py (11-3)

    Each file MUST have ≥1 `action_class=ActionClass.X` pattern (which
    catches BOTH `emit_audit_typed(...)` AND `_ActionRegistry.validate(...)`).

    Reversal-related services (reversal_service.py + reversal_execute_service.py)
    are not enforced here — they're covered by per-ActionClass call
    site tests above (REVERSAL_LOG).
    """
    services_dir = ROOT / "apps" / "api" / "modules" / "m11_close" / "services"
    target_files = [
        "reopen_service.py",
        "close_sequence_service.py",
        "snapshot_persistence_service.py",
    ]

    violations: list[str] = []
    for filename in target_files:
        service_file = services_dir / filename
        if not service_file.exists():
            violations.append(f"{filename}: file not found")
            continue
        src = _normalize_ws(_read(service_file))
        if "action_class=ActionClass." not in src:
            violations.append(
                f"{filename}: missing action_class=ActionClass.X pattern. "
                "A5 forward-lock requires fail-fast validation (via "
                "_ActionRegistry.validate OR emit_audit_typed) before INSERT."
            )

    assert not violations, (
        "A18 3-way EXTENSION: service-layer writers must use action_class=ActionClass.X.\n"
        + "\n".join(violations)
    )


# ─────────────────────────────────────────────────────────────
# 7. Cross-cutting: registry total ActionClass parity
# ─────────────────────────────────────────────────────────────


@pytest.mark.engine
def test_reversal_log_does_not_route_to_audit_logs() -> None:
    """A18 3-way (17/17): REVERSAL_LOG routes to reversal_log (NOT audit_logs).

    Sanity check: REVERSAL_LOG is the ONLY ActionClass among the 4 that
    routes to a non-`audit_logs` destination (`reversal_log`). This
    pins the routing invariant to prevent accidental regression.
    """
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    # REVERSAL_LOG → reversal_log.
    log_type, _ = _ActionRegistry._REGISTRY[ActionClass.REVERSAL_LOG]
    assert log_type == "reversal_log", (
        f"REVERSAL_LOG must route to 'reversal_log', got {log_type!r}"
    )

    # The other 3 ActionClasses → audit_logs.
    for ac in (
        ActionClass.MONTHLY_CLOSING,
        ActionClass.SNAPSHOT_PERSISTENCE,
        ActionClass.REOPEN_OPERATOR,
    ):
        lt, _ = _ActionRegistry._REGISTRY[ac]
        assert lt == "audit_logs", (
            f"{ac.name} must route to 'audit_logs', got {lt!r}"
        )


__all__ = [
    "test_reversal_log_registry_present",
    "test_reversal_log_call_sites_use_registry",
    "test_monthly_closing_registry_present",
    "test_monthly_closing_call_sites_use_registry",
    "test_snapshot_persistence_registry_present",
    "test_snapshot_persistence_call_sites_use_registry",
    "test_reopen_operator_registry_present",
    "test_reopen_operator_call_sites_use_registry",
    "test_monthly_input_period_opening_unlocked_registry_present",
    "test_monthly_input_period_opening_unlocked_call_site_uses_registry",
    "test_service_layer_writers_use_registry_validate_extension",
    "test_reversal_log_does_not_route_to_audit_logs",
]
