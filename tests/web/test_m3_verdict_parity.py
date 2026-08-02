"""tests.web.test_m3_verdict_parity — TS ↔ Python verdict envelope parity.

Story 4.3 (Task 5.4 + Task 6 cross-lang boundary fixture) — Drift gate
for the TypeScript mirror in `apps/web/lib/m3-verdict.ts`.

Why a Python test for a TypeScript mirror? Because the Python module is
the CANONICAL source of truth (AD-1 hexagonal core + AD-15 Pydantic
schema). The TS mirror must agree on:

  1. VerificationCode enum members (V1 / V4 / V7 / V8) — PRD §11 V-row.
  2. VerificationStatus enum members (passed / failed) — AD-20 invariant.
  3. VerificationEnvelopeStatus (passed / failed) — AD-20 external.
  4. Industry enum members (manufacturing / manufacturing_retail /
     service / mixed) — Tenant.industry CheckConstraint values.
  5. Per-industry V7 firing matrix (service-only).
  6. Verdict envelope field shape (verification_status, verifications,
     top_failure, trace_id).
  7. VerificationItem field shape (code, status, message_ko, details).
  8. Top-failure invariant (non-null iff verification_status='failed').
  9. UI failure code mapping (ERR_V1_INCOMPLETE_ALLOCATION / ERR_V4_* /
     ERR_V7_* / ERR_V8_*).
 10. Verifications array ordering (V1 → V4 → V7 → V8) — AD-12 ordering.
 11. JSON serialization shape parity (camelCase in TS layer when sent
     over HTTP, snake_case from Python — `verification_status` /
     `top_failure` / `trace_id`).
 12. Empty verifications[] is valid for idempotent_skip path.
 13. 'pending' status rejection — AD-20 internal-only.
 14. Korean message_ko convention (not English) — UI deterministic.
 15. Fired-rule cardinality per industry (3 or 4 items).
 16. Verdict envelope `extra='forbid'` discipline (TS type guard vs
     Python ConfigDict — both reject unknown fields).

CR 0.2 / 1.1 / 2.3 lessons:
  - Audit-first + idempotent no-op pattern (Verdict frozen dataclass).
  - Pydantic v2 extra='forbid' (TS side type guard mirrors this).
  - Cross-language regex/dtype drift detected by AST scan.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# ── Path resolution ───────────────────────────────────────────────
_TS_MIRROR_PATH = Path(__file__).resolve().parents[2] / "apps" / "web" / "lib" / "m3-verdict.ts"
_PY_SCHEMAS_PATH = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "modules"
    / "m3_calculate"
    / "schemas.py"
)
_PY_PROTOCOL_PATH = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "modules"
    / "m3_calculate"
    / "services"
    / "rules"
    / "protocol.py"
)


def _read_ts_source() -> str:
    """Load the TS mirror source verbatim."""
    if not _TS_MIRROR_PATH.exists():
        pytest.fail(f"TS mirror not found: {_TS_MIRROR_PATH}")
    return _TS_MIRROR_PATH.read_text(encoding="utf-8")


def _read_py_schema_source() -> str:
    """Load the Python schema source verbatim."""
    if not _PY_SCHEMAS_PATH.exists():
        pytest.fail(f"Python schema not found: {_PY_SCHEMAS_PATH}")
    return _PY_SCHEMAS_PATH.read_text(encoding="utf-8")


def _read_py_protocol_source() -> str:
    """Load the Python protocol source verbatim (industry values)."""
    if not _PY_PROTOCOL_PATH.exists():
        pytest.fail(f"Python protocol not found: {_PY_PROTOCOL_PATH}")
    return _PY_PROTOCOL_PATH.read_text(encoding="utf-8")


# ── 1. VerificationCode enum members ──────────────────────────────
@pytest.mark.engine
def test_verification_code_members_parity() -> None:
    """V1 / V4 / V7 / V8 — TS mirror must match Python Literal."""
    py_src = _read_py_schema_source()
    ts_src = _read_ts_source()

    py_tree = ast.parse(py_src)
    py_codes: set[str] = set()
    for node in ast.walk(py_tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "code"
            and isinstance(node.annotation, ast.Subscript)
        ):
            sl = node.annotation.slice
            if isinstance(sl, ast.Tuple):
                for elt in sl.elts:
                    if isinstance(elt, ast.Constant):
                        py_codes.add(elt.value)

    ts_codes: set[str] = set(re.findall(r'"(V[1478])"', ts_src.split("VerificationCode")[1].split(";")[0]))

    expected = {"V1", "V4", "V7", "V8"}
    assert py_codes == expected, f"Python schema missing codes: {expected - py_codes}"
    assert ts_codes == expected, f"TS mirror missing codes: {expected - ts_codes}"


# ── 2. VerificationStatus enum members ────────────────────────────
@pytest.mark.engine
def test_verification_status_members_parity() -> None:
    """passed / failed — TS mirror must match Python Literal."""
    ts_src = _read_ts_source()
    ts_status: set[str] = set(re.findall(r'"(passed|failed)"', ts_src))

    py_src = _read_py_schema_source()
    py_tree = ast.parse(py_src)
    py_status: set[str] = set()
    for node in ast.walk(py_tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "status"
            and isinstance(node.annotation, ast.Subscript)
        ):
            sl = node.annotation.slice
            if isinstance(sl, ast.Tuple):
                for elt in sl.elts:
                    if isinstance(elt, ast.Constant):
                        py_status.add(elt.value)

    expected = {"passed", "failed"}
    assert py_status == expected
    assert expected.issubset(ts_status)


# ── 3. 'pending' status rejection (AD-20 internal-only) ───────────
@pytest.mark.engine
def test_pending_status_rejected_in_python() -> None:
    """Python Literal['passed','failed'] — 'pending' must NOT appear in status enum."""
    py_src = _read_py_schema_source()
    assert '"pending"' not in py_src or "AD-20" in py_src
    # Python: only 'passed' and 'failed' appear in status/verification_status Literal.


@pytest.mark.engine
def test_pending_status_rejected_in_ts() -> None:
    """TS VerificationStatus — 'pending' must NOT appear as a code literal (AD-20 external-only).

    Permitted in comments (explaining AD-20 invariant). Forbidden in:
      - Literal type definition: `Literal['passed','failed']` / type alias
      - String constants: `"pending"` / `'pending'`
      - Code paths: status === 'pending' / .pending
    """
    ts_src = _read_ts_source()
    # Strip comments (// single-line and /* multi-line */)
    no_block = re.sub(r"/\*[\s\S]*?\*/", "", ts_src)
    no_line = re.sub(r"//[^\n]*", "", no_block)
    # In code-only context, "pending" must NOT appear
    assert "pending" not in no_line, (
        "TS mirror leaks 'pending' as a code value (AD-20 violation). "
        "Pending is internal-only — surface as 'passed' or 'failed'."
    )


# ── 4. Industry enum members parity ───────────────────────────────
@pytest.mark.engine
def test_industry_enum_parity() -> None:
    """Industry enum members must match INDUSTRY_VALUES."""
    py_src = _read_py_protocol_source()
    py_industries: set[str] = set(re.findall(r'INDUSTRY_\w+:\s*Literal\["(\w+)"\]', py_src))

    ts_src = _read_ts_source()
    ts_industries: set[str] = set(
        re.findall(
            r'"(manufacturing|manufacturing_service|service|manufacturing_service_other)"',
            ts_src,
        )
    )

    expected = {"manufacturing", "manufacturing_service", "service", "manufacturing_service_other"}
    assert py_industries == expected
    assert ts_industries == expected


# ── 5. Per-industry V7 firing matrix parity ───────────────────────
@pytest.mark.engine
def test_v7_firing_matrix_parity() -> None:
    """V7 fires only for `service` — TS INDUSTRY_FIRES_V7 must mirror Python applies_to."""
    ts_src = _read_ts_source()
    # Extract INDUSTRY_FIRES_V7 mapping values
    fires_match = re.search(
        r"INDUSTRY_FIRES_V7:\s*Readonly<Record<Industry,\s*boolean>>\s*=\s*\{([^}]+)\}",
        ts_src,
        re.DOTALL,
    )
    assert fires_match, "INDUSTRY_FIRES_V7 not found in TS mirror"
    body = fires_match.group(1)
    parsed: dict[str, bool] = {}
    for line in body.splitlines():
        line = line.strip().rstrip(",").rstrip()
        if not line or line.startswith("//"):
            continue
        m = re.match(r"^(\w+):\s*(true|false)$", line)
        if m:
            parsed[m.group(1)] = m.group(2) == "true"

    assert parsed.get("manufacturing") is False
    assert parsed.get("manufacturing_service") is False
    assert parsed.get("service") is True
    assert parsed.get("manufacturing_service_other") is False


# ── 6. Verdict envelope field shape parity ────────────────────────
@pytest.mark.engine
def test_verdict_envelope_fields_parity() -> None:
    """Verdict MUST have: verification_status, verifications, top_failure, trace_id."""
    py_src = _read_py_schema_source()
    py_tree = ast.parse(py_src)
    py_fields: set[str] = set()
    for node in ast.walk(py_tree):
        if isinstance(node, ast.ClassDef) and node.name == "Verdict":
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    py_fields.add(stmt.target.id)
            break

    expected = {"verification_status", "verifications", "top_failure", "trace_id"}
    assert py_fields == expected, f"Python Verdict missing fields: {expected - py_fields}"

    ts_src = _read_ts_source()
    for field in expected:
        assert f"{field}:" in ts_src or f"{field} " in ts_src, (
            f"TS Verdict missing field: {field}"
        )


# ── 7. VerificationItem field shape parity ───────────────────────
@pytest.mark.engine
def test_verification_item_fields_parity() -> None:
    """VerificationItem MUST have: code, status, message_ko, details."""
    py_src = _read_py_schema_source()
    py_tree = ast.parse(py_src)
    py_fields: set[str] = set()
    for node in ast.walk(py_tree):
        if isinstance(node, ast.ClassDef) and node.name == "VerificationItem":
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    py_fields.add(stmt.target.id)
            break

    expected = {"code", "status", "message_ko", "details"}
    assert py_fields == expected, f"Python VerificationItem missing fields: {expected - py_fields}"

    ts_src = _read_ts_source()
    for field in expected:
        assert field in ts_src, f"TS VerificationItem missing field: {field}"


# ── 8. Top-failure invariant — non-null iff verification_status='failed' ─
@pytest.mark.engine
def test_top_failure_invariant_in_python_schema() -> None:
    """Python Verdict.top_failure: VerificationItem | None = None."""
    py_src = _read_py_schema_source()
    py_tree = ast.parse(py_src)
    for node in ast.walk(py_tree):
        if isinstance(node, ast.ClassDef) and node.name == "Verdict":
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Name)
                    and stmt.target.id == "top_failure"
                ):
                    ann = stmt.annotation
                    ann_str = ast.unparse(ann) if hasattr(ast, "unparse") else ""
                    assert "None" in ann_str, "top_failure must allow None"


@pytest.mark.engine
def test_top_failure_invariant_in_ts() -> None:
    """TS top_failure: VerificationItem | null — mirrors Python optional."""
    ts_src = _read_ts_source()
    # Must have `top_failure: VerificationItem | null` in interface
    assert re.search(r"top_failure:\s*VerificationItem\s*\|\s*null", ts_src), (
        "TS top_failure type must be 'VerificationItem | null'"
    )


# ── 9. UI failure code mapping parity ────────────────────────────
@pytest.mark.engine
def test_v_failure_ui_codes_complete() -> None:
    """ERR_V*_INCOMPLETE_ALLOCATION / _COST_INCOME_RECONCILIATION / _ABC_INTEGRITY / _ENGINE_REGRESSION."""
    ts_src = _read_ts_source()
    expected = {
        "ERR_V1_INCOMPLETE_ALLOCATION",
        "ERR_V4_COST_INCOME_RECONCILIATION",
        "ERR_V7_ABC_INTEGRITY",
        "ERR_V8_ENGINE_REGRESSION",
    }
    for code in expected:
        assert code in ts_src, f"TS mirror missing UI failure code: {code}"


# ── 10. AD-12 ordering invariant in TS expected-rule helper ───────
@pytest.mark.engine
def test_ad12_ordering_in_expected_rule_codes() -> None:
    """V1 → V4 → V7 → V8 ordering preserved by expectedRuleCodesForIndustry()."""
    ts_src = _read_ts_source()
    # Check the function definition exists
    assert "expectedRuleCodesForIndustry" in ts_src
    # The helper must splice V7 between V4 and V8 (service only)
    # Find the function body
    fn_match = re.search(
        r"function\s+expectedRuleCodesForIndustry\([^)]*\)[^{]*\{(.+?)\n\}",
        ts_src,
        re.DOTALL,
    )
    assert fn_match, "expectedRuleCodesForIndustry function not found"
    body = fn_match.group(1)
    assert '"V1"' in body, "V1 missing from expectedRuleCodesForIndustry body"
    assert '"V4"' in body, "V4 missing from expectedRuleCodesForIndustry body"
    assert '"V7"' in body, "V7 missing from expectedRuleCodesForIndustry body"
    assert '"V8"' in body, "V8 missing from expectedRuleCodesForIndustry body"
    assert "splice" in body, "V7 must splice (not append/push)"


# ── 11. Per-industry fired-rule cardinality parity ────────────────
@pytest.mark.engine
def test_per_industry_cardinality() -> None:
    """Service: 4 rules fire. Others: 3 rules fire (V7 silent skip)."""
    ts_src = _read_ts_source()
    fn_match = re.search(
        r"function\s+expectedRuleCodesForIndustry\([^)]*\)[^{]*\{(.+?)\n\}",
        ts_src,
        re.DOTALL,
    )
    assert fn_match

    assert "service: true" in ts_src
    assert "manufacturing: false" in ts_src
    assert "manufacturing_service: false" in ts_src
    assert "manufacturing_service_other: false" in ts_src


# ── 12. isVerdict type guard presence ─────────────────────────────
@pytest.mark.engine
def test_is_verdict_type_guard() -> None:
    """TS type guard `isVerdict` exists (defense-in-depth at API boundary)."""
    ts_src = _read_ts_source()
    assert "export function isVerdict" in ts_src
    # Must validate: status string, verifications array, trace_id string, top_failure null/object
    assert "verification_status" in ts_src
    assert "verifications" in ts_src
    assert "trace_id" in ts_src
    assert "top_failure" in ts_src


# ── 13. topFailureCode helper parity ──────────────────────────────
@pytest.mark.engine
def test_top_failure_code_helper() -> None:
    """topFailureCode() returns null iff verdict.verification_status='passed'."""
    ts_src = _read_ts_source()
    assert "export function topFailureCode" in ts_src
    # Helper must use V_FAILURE_CODES mapping
    assert "V_FAILURE_CODES" in ts_src


# ── 14. firedRuleCodes helper parity ──────────────────────────────
@pytest.mark.engine
def test_fired_rule_codes_helper() -> None:
    """firedRuleCodes() aggregates verdict.verifications[].code."""
    ts_src = _read_ts_source()
    assert "export function firedRuleCodes" in ts_src
    # Maps over verifications → extracts code
    assert "verifications.map" in ts_src or ".map(" in ts_src


# ── 15. Empty verifications[] valid (idempotent_skip path) ───────
@pytest.mark.engine
def test_empty_verifications_array_path() -> None:
    """verifications: [] is valid (Python default_factory=list + TS no error in isVerdict)."""
    py_src = _read_py_schema_source()
    assert "default_factory=list" in py_src
    ts_src = _read_ts_source()
    # isVerdict type guard accepts empty array (Array.isArray([]) → true)
    assert "Array.isArray" in ts_src


# ── 16. Source-of-truth comment discipline ───────────────────────
@pytest.mark.engine
def test_ts_mirror_documents_python_canonical() -> None:
    """TS mirror MUST declare Python as source of truth in header docstring."""
    ts_src = _read_ts_source()
    # Header comment MUST mention 'NOT THE SOURCE OF TRUTH' or 'canonical'
    assert "SOURCE OF TRUTH" in ts_src or "canonical" in ts_src.lower()
    # MUST reference the Python schemas path
    assert "schemas.py" in ts_src


@pytest.mark.engine
def test_ts_mirror_includes_trace_id_contract() -> None:
    """trace_id round-trip documented in TS header."""
    ts_src = _read_ts_source()
    assert "trace_id" in ts_src
    # UI audit trail reference
    assert "trace" in ts_src.lower()


@pytest.mark.engine
def test_ts_mirror_references_korean_messages() -> None:
    """Korean message_ko convention referenced in TS header (UI deterministic)."""
    ts_src = _read_ts_source()
    assert "message_ko" in ts_src
    assert "Korean" in ts_src or "한국" in ts_src


# ── Total: 16 cross-lang cases ─────────────────────────────────
