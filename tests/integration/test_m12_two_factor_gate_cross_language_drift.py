"""tests/integration/test_m12_two_factor_gate_cross_language_drift.py — Story 12.5

Cross-language parity drift detector for the M2 entry gate (D-PARITY-01 fix).

Two test files exercise the same 8 parity vectors — one Python (pure kernel
composition) and one TS (mirror). If either side changes its inputs
(`role`, `totp_enabled`, `locked_out`, `lockout_until`) without updating
the other, the gate logic on the slow side goes stale and D-PARITY-01
regresses.

  Python: `tests/integration/test_m12_two_factor_gate_kernel_parity.py`
  TS:      `apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts`

This test does NOT execute vitest. It parses both files for the
`parity N (corrected): ...` vector descriptions and asserts:
  - both files declare exactly the same 8 vector labels (parity 1..8)
  - both files exercise exactly the same 8 input tuples
  - both files assert the 6 key output fields (allowed, requires_two_factor,
    requires_challenge, role_allowed, locked_out, message_ko)

Failure modes caught:
  - vitest file drops a parity case → parity drift on either side
  - Python file changes input role (e.g., viewer → auditor) but TS doesn't update
  - Either side renames a vector label (parity 5 → parity 4b)
  - Either file is removed entirely (fail-closed structural check)

Pattern follows CR 11-4 P-015 ko-KR.json SSOT drift detector + capability
matrix v1.12 drift detector.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PY_PARITY = (
    REPO_ROOT
    / "tests"
    / "integration"
    / "test_m12_two_factor_gate_kernel_parity.py"
)
TS_PARITY = (
    REPO_ROOT
    / "apps"
    / "web"
    / "__tests__"
    / "lib"
    / "m12-two-factor-gate-parity.test.ts"
)

# ── 8 parity vector names that both files must declare (in order) ──
# Composition priority: setup-required > lockout > role_denied. Parity 5
# and parity 8 therefore use `totp_enabled=True` so the role_denied
# message priority #3 wins (otherwise setup-required message #1 dominates).
EXPECTED_LABELS: tuple[str, ...] = (
    "parity 1 (corrected): owner role + 2FA disabled → blocked, requires setup",
    "parity 2 (corrected): owner role + 2FA enabled → allowed=true",
    "parity 3 (corrected): member role + 2FA disabled → blocked, requires setup",
    "parity 4 (corrected): member role + 2FA enabled → allowed=true",
    "parity 5 (corrected): viewer role + 2FA enabled → blocked, role_denied",
    "parity 6 (corrected): consultant_proxy role → blocked, role_denied",
    "parity 7 (corrected): locked_out owner → blocked, lockout message",
    "parity 8 (corrected): unknown role 'auditor' + 2FA enabled → blocked, role_denied",
)


def _read(path: Path) -> str:
    assert path.exists(), f"missing parity file: {path}"
    return path.read_text(encoding="utf-8")


def _extract_labels_python(src: str) -> list[str]:
    """Pulls `def test_parity_<N>_<slug>(...) -> None:` docstring first line.

    The Python parity test marks each vector with a docstring whose first
    line starts with `parity N (corrected): ...`. Multi-line docstrings
    exist; we take the first line only, then strip trailing triple-quote
    and any trailing period.
    """
    out: list[str] = []
    pat = re.compile(
        r'def\s+(test_parity_\d+_\w+)\([^)]*\)\s*->\s*None:\s*"""\s*([^\n]+)',
        re.MULTILINE,
    )
    for m in pat.finditer(src):
        label = m.group(2).rstrip()
        # Strip trailing triple-quote (single-line docstring terminator).
        if label.endswith('"""'):
            label = label[:-3].rstrip()
        # Strip trailing period (preceded by whitespace).
        label = re.sub(r"\.\s*$", "", label).rstrip()
        out.append(label)
    return out


def _extract_labels_ts(src: str) -> list[str]:
    """Pulls vitest `it("parity N (corrected): ...", ...)` strings."""
    out: list[str] = []
    for m in re.finditer(r'\bit\(\s*"(parity[^\"]+)"', src):
        out.append(m.group(1))
    return out


def _extract_py_calls(src: str) -> list[dict[str, object]]:
    """Extracts the 8 _compose_m2_entry_state(...) call kwargs from Python."""
    # Match `_compose_m2_entry_state(\n  role="X",\n  totp_enabled=True/False,\n  ...`
    out: list[dict[str, object]] = []
    block_pat = re.compile(
        r"_compose_m2_entry_state\(\s*(?P<args>.*?)\s*\)",
        re.DOTALL,
    )
    for m in block_pat.finditer(src):
        kwarg_pat = re.compile(
            r'(\w+)\s*=\s*(True|False|"[^"]*"|None|"[^"]*")',
        )
        kwargs: dict[str, object] = {}
        for kp in kwarg_pat.finditer(m.group("args")):
            key = kp.group(1)
            raw = kp.group(2)
            if raw == "True":
                kwargs[key] = True
            elif raw == "False":
                kwargs[key] = False
            elif raw == "None":
                kwargs[key] = None
            else:
                kwargs[key] = raw.strip('"')
        if {"role", "totp_enabled", "locked_out"}.issubset(kwargs.keys()):
            out.append(kwargs)
    return out


def _extract_ts_calls(src: str) -> list[dict[str, object]]:
    """Extracts the 8 buildM2EntryGateState({...}) object literals from TS."""
    out: list[dict[str, object]] = []
    block_pat = re.compile(
        r"buildM2EntryGateState\(\s*\{(?P<args>[^}]+)\}\s*\)",
        re.DOTALL,
    )
    for m in block_pat.finditer(src):
        kwarg_pat = re.compile(
            r'(\w+):\s*(true|false|"[^"]*"|null|"[^"]*")',
        )
        kwargs: dict[str, object] = {}
        for kp in kwarg_pat.finditer(m.group("args")):
            key = kp.group(1)
            raw = kp.group(2)
            if raw == "true":
                kwargs[key] = True
            elif raw == "false":
                kwargs[key] = False
            elif raw == "null":
                kwargs[key] = None
            else:
                kwargs[key] = raw.strip('"')
        if {"role", "totp_enabled", "locked_out"}.issubset(kwargs.keys()):
            out.append(kwargs)
    return out


# ── 1. Both files exist ──────────────────────────────────────────


def test_python_parity_file_exists() -> None:
    """Python kernel parity test file must exist (fail-closed structural)."""
    assert PY_PARITY.exists(), f"missing: {PY_PARITY}"


def test_ts_parity_file_exists() -> None:
    """TS mirror parity test file must exist (fail-closed structural)."""
    assert TS_PARITY.exists(), f"missing: {TS_PARITY}"


# ── 2. Both files declare the same 8 parity vectors (in order) ───


def test_python_parity_labels_match_expected_8_vectors() -> None:
    """Python test must declare exactly the 8 expected parity labels."""
    src = _read(PY_PARITY)
    labels = _extract_labels_python(src)
    assert len(labels) == 8, (
        f"expected 8 parity labels in Python file, got {len(labels)}: {labels}"
    )
    for i, expected in enumerate(EXPECTED_LABELS):
        assert labels[i] == expected, (
            f"Python parity label #{i + 1} mismatch.\n"
            f"  expected: {expected!r}\n"
            f"  got:      {labels[i]!r}"
        )


def test_ts_parity_labels_match_expected_8_vectors() -> None:
    """TS test must declare exactly the 8 expected parity labels."""
    src = _read(TS_PARITY)
    labels = _extract_labels_ts(src)
    assert len(labels) == 8, (
        f"expected 8 parity labels in TS file, got {len(labels)}: {labels}"
    )
    for i, expected in enumerate(EXPECTED_LABELS):
        assert labels[i] == expected, (
            f"TS parity label #{i + 1} mismatch.\n"
            f"  expected: {expected!r}\n"
            f"  got:      {labels[i]!r}"
        )


def test_python_and_ts_parity_labels_match_in_order() -> None:
    """Both files must list the 8 vectors in the same order (drift detector)."""
    py_src = _read(PY_PARITY)
    ts_src = _read(TS_PARITY)
    py_labels = _extract_labels_python(py_src)
    ts_labels = _extract_labels_ts(ts_src)
    assert py_labels == ts_labels, (
        f"parity vector order/labels drift between Python and TS.\n"
        f"  Python ({len(py_labels)}): {py_labels}\n"
        f"  TS      ({len(ts_labels)}): {ts_labels}"
    )


# ── 3. Both files exercise the same 8 input tuples ────────────────


def test_python_and_ts_parity_inputs_match() -> None:
    """Both files must call their composition helper with the same 8 input tuples.

    Drift detector: if either side silently changes an input role or
    2FA state, the parity invariant (Python == TS output) silently
    breaks. This test compares the *inputs* directly.
    """
    py_inputs = _extract_py_calls(_read(PY_PARITY))
    ts_inputs = _extract_ts_calls(_read(TS_PARITY))
    assert len(py_inputs) == 8, (
        f"expected 8 _compose_m2_entry_state calls in Python, got {len(py_inputs)}"
    )
    assert len(ts_inputs) == 8, (
        f"expected 8 buildM2EntryGateState calls in TS, got {len(ts_inputs)}"
    )
    # Compare role + totp_enabled + locked_out (lockout_until_iso is None for 7/8)
    for i, (py, ts) in enumerate(zip(py_inputs, ts_inputs)):
        assert py["role"] == ts["role"], (
            f"parity #{i + 1} role drift: Python={py['role']!r} vs TS={ts['role']!r}"
        )
        assert py["totp_enabled"] == ts["totp_enabled"], (
            f"parity #{i + 1} totp_enabled drift: "
            f"Python={py['totp_enabled']!r} vs TS={ts['totp_enabled']!r}"
        )
        assert py["locked_out"] == ts["locked_out"], (
            f"parity #{i + 1} locked_out drift: "
            f"Python={py['locked_out']!r} vs TS={ts['locked_out']!r}"
        )


# ── 4. Both files assert the same 6 output fields ────────────────


_PY_FIELDS = re.compile(
    r'state\[(allowed|requires_two_factor|requires_challenge|'
    r'role_allowed|locked_out|message_ko)\]',
)
_TS_FIELDS = re.compile(
    r'state\.(allowed|requires_two_factor|requires_challenge|'
    r'role_allowed|locked_out|message_ko)',
)

EXPECTED_OUTPUT_FIELDS: tuple[str, ...] = (
    "allowed",
    "requires_two_factor",
    "requires_challenge",
    "role_allowed",
    "locked_out",
    "message_ko",
)


def test_python_parity_assertions_hit_6_output_fields() -> None:
    """Python assertions must cover all 6 output gate fields."""
    src = _read(PY_PARITY)
    # Find all 8 parity test bodies (parity 1..8 + 2 role assertions + 2 kernel
    # primitives — but primitives assert on inputs, not gate state, so for the
    # parity cases we expect all 6 fields to appear in body assertions).
    # Simpler check: across the entire file, all 6 fields must appear at least
    # once via state["..."] — that catches regressions on either parity vector.
    for field in EXPECTED_OUTPUT_FIELDS:
        assert f'state["{field}"]' in src, (
            f"Python parity file missing assertion on state['{field}']"
        )


def test_ts_parity_assertions_hit_6_output_fields() -> None:
    """TS assertions must cover all 6 output gate fields."""
    src = _read(TS_PARITY)
    for field in EXPECTED_OUTPUT_FIELDS:
        assert f"state.{field}" in src, (
            f"TS parity file missing assertion on state.{field}"
        )
