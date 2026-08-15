"""tests/integration/test_m12_account_deletion_cross_language_drift.py — Story 12.3

Cross-language parity drift detector for the M12 account deletion
TS mirror (`apps/web/lib/m12-account-deletion.ts`).

Mirrors the Python pure kernel `packages/services/m12_account/account_deletion.py`.
If either side changes its constants (RETENTION_DAYS, DELETION_ENVELOPE_SCHEMA_VERSION,
DELETION_CHALLENGE_TOKEN_TTL_SECONDS, DELETION_CONSENT_TEMPLATE_KO, FSM values) or
output fields (DeletionStatusResponse, DeletionEnvelopeResponse) without updating the
other, the parity on the slow side goes stale.

This test parses both files and asserts:
  - both files declare the same 5 numeric/enum constants
  - both files declare the same 3-value TenantDeletionStatus enum
  - both files declare a `can_transition_status` / `canTransitionStatus` function
  - both files declare the same 8 audit action values

Pattern follows `tests/integration/test_m12_two_factor_gate_cross_language_drift.py`
(Story 12.5 D-PARITY-01 fix).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PY_KERNEL = (
    REPO_ROOT / "packages" / "services" / "m12_account" / "account_deletion.py"
)
PY_SERVICE = (
    REPO_ROOT
    / "apps"
    / "api"
    / "modules"
    / "m12_account"
    / "services"
    / "account_deletion_service.py"
)
TS_MIRROR = REPO_ROOT / "apps" / "web" / "lib" / "m12-account-deletion.ts"
PY_AUDIT_ACTION = REPO_ROOT / "apps" / "api" / "core" / "audit_action.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing parity file: {path}"
    return path.read_text(encoding="utf-8")


# ── 1. Numeric/enum constant parity (Python ↔ TS) ─────────────
def test_retention_days_constant_matches() -> None:
    """RETENTION_DAYS must be 30 in both Python and TS (NFR4 2절).

    Python uses `RETENTION_DAYS: Final[int] = 30` (type annotation form).
    TS uses `RETENTION_DAYS = 30 as const` (TS literal form).
    """
    py = _read(PY_KERNEL)
    ts = _read(TS_MIRROR)
    # Python: `RETENTION_DAYS: Final[int] = 30` — accept optional type annotation
    assert re.search(
        r"^RETENTION_DAYS\s*:?\s*[A-Za-z\[\], _]*=\s*30\b", py, re.MULTILINE
    ), "Python RETENTION_DAYS = 30 not found"
    # TS: `export const RETENTION_DAYS = 30 as const`
    assert re.search(
        r"^export\s+const\s+RETENTION_DAYS\s*=\s*30\b", ts, re.MULTILINE
    ), "TS RETENTION_DAYS = 30 not found"


def test_envelope_schema_version_matches() -> None:
    """DELETION_ENVELOPE_SCHEMA_VERSION must be "1.0" in both."""
    py = _read(PY_KERNEL)
    ts = _read(TS_MIRROR)
    # Python: `DELETION_ENVELOPE_SCHEMA_VERSION: Final[str] = "1.0"`
    assert re.search(
        r'^DELETION_ENVELOPE_SCHEMA_VERSION\s*:?\s*[A-Za-z\[\], _]*=\s*[\'"]1\.0[\'"]',
        py,
        re.MULTILINE,
    ), "Python DELETION_ENVELOPE_SCHEMA_VERSION = '1.0' not found"
    # TS: `export const DELETION_ENVELOPE_SCHEMA_VERSION = "1.0" as const`
    assert re.search(
        r"DELETION_ENVELOPE_SCHEMA_VERSION\s*=\s*[\"']1\.0[\"']\s+as\s+const", ts
    ), "TS DELETION_ENVELOPE_SCHEMA_VERSION = '1.0' not found"


def test_challenge_token_ttl_matches() -> None:
    """DELETION_CHALLENGE_TOKEN_TTL_SECONDS must be 300 in both (5 min).

    Lives in service layer (not pure kernel) because it depends on JWT/clock.
    """
    py = _read(PY_SERVICE)
    ts = _read(TS_MIRROR)
    # Python service: `DELETION_CHALLENGE_TOKEN_TTL_SECONDS: int = 300`
    assert re.search(
        r"^DELETION_CHALLENGE_TOKEN_TTL_SECONDS\s*:?\s*[A-Za-z\[\], _]*=\s*300\b",
        py,
        re.MULTILINE,
    ), "Python DELETION_CHALLENGE_TOKEN_TTL_SECONDS = 300 not found"
    # TS: `export const DELETION_CHALLENGE_TOKEN_TTL_SECONDS = 300 as const`
    assert re.search(
        r"DELETION_CHALLENGE_TOKEN_TTL_SECONDS\s*=\s*300\b", ts
    ), "TS DELETION_CHALLENGE_TOKEN_TTL_SECONDS = 300 not found"


def test_challenge_token_purpose_matches() -> None:
    """DELETION_CHALLENGE_TOKEN_PURPOSE must be 'account_deletion' in both.

    Lives in service layer (not pure kernel).
    """
    py = _read(PY_SERVICE)
    ts = _read(TS_MIRROR)
    assert re.search(
        r"^DELETION_CHALLENGE_TOKEN_PURPOSE\s*:?\s*[A-Za-z\[\], _]*=\s*[\"']account_deletion[\"']",
        py,
        re.MULTILINE,
    ), "Python DELETION_CHALLENGE_TOKEN_PURPOSE = 'account_deletion' not found"
    assert re.search(
        r"DELETION_CHALLENGE_TOKEN_PURPOSE\s*=\s*[\"']account_deletion[\"']\s+as\s+const",
        ts,
    ), "TS DELETION_CHALLENGE_TOKEN_PURPOSE = 'account_deletion' not found"


def test_consent_template_ko_matches() -> None:
    """DELETION_CONSENT_TEMPLATE_KO must be identical verbatim in both."""
    py = _read(PY_KERNEL)
    ts = _read(TS_MIRROR)
    assert "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다" in py, (
        "Python DELETION_CONSENT_TEMPLATE_KO literal not found"
    )
    assert (
        "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다" in ts
    ), "TS DELETION_CONSENT_TEMPLATE_KO literal not found"


# ── 2. TenantDeletionStatus FSM parity (3 values) ─────────────
def test_tenant_deletion_status_enum_values_match() -> None:
    """TenantDeletionStatus must declare exactly 3 values: active, pending_deletion, deleted."""
    py = _read(PY_KERNEL)
    ts = _read(TS_MIRROR)
    for status_value in ("active", "pending_deletion", "deleted"):
        assert f'"{status_value}"' in py or f"'{status_value}'" in py, (
            f"Python TenantDeletionStatus missing '{status_value}'"
        )
        assert f'"{status_value}"' in ts, (
            f"TS TenantDeletionStatus missing '{status_value}'"
        )


def test_fsm_function_declared_in_both_files() -> None:
    """Both files MUST declare a `can_transition_status` / `canTransitionStatus` function.

    Semantic correctness (3 allowed transitions) is verified by the
    `test_m12_account_deletion_kernel_parity.py::test_fsm_full_grid_exhaustive`
    test which runs `can_transition_status` on the full 3×3 grid.
    """
    py = _read(PY_KERNEL)
    ts = _read(TS_MIRROR)
    assert re.search(r"^def\s+can_transition_status\s*\(", py, re.MULTILINE), (
        "Python can_transition_status() not declared"
    )
    assert re.search(
        r"function\s+canTransitionStatus\s*\(", ts
    ), "TS canTransitionStatus() not declared"


# ── 3. 8 audit action values parity (Python Literal ↔ TS const) ──
def test_audit_action_values_count_match() -> None:
    """AccountDeletionAction must declare exactly 8 values in BOTH sides."""
    py = _read(PY_AUDIT_ACTION)
    ts = _read(TS_MIRROR)
    # Python: AccountDeletionAction = Literal["...", ...]  (8 string literals)
    py_match = re.search(
        r"AccountDeletionAction\s*=\s*Literal\[\s*(.*?)\s*\]", py, re.DOTALL
    )
    assert py_match is not None, "Python AccountDeletionAction Literal not found"
    # Match strings — accept lowercase letters, underscores, and DIGITS
    # (e.g. `deletion_2fa_failed` has digit '2')
    py_values = re.findall(r"['\"]([a-z0-9_]+)['\"]", py_match.group(1))
    assert len(py_values) == 8, (
        f"Python AccountDeletionAction has {len(py_values)} values (expected 8): {py_values}"
    )
    # TS: const AccountDeletionAction = { DELETION_REQUESTED: "deletion_requested", ... }
    ts_match = re.search(
        r"export const AccountDeletionAction = \{(.*?)\} as const", ts, re.DOTALL
    )
    assert ts_match is not None, "TS AccountDeletionAction const not found"
    ts_values = re.findall(r':\s*"([a-z0-9_]+)"', ts_match.group(1))
    assert len(ts_values) == 8, (
        f"TS AccountDeletionAction has {len(ts_values)} values (expected 8): {ts_values}"
    )
    # Pairwise comparison — same set of literal values
    assert set(py_values) == set(ts_values), (
        f"AccountDeletionAction drift: Python-only={set(py_values) - set(ts_values)}, "
        f"TS-only={set(ts_values) - set(py_values)}"
    )


# ── 4. ActionClass registry ↔ TS mirror parity ────────────────
def test_action_class_registry_has_account_deletion() -> None:
    """ActionClass.ACCOUNT_DELETION must exist in audit_action.py registry."""
    py = _read(PY_AUDIT_ACTION)
    assert "ACCOUNT_DELETION" in py
    assert "ActionClass.ACCOUNT_DELETION" in py or "ACCOUNT_DELETION = " in py


def test_action_class_account_deletion_registry_count() -> None:
    """ActionClass.ACCOUNT_DELETION registry must have exactly 8 values."""
    py = _read(PY_AUDIT_ACTION)
    # Find the registry block for ACCOUNT_DELETION. The block spans
    # `ActionClass.ACCOUNT_DELETION: ( "audit_logs", frozenset( { ... } ), )`
    # We use a balanced-brace match: capture from `frozenset(\s*{` to the
    # matching closing `}` (not the first one).
    m = re.search(
        r"ActionClass\.ACCOUNT_DELETION:\s*\(\s*['\"]audit_logs['\"]\s*,\s*frozenset\(\s*\{",
        py,
    )
    assert m is not None, "ACCOUNT_DELETION registry block not found"
    start = m.end()
    # Walk the string to find the matching closing brace
    depth = 1
    pos = start
    while pos < len(py) and depth > 0:
        if py[pos] == "{":
            depth += 1
        elif py[pos] == "}":
            depth -= 1
        pos += 1
    registry_block = py[start : pos - 1]
    registry_values = re.findall(r"['\"]([a-z0-9_]+)['\"]", registry_block)
    assert len(registry_values) == 8, (
        f"ACCOUNT_DELETION registry has {len(registry_values)} values (expected 8): "
        f"{registry_values}"
    )
